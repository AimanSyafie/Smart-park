import os
import sqlite3
import xml.etree.ElementTree as ET
from flask import Flask, render_template, request, redirect, url_for, jsonify

# =========================
# APP SETUP
# =========================
app = Flask(__name__)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "smartpark.db")


# =========================
# DATABASE CONNECTION
# =========================
def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


# =========================
# CREATE / RESET DATABASE
# =========================
def setup_database():
    conn = get_db_connection()
    cursor = conn.cursor()

    # Create parking_spots table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS parking_spots (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        area TEXT NOT NULL,
        spot_code TEXT NOT NULL,
        latitude REAL NOT NULL,
        longitude REAL NOT NULL,
        is_free INTEGER NOT NULL
    )
    """)

    # Create parking_reports table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS parking_reports (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        area TEXT NOT NULL,
        spot_code TEXT NOT NULL,
        new_status TEXT NOT NULL,
        xml_data TEXT NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)

    # IMPORTANT: clear old parking spots
    cursor.execute("DELETE FROM parking_spots")

    spots = []

    # =========================
    # FUNCTION TO ADD SPOTS
    # =========================
    def add_spots(area, base_lat, base_lng, free_spot_codes=None):
        if free_spot_codes is None:
            free_spot_codes = []

        count = 1

        # 2 parking rows, 5 spots each
        for row in range(2):
            for col in range(5):
                spot_code = f"{area[:3].upper()}-{count:02d}"

                # parking row layout
                lat = base_lat + (row * 0.00012)
                lng = base_lng + (col * 0.00008)

                is_free = 1 if spot_code in free_spot_codes else 0

                spots.append((area, spot_code, lat, lng, is_free))
                count += 1

    # =========================
    # USE UPDATED COORDINATES
    # =========================
    add_spots("Library", 4.96920, 114.89770)
    add_spots("FOS",     4.975646, 114.895485)
    add_spots("FIT",     4.96800, 114.89150)
    add_spots("SDS",     4.976578, 114.893015, free_spot_codes=["SDS-02", "SDS-05", "SDS-08"])
    add_spots("UBDSBE",  4.974128, 114.892298)
    add_spots("SAS",     4.97010, 114.89500)
    add_spots("ADMIN",   4.97080, 114.89680)

    # Insert all spots
    cursor.executemany("""
    INSERT INTO parking_spots (area, spot_code, latitude, longitude, is_free)
    VALUES (?, ?, ?, ?, ?)
    """, spots)

    conn.commit()
    conn.close()


# Run setup at startup
setup_database()


# =========================
# AREA CENTER POINTS
# =========================
AREA_CENTERS = {
    "Library": {"lat": 4.96925, "lng": 114.89778},
    "FOS": {"lat": 4.975646, "lng": 114.895485},
    "FIT": {"lat": 4.96803, "lng": 114.89158},
    "SDS": {"lat": 4.976578, "lng": 114.893015},
    "UBDSBE": {"lat": 4.974128, "lng": 114.892298},
    "SAS": {"lat": 4.97013, "lng": 114.89508},
    "ADMIN": {"lat": 4.97083, "lng": 114.89688},
}


# =========================
# HOME PAGE
# =========================
@app.route("/")
def home():
    areas = ["Library", "FOS", "FIT", "SDS", "UBDSBE", "SAS", "ADMIN"]
    return render_template("home.html", areas=areas)


# =========================
# LOCATION PAGE
# =========================
@app.route("/location/<area>")
def location(area):
    conn = get_db_connection()

    spots = conn.execute("""
        SELECT * FROM parking_spots
        WHERE area = ?
        ORDER BY spot_code
    """, (area,)).fetchall()

    conn.close()

    total_spots = len(spots)
    free_spots = sum(1 for s in spots if s["is_free"] == 1)
    full_spots = total_spots - free_spots

    center = AREA_CENTERS.get(area, {"lat": 4.9685, "lng": 114.8955})

    return render_template(
        "location.html",
        area=area,
        spots=spots,
        total_spots=total_spots,
        free_spots=free_spots,
        full_spots=full_spots,
        center=center
    )


# =========================
# API FOR AUTO REFRESH
# =========================
@app.route("/api/location/<area>")
def api_location(area):
    conn = get_db_connection()

    spots = conn.execute("""
        SELECT * FROM parking_spots
        WHERE area = ?
        ORDER BY spot_code
    """, (area,)).fetchall()

    conn.close()

    total_spots = len(spots)
    free_spots = sum(1 for s in spots if s["is_free"] == 1)
    full_spots = total_spots - free_spots

    return jsonify({
        "area": area,
        "total_spots": total_spots,
        "free_spots": free_spots,
        "full_spots": full_spots,
        "spots": [dict(s) for s in spots]
    })


# =========================
# USER REPORT
# =========================
@app.route("/report", methods=["POST"])
def report():
    area = request.form["area"]
    spot_code = request.form["spot_code"]
    new_status = request.form["new_status"]

    is_free = 1 if new_status == "Available" else 0

    # XML structured text
    root = ET.Element("report")
    ET.SubElement(root, "area").text = area
    ET.SubElement(root, "spot_code").text = spot_code
    ET.SubElement(root, "new_status").text = new_status
    xml_data = ET.tostring(root, encoding="unicode")

    conn = get_db_connection()

    conn.execute("""
        UPDATE parking_spots
        SET is_free = ?
        WHERE spot_code = ?
    """, (is_free, spot_code))

    conn.execute("""
        INSERT INTO parking_reports (area, spot_code, new_status, xml_data)
        VALUES (?, ?, ?, ?)
    """, (area, spot_code, new_status, xml_data))

    conn.commit()
    conn.close()

    return redirect(url_for("location", area=area))


# =========================
# ADMIN PAGE
# =========================
@app.route("/admin")
def admin():
    conn = get_db_connection()

    reports = conn.execute("""
        SELECT * FROM parking_reports
        ORDER BY created_at DESC
    """).fetchall()

    conn.close()
    return render_template("admin.html", reports=reports)


# =========================
# RUN APP
# =========================
if __name__ == "__main__":
    app.run(debug=True)
