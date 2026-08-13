from flask import Flask, render_template, request, redirect
import sqlite3

app = Flask(__name__)

DATABASE = "jobs.db"


def get_db_connection():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_db_connection()

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


# IMPORTANT:
# Create the database/table when Render starts the application
init_db()


@app.route("/")
def home():
    conn = get_db_connection()

    jobs = conn.execute(
        "SELECT * FROM jobs ORDER BY id DESC"
    ).fetchall()

    total = conn.execute(
        "SELECT COUNT(*) FROM jobs"
    ).fetchone()[0]

    applied = conn.execute(
        "SELECT COUNT(*) FROM jobs WHERE status = ?",
        ("Applied",)
    ).fetchone()[0]

    interview = conn.execute(
        "SELECT COUNT(*) FROM jobs WHERE status = ?",
        ("Interview",)
    ).fetchone()[0]

    rejected = conn.execute(
        "SELECT COUNT(*) FROM jobs WHERE status = ?",
        ("Rejected",)
    ).fetchone()[0]

    selected = conn.execute(
        "SELECT COUNT(*) FROM jobs WHERE status = ?",
        ("Selected",)
    ).fetchone()[0]

    conn.close()

    return render_template(
        "index.html",
        jobs=jobs,
        total=total,
        applied=applied,
        interview=interview,
        rejected=rejected,
        selected=selected
    )


@app.route("/add", methods=["POST"])
def add_job():
    company = request.form.get("company")
    role = request.form.get("role")
    application_date = request.form.get("application_date")
    status = request.form.get("status")
    interview_date = request.form.get("interview_date")
    job_url = request.form.get("job_url")
    notes = request.form.get("notes")

    conn = get_db_connection()

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

    return redirect("/")


@app.route("/delete/<int:job_id>", methods=["POST"])
def delete_job(job_id):
    conn = get_db_connection()

    conn.execute(
        "DELETE FROM jobs WHERE id = ?",
        (job_id,)
    )

    conn.commit()
    conn.close()

    return redirect("/")


@app.route("/edit/<int:job_id>")
def edit_job(job_id):
    conn = get_db_connection()

    job = conn.execute(
        "SELECT * FROM jobs WHERE id = ?",
        (job_id,)
    ).fetchone()

    conn.close()

    return render_template(
        "edit.html",
        job=job
    )


@app.route("/update/<int:job_id>", methods=["POST"])
def update_job(job_id):
    company = request.form.get("company")
    role = request.form.get("role")
    application_date = request.form.get("application_date")
    status = request.form.get("status")
    interview_date = request.form.get("interview_date")
    job_url = request.form.get("job_url")
    notes = request.form.get("notes")

    conn = get_db_connection()

    conn.execute("""
        UPDATE jobs
        SET company = ?,
            role = ?,
            application_date = ?,
            status = ?,
            interview_date = ?,
            job_url = ?,
            notes = ?
        WHERE id = ?
    """, (
        company,
        role,
        application_date,
        status,
        interview_date,
        job_url,
        notes,
        job_id
    ))

    conn.commit()
    conn.close()

    return redirect("/")


@app.route("/search")
def search():
    query = request.args.get("q", "")

    conn = get_db_connection()

    jobs = conn.execute("""
        SELECT * FROM jobs
        WHERE company LIKE ?
           OR role LIKE ?
           OR status LIKE ?
        ORDER BY id DESC
    """, (
        "%" + query + "%",
        "%" + query + "%",
        "%" + query + "%"
    )).fetchall()

    conn.close()

    return render_template(
        "index.html",
        jobs=jobs,
        total=len(jobs),
        applied=0,
        interview=0,
        rejected=0,
        selected=0
    )


if __name__ == "__main__":
    app.run(
        host="0.0.0.0",
        port=5000,
        debug=True
    )