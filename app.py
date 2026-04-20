import os
import sqlite3
from datetime import datetime
from flask import Flask, render_template, request, redirect, url_for, jsonify
import xml.etree.ElementTree as ET

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
    "FIT": {"lat": 4.9680, "lng": 114.8915, "label": "FIT Area"},
    "FOS": {"lat": 4.9712, "lng": 114.8930, "label": "Faculty of Science Area"},
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

    zones = conn.execute("""
        SELECT * FROM parking_zones
        WHERE destination_tag = ?
    """, (destination,)).fetchall()

    spots = conn.execute("""
        SELECT * FROM parking_spots
        WHERE destination_tag = ?
    """, (destination,)).fetchall()

    conn.close()

    total_free = sum(z["free_spots"] for z in zones)
    total_capacity = sum(z["total_spots"] for z in zones)
    best_zone = max(zones, key=lambda z: z["free_spots"]) if zones else None
    last_updated = datetime.now().strftime("%H:%M:%S")

    area_center = AREA_CENTERS.get(
        destination,
        {"lat": 4.9685, "lng": 114.8955, "label": "UBD"}
    )

    return render_template(
        "parking.html",
        zones=zones,
        spots=spots,
        destination=destination,
        total_free=total_free,
        total_capacity=total_capacity,
        best_zone=best_zone,
        last_updated=last_updated,
        area_center=area_center
    )


@app.route("/api/parking/<destination>")
def parking_data(destination):
    conn = get_db_connection()

    zones = conn.execute("""
        SELECT * FROM parking_zones
        WHERE destination_tag = ?
    """, (destination,)).fetchall()

    spots = conn.execute("""
        SELECT * FROM parking_spots
        WHERE destination_tag = ?
    """, (destination,)).fetchall()

    conn.close()

    total_free = sum(z["free_spots"] for z in zones)
    total_capacity = sum(z["total_spots"] for z in zones)
    best_zone = max(zones, key=lambda z: z["free_spots"]) if zones else None

    return jsonify({
        "zones": [dict(z) for z in zones],
        "spots": [dict(s) for s in spots],
        "total_free": total_free,
        "total_capacity": total_capacity,
        "best_zone": dict(best_zone) if best_zone else None,
        "time": datetime.now().strftime("%H:%M:%S")
    })


@app.route("/report", methods=["POST"])
def report():
    spot_code = request.form["spot_code"]
    status = request.form["status"]

    conn = get_db_connection()

    spot = conn.execute("""
        SELECT destination_tag, zone_name
        FROM parking_spots
        WHERE spot_code = ?
    """, (spot_code,)).fetchone()

    if spot:
        is_free = 1 if status == "Free" else 0

        conn.execute("""
            UPDATE parking_spots
            SET is_free = ?
            WHERE spot_code = ?
        """, (is_free, spot_code))

        stats = conn.execute("""
            SELECT COUNT(*) total,
                   SUM(is_free) free
            FROM parking_spots
            WHERE zone_name = ?
        """, (spot["zone_name"],)).fetchone()

        total = stats["total"]
        free = stats["free"] or 0
        zone_status = calculate_status(free, total)

        conn.execute("""
            UPDATE parking_zones
            SET total_spots = ?, free_spots = ?, status = ?
            WHERE zone_name = ?
        """, (total, free, zone_status, spot["zone_name"]))

        root = ET.Element("report")
        ET.SubElement(root, "spot").text = spot_code
        ET.SubElement(root, "status").text = status
        xml_data = ET.tostring(root, encoding="unicode")

        conn.execute("""
            INSERT INTO parking_reports (spot_code, status, xml_data)
            VALUES (?, ?, ?)
        """, (spot_code, status, xml_data))

        conn.commit()

    conn.close()
    return redirect(request.referrer or url_for("home"))


@app.route("/admin")
def admin():
    conn = get_db_connection()
    zones = conn.execute("""
        SELECT * FROM parking_zones
        ORDER BY zone_name
    """).fetchall()
    conn.close()
    return render_template("admin.html", zones=zones)


@app.route("/update/<int:zone_id>", methods=["POST"])
def update_zone(zone_id):
    free_spots = int(request.form["free_spots"])

    conn = get_db_connection()
    zone = conn.execute("""
        SELECT * FROM parking_zones
        WHERE id = ?
    """, (zone_id,)).fetchone()

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
