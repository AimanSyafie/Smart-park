import os
import xml.etree.ElementTree as ET
from flask import Flask, render_template, request, redirect, url_for, jsonify
import psycopg2
import psycopg2.extras

app = Flask(__name__)

# =========================
# DATABASE CONFIG
# =========================
DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    raise ValueError("DATABASE_URL not set")

def get_db_connection():
    try:
        return psycopg2.connect(DATABASE_URL)
    except Exception as e:
        print("Database connection error:", e)
        raise


# =========================
# CREATE TABLES (ONLY)
# =========================
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

    conn.commit()
    cursor.close()
    conn.close()


# Run once
setup_database()


# =========================
# AREA MAP CENTERS
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


# =========================
# API (REAL-TIME DATA)
# =========================
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


# =========================
# USER UPDATE (IMPORTANT)
# =========================
@app.route("/report", methods=["POST"])
def report():
    area = request.form["area"]
    spot_code = request.form["spot_code"]
    new_status = request.form["new_status"]

    is_free = 1 if new_status == "Available" else 0

    # XML structured data
    root = ET.Element("parking_report")
    ET.SubElement(root, "area").text = area
    ET.SubElement(root, "spot_code").text = spot_code
    ET.SubElement(root, "new_status").text = new_status
    xml_data = ET.tostring(root, encoding="unicode")

    conn = get_db_connection()
    cursor = conn.cursor()

    # SAFER UPDATE (area included)
    cursor.execute("""
        UPDATE parking_spots
        SET is_free = %s
        WHERE spot_code = %s AND area = %s
    """, (is_free, spot_code, area))

    # INSERT REPORT
    cursor.execute("""
        INSERT INTO parking_reports (area, spot_code, new_status, xml_data)
        VALUES (%s, %s, %s, %s)
    """, (area, spot_code, new_status, xml_data))

    conn.commit()
    cursor.close()
    conn.close()

    return redirect(url_for("location", area=area))


# =========================
# ADMIN DASHBOARD
# =========================
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


# =========================
# RUN APP
# =========================
if __name__ == "__main__":
    app.run(debug=True)
