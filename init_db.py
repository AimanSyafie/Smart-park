import os
import sqlite3
import random

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "smartpark.db")

conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()

cursor.execute("DROP TABLE IF EXISTS parking_zones")
cursor.execute("DROP TABLE IF EXISTS parking_spots")
cursor.execute("DROP TABLE IF EXISTS parking_reports")

# Zones
cursor.execute("""
CREATE TABLE parking_zones (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    zone_name TEXT,
    total_spots INTEGER,
    free_spots INTEGER,
    status TEXT,
    location TEXT,
    destination_tag TEXT
)
""")

# Spots (REAL MAP)
cursor.execute("""
CREATE TABLE parking_spots (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    destination_tag TEXT,
    zone_name TEXT,
    spot_code TEXT,
    is_free INTEGER,
    latitude REAL,
    longitude REAL
)
""")

# User Reports (NEW FEATURE)
cursor.execute("""
CREATE TABLE parking_reports (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    spot_code TEXT,
    status TEXT,
    xml_data TEXT
)
""")

# Dummy zones
zones = [
    ("Library Parking", 20, 10, "Available", "Library Area", "Library"),
    ("FIT Parking", 20, 12, "Available", "FIT Area", "FIT"),
]

cursor.executemany("""
INSERT INTO parking_zones 
(zone_name, total_spots, free_spots, status, location, destination_tag)
VALUES (?, ?, ?, ?, ?, ?)
""", zones)

# 🔥 SPREAD-OUT GRID MAP (IMPORTANT)
base_locations = {
    "Library": (4.9693, 114.8979),
    "FIT": (4.9680, 114.8915)
}

spot_data = []

for area, (lat, lng) in base_locations.items():
    for i in range(20):
        # create grid spread
        offset_lat = lat + (i % 5) * 0.00003
        offset_lng = lng + (i // 5) * 0.00003

        spot_data.append((
            area,
            f"{area} Zone",
            f"{area[:2]}-{i+1}",
            random.choice([0, 1]),
            offset_lat,
            offset_lng
        ))

cursor.executemany("""
INSERT INTO parking_spots
(destination_tag, zone_name, spot_code, is_free, latitude, longitude)
VALUES (?, ?, ?, ?, ?, ?)
""", spot_data)

conn.commit()
conn.close()

print("Database with spread-out map + reports ready.")
