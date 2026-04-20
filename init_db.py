import os
import sqlite3

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "smartpark.db")

conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()

cursor.execute("DROP TABLE IF EXISTS parking_zones")

cursor.execute("""
CREATE TABLE parking_zones (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    zone_name TEXT NOT NULL,
    total_spots INTEGER NOT NULL,
    free_spots INTEGER NOT NULL,
    status TEXT NOT NULL,
    location TEXT,
    destination_tag TEXT,
    latitude REAL,
    longitude REAL,
    section_code TEXT
)
""")

sample_data = [
    ("Library Parking A", 40, 12, "Available", "Near University Library", "Library", 4.9692, 114.8977, "A1"),
    ("Library Parking B", 35, 5, "Limited", "Near University Library", "Library", 4.9695, 114.8981, "A2"),
    ("Faculty of Science Parking A", 30, 7, "Limited", "Near Faculty of Science", "FOS", 4.9710, 114.8928, "B1"),
    ("Faculty of Science Parking B", 25, 0, "Full", "Near Faculty of Science", "FOS", 4.9714, 114.8933, "B2"),
    ("Faculty of Integrated Technologies Parking", 45, 15, "Available", "Near FIT", "FIT", 4.9680, 114.8915, "C1"),
    ("School of Digital Science Parking", 28, 9, "Available", "Near School of Digital Science", "SDS", 4.9673, 114.8940, "D1"),
    ("UBDSBE Parking", 36, 3, "Limited", "Near UBD School of Business and Economics", "UBDSBE", 4.9662, 114.8964, "E1"),
    ("Student Affairs Parking", 20, 8, "Available", "Near Student Affairs Section", "SAS", 4.9701, 114.8950, "F1"),
    ("Administration Parking", 18, 2, "Limited", "Near Administration Building", "ADMIN", 4.9708, 114.8968, "G1")
]

cursor.executemany("""
INSERT INTO parking_zones (
    zone_name, total_spots, free_spots, status, location, destination_tag,
    latitude, longitude, section_code
)
VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
""", sample_data)

conn.commit()
conn.close()

print("UBD parking database initialized with map data.")
