import os
import sqlite3
import random
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


def build_spot_rows():
    spot_rows = []

    # ------------------------
    # LIBRARY (wide horizontal lot)
    # ------------------------
    base_lat, base_lng = 4.9693, 114.8979
    for row in range(3):
        for col in range(10):
            spot_rows.append((
                "Library",
                "Library Parking",
                f"LB-{row}{col}",
                random.choice([0, 1]),
                base_lat + (row * 0.00002),
                base_lng + (col * 0.00003)
            ))

    # ------------------------
    # FIT (vertical layout)
    # ------------------------
    base_lat, base_lng = 4.9680, 114.8915
    for col in range(3):
        for row in range(8):
            spot_rows.append((
                "FIT",
                "FIT Parking",
                f"FT-{row}{col}",
                random.choice([0, 1]),
                base_lat + (row * 0.00003),
                base_lng + (col * 0.00002)
            ))

    # ------------------------
    # ADMIN (L-shape layout)
    # ------------------------
    base_lat, base_lng = 4.9708, 114.8968
    for i in range(8):
        spot_rows.append((
            "ADMIN",
            "ADMIN Parking",
            f"AD-A{i}",
            random.choice([0, 1]),
            base_lat,
            base_lng + (i * 0.000025)
        ))

    for i in range(6):
        spot_rows.append((
            "ADMIN",
            "ADMIN Parking",
            f"AD-B{i}",
            random.choice([0, 1]),
            base_lat + (i * 0.000025),
            base_lng
        ))

    # ------------------------
    # FOS (cluster style)
    # ------------------------
    base_lat, base_lng = 4.9712, 114.8930
    for i in range(15):
        spot_rows.append((
            "FOS",
            "FOS Parking",
            f"FS-{i}",
            random.choice([0, 1]),
            base_lat + random.uniform(-0.0001, 0.0001),
            base_lng + random.uniform(-0.0001, 0.0001)
        ))

    # ------------------------
    # SDS (small compact grid)
    # ------------------------
    base_lat, base_lng = 4.9673, 114.8940
    for row in range(3):
        for col in range(4):
            spot_rows.append((
                "SDS",
                "SDS Parking",
                f"SD-{row}{col}",
                random.choice([0, 1]),
                base_lat + (row * 0.00002),
                base_lng + (col * 0.00002)
            ))

    # ------------------------
    # UBDSBE (diagonal style)
    # ------------------------
    base_lat, base_lng = 4.9662, 114.8964
    for i in range(10):
        spot_rows.append((
            "UBDSBE",
            "UBDSBE Parking",
            f"UB-{i}",
            random.choice([0, 1]),
            base_lat + (i * 0.00002),
            base_lng + (i * 0.00002)
        ))

    # ------------------------
    # SAS (rectangle)
    # ------------------------
    base_lat, base_lng = 4.9701, 114.8950
    for row in range(4):
        for col in range(4):
            spot_rows.append((
                "SAS",
                "SAS Parking",
                f"SA-{row}{col}",
                random.choice([0, 1]),
                base_lat + (row * 0.000025),
                base_lng + (col * 0.000025)
            ))

    return spot_rows


def compute_zone_summary_from_spots(spot_rows):
    summary = {}

    for destination_tag, zone_name, spot_code, is_free, latitude, longitude in spot_rows:
        if destination_tag not in summary:
            summary[destination_tag] = {
                "zone_name": zone_name,
                "total_spots": 0,
                "free_spots": 0,
                "status": "Available",
                "location": AREA_CENTERS[destination_tag]["label"],
                "destination_tag": destination_tag
            }

        summary[destination_tag]["total_spots"] += 1
        summary[destination_tag]["free_spots"] += is_free

    zones = []
    for item in summary.values():
        item["status"] = calculate_status(item["free_spots"], item["total_spots"])
        zones.append((
            item["zone_name"],
            item["total_spots"],
            item["free_spots"],
            item["status"],
            item["location"],
            item["destination_tag"]
        ))

    return zones


def seed_database():
    conn = get_db_connection()
    cursor = conn.cursor()

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

    if zone_count == 0 or spot_count == 0:
        cursor.execute("DELETE FROM parking_zones")
        cursor.execute("DELETE FROM parking_spots")

        spot_rows = build_spot_rows()
        zone_rows = compute_zone_summary_from_spots(spot_rows)

        cursor.executemany("""
        INSERT INTO parking_zones
        (zone_name, total_spots, free_spots, status, location, destination_tag)
        VALUES (?, ?, ?, ?, ?, ?)
        """, zone_rows)

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
