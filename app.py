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
# AREA CENTER POINTS
# used to center the map
# =========================
AREA_CENTERS = {
    "Library": {"lat": 4.96925, "lng": 114.89778},
    "FOS": {"lat": 4.97105, "lng": 114.89288},
    "FIT": {"lat": 4.96803, "lng": 114.89158},
    "SDS": {"lat": 4.96733, "lng": 114.89408},
    "UBDSBE": {"lat": 4.96623, "lng": 114.89648},
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
# show one selected area
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
# USER REPORT / UPDATE SPOT
# saves update in XML too
# =========================
@app.route("/report", methods=["POST"])
def report():
    area = request.form["area"]
    spot_code = request.form["spot_code"]
    new_status = request.form["new_status"]  # Available or Full

    is_free = 1 if new_status == "Available" else 0

    # Create XML structured text
    root = ET.Element("report")
    ET.SubElement(root, "area").text = area
    ET.SubElement(root, "spot_code").text = spot_code
    ET.SubElement(root, "new_status").text = new_status

    xml_data = ET.tostring(root, encoding="unicode")

    conn = get_db_connection()

    # Update spot
    conn.execute("""
        UPDATE parking_spots
        SET is_free = ?
        WHERE spot_code = ?
    """, (is_free, spot_code))

    # Save XML report log
    conn.execute("""
        INSERT INTO parking_reports (area, spot_code, new_status, xml_data)
        VALUES (?, ?, ?, ?)
    """, (area, spot_code, new_status, xml_data))

    conn.commit()
    conn.close()

    return redirect(url_for("location", area=area))


# =========================
# ADMIN PAGE
# simple query view
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
