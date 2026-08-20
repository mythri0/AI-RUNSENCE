import sqlite3
import os

db_path = os.path.join("data", "runsense.db")
c = sqlite3.connect(db_path)
rows = c.execute("SELECT id, runner_id, status, video_filename FROM run_sessions ORDER BY id").fetchall()
for r in rows:
    print(r)
