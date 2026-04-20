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
def index():
    destination = request.args.get("destination", "").strip()
    keyword = request.args.get("keyword", "").strip()

    conn = get_db_connection()

    query = "SELECT * FROM parking_zones WHERE 1=1"
    params = []

    if destination:
        query += " AND destination_tag = ?"
        params.append(destination)

    if keyword:
        query += " AND (zone_name LIKE ? OR location LIKE ?)"
        params.extend([f"%{keyword}%", f"%{keyword}%"])

    zones = conn.execute(query, params).fetchall()

    all_destinations = conn.execute(
        "SELECT DISTINCT destination_tag FROM parking_zones ORDER BY destination_tag"
    ).fetchall()

    summary = conn.execute("""
        SELECT 
            COUNT(*) AS total_areas,
            SUM(free_spots) AS total_free_spaces,
            SUM(CASE WHEN status = 'Limited' THEN 1 ELSE 0 END) AS limited_areas,
            SUM(CASE WHEN status = 'Full' THEN 1 ELSE 0 END) AS full_areas
        FROM parking_zones
    """).fetchone()

    conn.close()

    last_updated = datetime.now().strftime("%d %b %Y, %I:%M %p")

    return render_template(
        "index.html",
        zones=zones,
        destinations=all_destinations,
        selected_destination=destination,
        keyword=keyword,
        summary=summary,
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