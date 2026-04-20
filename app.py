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
    elif free_spots <= max(2, int(total_spots * 0.2)):
        return "Limited"
    return "Available"


AREA_CENTERS = {
    "Library": {"lat": 4.9693, "lng": 114.8979, "label": "Library Area"},
    "FOS": {"lat": 4.9712, "lng": 114.8930, "label": "Faculty of Science Area"},
    "FIT": {"lat": 4.9680, "lng": 114.8915, "label": "FIT Area"},
    "SDS": {"lat": 4.9673, "lng": 114.8940, "label": "School of Digital Science Area"},
    "UBDSBE": {"lat": 4.9662, "lng": 114.8964, "label": "UBDSBE Area"},
    "SAS": {"lat": 4.9701, "lng": 114.8950, "label": "Student Affairs Area"},
    "ADMIN": {"lat": 4.9708, "lng": 114.8968, "label": "Administration Area"},
}


@app.route("/")
def home():
    return render_template("home.html")


@app.route("/locations")
def locations():
    conn = get_db_connection()
    destinations = conn.execute("""
        SELECT DISTINCT destination_tag, zone_name, location
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
    spots = []
    selected_area = None

    if destination:
        zones = conn.execute("""
            SELECT * FROM parking_zones
            WHERE destination_tag = ?
            ORDER BY zone_name
        """, (destination,)).fetchall()

        spots = conn.execute("""
            SELECT * FROM parking_spots
            WHERE destination_tag = ?
            ORDER BY section_code, spot_code
        """, (destination,)).fetchall()

        selected_area = conn.execute("""
            SELECT destination_tag, zone_name, location
            FROM parking_zones
            WHERE destination_tag = ?
            LIMIT 1
        """, (destination,)).fetchone()

    conn.close()

    total_free = sum(zone["free_spots"] for zone in zones) if zones else 0
    total_capacity = sum(zone["total_spots"] for zone in zones) if zones else 0
    last_updated = datetime.now().strftime("%d %b %Y, %I:%M %p")
    best_zone = max(zones, key=lambda z: z["free_spots"]) if zones else None
    area_center = AREA_CENTERS.get(destination, {"lat": 4.9685, "lng": 114.8955, "label": "UBD Campus Area"})

    return render_template(
        "parking.html",
        zones=zones,
        spots=spots,
        selected_area=selected_area,
        destination=destination,
        total_free=total_free,
        total_capacity=total_capacity,
        last_updated=last_updated,
        best_zone=best_zone,
        area_center=area_center
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
    zone = conn.execute("SELECT * FROM parking_zones WHERE id = ?", (zone_id,)).fetchone()

    if zone:
        total_spots = zone["total_spots"]
        free_spots = max(0, min(free_spots, total_spots))
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
