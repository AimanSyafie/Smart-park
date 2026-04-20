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


def seed_database():
    conn = get_db_connection()
    cursor = conn.cursor()

    # Create parking_zones
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS parking_zones (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        zone_name TEXT,
        total_spots INTEGER,
        free_spots INTEGER,
        status TEXT,
        location TEXT,
        destination_tag TEXT
    )
    """)

    # Create parking_spots
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS parking_spots (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        destination_tag TEXT,
        zone_name TEXT,
        spot_code TEXT,
        is_free INTEGER,
        latitude REAL,
        longitude REAL
    )
    """)

    # Create parking_reports
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS parking_reports (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        spot_code TEXT,
        status TEXT,
        xml_data TEXT
    )
    """)

    zone_count = cursor.execute("SELECT COUNT(*) AS c FROM parking_zones").fetchone()["c"]
    spot_count = cursor.execute("SELECT COUNT(*) AS c FROM parking_spots").fetchone()["c"]

    if zone_count == 0:
        zones = [
            ("Library Parking", 20, 10, "Available", "Library Area", "Library"),
            ("FIT Parking", 20, 12, "Available", "FIT Area", "FIT"),
            ("FOS Parking", 20, 8, "Limited", "Faculty of Science Area", "FOS"),
            ("SDS Parking", 20, 9, "Available", "School of Digital Science Area", "SDS"),
            ("UBDSBE Parking", 20, 5, "Limited", "UBDSBE Area", "UBDSBE"),
            ("SAS Parking", 20, 11, "Available", "Student Affairs Area", "SAS"),
            ("ADMIN Parking", 20, 4, "Limited", "Administration Area", "ADMIN"),
        ]

        cursor.executemany("""
        INSERT INTO parking_zones
        (zone_name, total_spots, free_spots, status, location, destination_tag)
        VALUES (?, ?, ?, ?, ?, ?)
        """, zones)

    if spot_count == 0:
        base_locations = {
            "Library": (4.9693, 114.8979),
            "FIT": (4.9680, 114.8915),
            "FOS": (4.9712, 114.8930),
            "SDS": (4.9673, 114.8940),
            "UBDSBE": (4.9662, 114.8964),
            "SAS": (4.9701, 114.8950),
            "ADMIN": (4.9708, 114.8968),
        }

        spot_rows = []

        for area, (lat, lng) in base_locations.items():
            for i in range(20):
                row = i // 5
                col = i % 5

                offset_lat = lat + (row * 0.00003)
                offset_lng = lng + (col * 0.00003)

                is_free = 1 if i % 3 != 0 else 0

                spot_rows.append((
                    area,
                    f"{area} Parking",
                    f"{area[:2].upper()}-{i+1:02d}",
                    is_free,
                    offset_lat,
                    offset_lng
                ))

        cursor.executemany("""
        INSERT INTO parking_spots
        (destination_tag, zone_name, spot_code, is_free, latitude, longitude)
        VALUES (?, ?, ?, ?, ?, ?)
        """, spot_rows)

    conn.commit()
    conn.close()


seed_database()


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
        SELECT * FROM parking_zones WHERE destination_tag = ?
    """, (destination,)).fetchall()

    spots = conn.execute("""
        SELECT * FROM parking_spots WHERE destination_tag = ?
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
            SELECT COUNT(*) total, SUM(is_free) free
            FROM parking_spots
            WHERE destination_tag = ?
        """, (spot["destination_tag"],)).fetchone()

        total = stats["total"] or 0
        free = stats["free"] or 0
        zone_status = calculate_status(free, total)

        conn.execute("""
            UPDATE parking_zones
            SET total_spots = ?, free_spots = ?, status = ?
            WHERE destination_tag = ?
        """, (total, free, zone_status, spot["destination_tag"]))

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
