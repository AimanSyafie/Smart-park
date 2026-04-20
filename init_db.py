import os
import sqlite3

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "smartpark.db")

conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS parking_zones (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    zone_name TEXT NOT NULL,
    total_spots INTEGER NOT NULL,
    free_spots INTEGER NOT NULL,
    status TEXT NOT NULL,
    location TEXT,
    destination_tag TEXT
)
""")

cursor.execute("DELETE FROM parking_zones")

sample_data = [
    ("Library Parking", 120, 18, "Available", "Near University Library", "Library"),
    ("Faculty of Science Parking", 90, 7, "Limited", "Near Faculty of Science", "FOS"),
    ("Faculty of Integrated Technologies Parking", 80, 12, "Available", "Near FIT", "FIT"),
    ("School of Digital Science Parking", 70, 5, "Limited", "Near School of Digital Science", "SDS"),
    ("UBDSBE Parking", 75, 0, "Full", "Near UBD School of Business and Economics", "UBDSBE"),
    ("Student Affairs / Cafeteria Parking", 60, 10, "Available", "Near Student Affairs Section", "SAS"),
    ("Administration Building Parking", 50, 3, "Limited", "Near Administration Building", "ADMIN")
]

cursor.executemany("""
INSERT INTO parking_zones (zone_name, total_spots, free_spots, status, location, destination_tag)
VALUES (?, ?, ?, ?, ?, ?)
""", sample_data)

conn.commit()
conn.close()

print("UBD parking database initialized at:", DB_PATH)