import sqlite3
import os

db_path = os.path.join("data", "runsense.db")

try:
    c = sqlite3.connect(db_path)
    c.execute("DROP TABLE IF EXISTS runners")
    c.execute("DROP TABLE IF EXISTS run_sessions")
    c.execute("DROP TABLE IF EXISTS timeline_data")
    c.commit()
    print("TABLES DROPPED SUCCESSFULLY from data/runsense.db")
except Exception as e:
    print("ERROR:", e)
