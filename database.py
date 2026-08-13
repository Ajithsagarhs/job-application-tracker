import sqlite3

DATABASE = "jobs.db"


def get_connection():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn


def create_table():
    conn = get_connection()

    conn.execute("""
        CREATE TABLE IF NOT EXISTS jobs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            company TEXT NOT NULL,
            role TEXT NOT NULL,
            application_date TEXT,
            status TEXT,
            interview_date TEXT,
            job_url TEXT,
            notes TEXT
        )
    """)

    conn.commit()
    conn.close()


def add_job(company, role, application_date, status,
            interview_date, job_url, notes):

    conn = get_connection()

    conn.execute("""
        INSERT INTO jobs
        (company, role, application_date, status,
         interview_date, job_url, notes)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (
        company,
        role,
        application_date,
        status,
        interview_date,
        job_url,
        notes
    ))

    conn.commit()
    conn.close()


def get_all_jobs():
    conn = get_connection()

    jobs = conn.execute("""
        SELECT * FROM jobs
        ORDER BY id DESC
    """).fetchall()

    conn.close()

    return jobs


def delete_job(job_id):
    conn = get_connection()

    conn.execute(
        "DELETE FROM jobs WHERE id = ?",
        (job_id,)
    )

    conn.commit()
    conn.close()


create_table()