import os
import sqlite3

# =========================
# DATABASE PATH
# =========================
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "smartpark.db")

conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()

# =========================
# DROP OLD TABLES
# =========================
cursor.execute("DROP TABLE IF EXISTS parking_spots")
cursor.execute("DROP TABLE IF EXISTS parking_reports")

# =========================
# TABLE 1: PARKING SPOTS
# =========================
cursor.execute("""
CREATE TABLE parking_spots (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    area TEXT NOT NULL,
    spot_code TEXT NOT NULL,
    latitude REAL NOT NULL,
    longitude REAL NOT NULL,
    is_free INTEGER NOT NULL
)
""")

# =========================
# TABLE 2: USER REPORTS
# =========================
cursor.execute("""
CREATE TABLE parking_reports (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    area TEXT NOT NULL,
    spot_code TEXT NOT NULL,
    new_status TEXT NOT NULL,
    xml_data TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)
""")

# =========================
# STORE ALL SPOTS HERE
# =========================
spots = []

# =========================
# FUNCTION TO ADD SPOTS
# Real parking row layout
# =========================
def add_spots(area, base_lat, base_lng, free_spot_codes=None):
    if free_spot_codes is None:
        free_spot_codes = []

    count = 1

    # 2 rows, 5 spots each
    for row in range(2):
        for col in range(5):
            spot_code = f"{area[:3].upper()}-{count:02d}"

            # realistic row layout
            lat = base_lat + (row * 0.00012)
            lng = base_lng + (col * 0.00008)

            is_free = 1 if spot_code in free_spot_codes else 0

            spots.append((area, spot_code, lat, lng, is_free))
            count += 1

# =========================
# DUMMY DATA
# all full except SDS has 3 free
# =========================
add_spots("Library", 4.96920, 114.89770)
add_spots("FOS",     4.975646, 114.895485)
add_spots("FIT",     4.96800, 114.89150)
add_spots("SDS",     4.976578, 114.893015, free_spot_codes=["SDS-02", "SDS-05", "SDS-08"])
add_spots("UBDSBE",  4.974128, 114.892298)
add_spots("SAS",     4.97010, 114.89500)
add_spots("ADMIN",   4.97080, 114.89680)

# =========================
# INSERT INTO DATABASE
# =========================
cursor.executemany("""
INSERT INTO parking_spots (area, spot_code, latitude, longitude, is_free)
VALUES (?, ?, ?, ?, ?)
""", spots)

conn.commit()
conn.close()

print("Database created successfully:", DB_PATH)
