import sqlite3

conn = sqlite3.connect("jobs.db")

conn.execute("""
CREATE TABLE IF NOT EXISTS jobs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    company TEXT NOT NULL,
    role TEXT NOT NULL,
    application_date TEXT,
    status TEXT
)
""")

conn.commit()
conn.close()

print("Database and jobs table created successfully!")