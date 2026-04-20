import os
import xml.etree.ElementTree as ET
from flask import Flask, render_template, request, redirect, url_for, jsonify
import psycopg2
import psycopg2.extras

app = Flask(__name__)

DATABASE_URL = os.getenv("DATABASE_URL")

def get_db_connection():
    conn = psycopg2.connect(DATABASE_URL)
    return conn

def setup_database():
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS parking_spots (
        id SERIAL PRIMARY KEY,
        area TEXT NOT NULL,
        spot_code TEXT NOT NULL,
        latitude DOUBLE PRECISION NOT NULL,
        longitude DOUBLE PRECISION NOT NULL,
        is_free INTEGER NOT NULL
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS parking_reports (
        id SERIAL PRIMARY KEY,
        area TEXT NOT NULL,
        spot_code TEXT NOT NULL,
        new_status TEXT NOT NULL,
        xml_data TEXT NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)

    cursor.execute("SELECT COUNT(*) FROM parking_spots")
    count = cursor.fetchone()[0]

    if count == 0:
        spots = []

        def add_spots(area, base_lat, base_lng, free_spot_codes=None):
            if free_spot_codes is None:
                free_spot_codes = []

            count = 1
            for row in range(2):
                for col in range(5):
                    spot_code = f"{area[:3].upper()}-{count:02d}"
                    lat = base_lat + (row * 0.00012)
                    lng = base_lng + (col * 0.00008)
                    is_free = 1 if spot_code in free_spot_codes else 0
                    spots.append((area, spot_code, lat, lng, is_free))
                    count += 1

        add_spots("Library", 4.96920, 114.89770)
        add_spots("FOS", 4.975646, 114.895485)
        add_spots("FIT", 4.96800, 114.89150)
        add_spots("SDS", 4.976578, 114.893015, free_spot_codes=["SDS-02", "SDS-05", "SDS-08"])
        add_spots("UBDSBE", 4.974128, 114.892298)
        add_spots("SAS", 4.97010, 114.89500)
        add_spots("ADMIN", 4.97080, 114.89680)

        psycopg2.extras.execute_batch(cursor, """
            INSERT INTO parking_spots (area, spot_code, latitude, longitude, is_free)
            VALUES (%s, %s, %s, %s, %s)
        """, spots)

    conn.commit()
    cursor.close()
    conn.close()

setup_database()

AREA_CENTERS = {
    "Library": {"lat": 4.96925, "lng": 114.89778},
    "FOS": {"lat": 4.975646, "lng": 114.895485},
    "FIT": {"lat": 4.96803, "lng": 114.89158},
    "SDS": {"lat": 4.976578, "lng": 114.893015},
    "UBDSBE": {"lat": 4.974128, "lng": 114.892298},
    "SAS": {"lat": 4.97013, "lng": 114.89508},
    "ADMIN": {"lat": 4.97083, "lng": 114.89688},
}

@app.route("/")
def home():
    areas = ["Library", "FOS", "FIT", "SDS", "UBDSBE", "SAS", "ADMIN"]
    return render_template("home.html", areas=areas)

@app.route("/location/<area>")
def location(area):
    conn = get_db_connection()
    cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

    cursor.execute("""
        SELECT * FROM parking_spots
        WHERE area = %s
        ORDER BY spot_code
    """, (area,))
    spots = cursor.fetchall()

    cursor.execute("""
        SELECT * FROM parking_reports
        WHERE area = %s
        ORDER BY created_at DESC
        LIMIT 5
    """, (area,))
    recent_reports = cursor.fetchall()

    cursor.close()
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
        center=center,
        recent_reports=recent_reports
    )

@app.route("/api/location/<area>")
def api_location(area):
    conn = get_db_connection()
    cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

    cursor.execute("""
        SELECT * FROM parking_spots
        WHERE area = %s
        ORDER BY spot_code
    """, (area,))
    spots = cursor.fetchall()

    cursor.close()
    conn.close()

    total_spots = len(spots)
    free_spots = sum(1 for s in spots if s["is_free"] == 1)
    full_spots = total_spots - free_spots

    return jsonify({
        "area": area,
        "total_spots": total_spots,
        "free_spots": free_spots,
        "full_spots": full_spots,
        "spots": spots
    })

@app.route("/report", methods=["POST"])
def report():
    area = request.form["area"]
    spot_code = request.form["spot_code"]
    new_status = request.form["new_status"]

    is_free = 1 if new_status == "Available" else 0

    root = ET.Element("parking_report")
    ET.SubElement(root, "area").text = area
    ET.SubElement(root, "spot_code").text = spot_code
    ET.SubElement(root, "new_status").text = new_status
    xml_data = ET.tostring(root, encoding="unicode")

    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("""
        UPDATE parking_spots
        SET is_free = %s
        WHERE spot_code = %s
    """, (is_free, spot_code))

    cursor.execute("""
        INSERT INTO parking_reports (area, spot_code, new_status, xml_data)
        VALUES (%s, %s, %s, %s)
    """, (area, spot_code, new_status, xml_data))

    conn.commit()
    cursor.close()
    conn.close()

    return redirect(url_for("location", area=area))

@app.route("/admin")
def admin():
    conn = get_db_connection()
    cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

    cursor.execute("""
        SELECT * FROM parking_reports
        ORDER BY created_at DESC
    """)
    reports = cursor.fetchall()

    cursor.execute("""
        SELECT * FROM parking_spots
        ORDER BY area, spot_code
    """)
    spots = cursor.fetchall()

    cursor.close()
    conn.close()

    return render_template("admin.html", reports=reports, spots=spots)

if __name__ == "__main__":
    app.run(debug=True)
