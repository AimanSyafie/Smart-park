import os
import sqlite3

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "smartpark.db")

conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()

cursor.execute("DROP TABLE IF EXISTS parking_zones")
cursor.execute("DROP TABLE IF EXISTS parking_spots")

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

cursor.execute("""
CREATE TABLE parking_spots (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    destination_tag TEXT NOT NULL,
    zone_name TEXT NOT NULL,
    section_code TEXT NOT NULL,
    spot_code TEXT NOT NULL,
    is_free INTEGER NOT NULL,
    latitude REAL NOT NULL,
    longitude REAL NOT NULL
)
""")

zone_data = [
    ("Library Parking A", 5, 3, "Available", "Near University Library", "Library", 4.9692, 114.8977, "A1"),
    ("Library Parking B", 5, 2, "Limited", "Near University Library", "Library", 4.9695, 114.8981, "A2"),
    ("Faculty of Science Parking A", 5, 2, "Limited", "Near Faculty of Science", "FOS", 4.9710, 114.8928, "B1"),
    ("Faculty of Science Parking B", 5, 0, "Full", "Near Faculty of Science", "FOS", 4.9714, 114.8933, "B2"),
    ("Faculty of Integrated Technologies Parking", 6, 4, "Available", "Near FIT", "FIT", 4.9680, 114.8915, "C1"),
    ("School of Digital Science Parking", 6, 3, "Available", "Near School of Digital Science", "SDS", 4.9673, 114.8940, "D1"),
    ("UBDSBE Parking", 6, 1, "Limited", "Near UBD School of Business and Economics", "UBDSBE", 4.9662, 114.8964, "E1"),
    ("Student Affairs Parking", 6, 4, "Available", "Near Student Affairs Section", "SAS", 4.9701, 114.8950, "F1"),
    ("Administration Parking", 6, 1, "Limited", "Near Administration Building", "ADMIN", 4.9708, 114.8968, "G1")
]

cursor.executemany("""
INSERT INTO parking_zones (
    zone_name, total_spots, free_spots, status, location, destination_tag,
    latitude, longitude, section_code
)
VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
""", zone_data)

spot_data = [
    # Library A
    ("Library", "Library Parking A", "A1", "A1-01", 1, 4.96920, 114.89770),
    ("Library", "Library Parking A", "A1", "A1-02", 1, 4.96922, 114.89773),
    ("Library", "Library Parking A", "A1", "A1-03", 0, 4.96924, 114.89776),
    ("Library", "Library Parking A", "A1", "A1-04", 1, 4.96926, 114.89779),
    ("Library", "Library Parking A", "A1", "A1-05", 0, 4.96928, 114.89782),

    # Library B
    ("Library", "Library Parking B", "A2", "A2-01", 1, 4.96948, 114.89808),
    ("Library", "Library Parking B", "A2", "A2-02", 0, 4.96950, 114.89811),
    ("Library", "Library Parking B", "A2", "A2-03", 1, 4.96952, 114.89814),
    ("Library", "Library Parking B", "A2", "A2-04", 0, 4.96954, 114.89817),
    ("Library", "Library Parking B", "A2", "A2-05", 0, 4.96956, 114.89820),

    # FIT
    ("FIT", "Faculty of Integrated Technologies Parking", "C1", "C1-01", 1, 4.96800, 114.89150),
    ("FIT", "Faculty of Integrated Technologies Parking", "C1", "C1-02", 1, 4.96802, 114.89153),
    ("FIT", "Faculty of Integrated Technologies Parking", "C1", "C1-03", 1, 4.96804, 114.89156),
    ("FIT", "Faculty of Integrated Technologies Parking", "C1", "C1-04", 0, 4.96806, 114.89159),
    ("FIT", "Faculty of Integrated Technologies Parking", "C1", "C1-05", 1, 4.96808, 114.89162),
    ("FIT", "Faculty of Integrated Technologies Parking", "C1", "C1-06", 0, 4.96810, 114.89165),

    # FOS
    ("FOS", "Faculty of Science Parking A", "B1", "B1-01", 1, 4.97100, 114.89280),
    ("FOS", "Faculty of Science Parking A", "B1", "B1-02", 0, 4.97102, 114.89283),
    ("FOS", "Faculty of Science Parking A", "B1", "B1-03", 1, 4.97104, 114.89286),
    ("FOS", "Faculty of Science Parking A", "B1", "B1-04", 0, 4.97106, 114.89289),
    ("FOS", "Faculty of Science Parking A", "B1", "B1-05", 0, 4.97108, 114.89292),

    # Add more dummy rows similarly for SDS, UBDSBE, SAS, ADMIN
]

cursor.executemany("""
INSERT INTO parking_spots (
    destination_tag, zone_name, section_code, spot_code, is_free, latitude, longitude
)
VALUES (?, ?, ?, ?, ?, ?, ?)
""", spot_data)

conn.commit()
conn.close()

print("UBD parking database initialized with exact dummy spots.")
