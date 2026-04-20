import os
import sqlite3
from datetime import datetime
from flask import Flask, render_template, request, redirect, url_for

app = Flask(__name__)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "smartpark.db")


def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def calculate_status(free_spots, total_spots):
    if free_spots <= 0:
        return "Full"
    elif free_spots <= max(5, int(total_spots * 0.1)):
        return "Limited"
    return "Available"


@app.route("/")
def home():
    return render_template("home.html")


@app.route("/locations")
def locations():
    conn = get_db_connection()
    destinations = conn.execute("""
        SELECT DISTINCT destination_tag, location
        FROM parking_zones
        ORDER BY destination_tag
    """).fetchall()
    conn.close()
    return render_template("locations.html", destinations=destinations)


@app.route("/parking")
def parking():
    destination = request.args.get("destination", "").strip()

    conn = get_db_connection()

    zones = []
    selected_area = None

    if destination:
        zones = conn.execute("""
            SELECT * FROM parking_zones
            WHERE destination_tag = ?
            ORDER BY section_code
        """, (destination,)).fetchall()

        selected_area = conn.execute("""
            SELECT destination_tag, location
            FROM parking_zones
            WHERE destination_tag = ?
            LIMIT 1
        """, (destination,)).fetchone()

    conn.close()

    total_free = sum(zone["free_spots"] for zone in zones) if zones else 0
    total_capacity = sum(zone["total_spots"] for zone in zones) if zones else 0
    last_updated = datetime.now().strftime("%d %b %Y, %I:%M %p")

    return render_template(
        "parking.html",
        zones=zones,
        selected_area=selected_area,
        destination=destination,
        total_free=total_free,
        total_capacity=total_capacity,
        last_updated=last_updated
    )


@app.route("/admin")
def admin():
    conn = get_db_connection()
    zones = conn.execute("SELECT * FROM parking_zones ORDER BY zone_name").fetchall()
    conn.close()
    return render_template("admin.html", zones=zones)


@app.route("/update/<int:zone_id>", methods=["POST"])
def update_zone(zone_id):
    free_spots = int(request.form["free_spots"])

    conn = get_db_connection()
    zone = conn.execute(
        "SELECT * FROM parking_zones WHERE id = ?",
        (zone_id,)
    ).fetchone()

    if zone:
        total_spots = zone["total_spots"]

        if free_spots < 0:
            free_spots = 0
        if free_spots > total_spots:
            free_spots = total_spots

        status = calculate_status(free_spots, total_spots)

        conn.execute("""
            UPDATE parking_zones
            SET free_spots = ?, status = ?
            WHERE id = ?
        """, (free_spots, status, zone_id))
        conn.commit()

    conn.close()
    return redirect(url_for("admin"))


if __name__ == "__main__":
    app.run(debug=True)
