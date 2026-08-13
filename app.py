from flask import Flask, render_template, request, redirect
import sqlite3

app = Flask(__name__)


def get_db_connection():
    conn = sqlite3.connect("jobs.db")
    conn.row_factory = sqlite3.Row
    return conn


def setup_database():
    conn = get_db_connection()

    conn.execute("""
        CREATE TABLE IF NOT EXISTS jobs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            company TEXT NOT NULL,
            role TEXT NOT NULL,
            application_date TEXT NOT NULL,
            status TEXT NOT NULL,
            interview_date TEXT,
            job_url TEXT,
            notes TEXT
        )
    """)

    existing_columns = [
        row["name"]
        for row in conn.execute("PRAGMA table_info(jobs)").fetchall()
    ]

    for column in ["interview_date", "job_url", "notes"]:
        if column not in existing_columns:
            conn.execute(
                f"ALTER TABLE jobs ADD COLUMN {column} TEXT"
            )

    conn.commit()
    conn.close()


@app.route("/")
def home():

    search = request.args.get("search", "")
    status = request.args.get("status", "")
    sort = request.args.get("sort", "newest")

    conn = get_db_connection()

    query = "SELECT * FROM jobs WHERE 1=1"
    params = []

    # Search
    if search:
        query += " AND (company LIKE ? OR role LIKE ?)"
        params.extend([
            f"%{search}%",
            f"%{search}%"
        ])

    # Status filter
    if status:
        query += " AND status = ?"
        params.append(status)

    # Sorting
    if sort == "oldest":
        query += " ORDER BY application_date ASC"

    elif sort == "company":
        query += " ORDER BY company ASC"

    else:
        query += " ORDER BY application_date DESC"

    jobs = conn.execute(query, params).fetchall()

    # Dashboard
    total_count = conn.execute(
        "SELECT COUNT(*) FROM jobs"
    ).fetchone()[0]

    applied_count = conn.execute(
        "SELECT COUNT(*) FROM jobs WHERE status = 'Applied'"
    ).fetchone()[0]

    interview_count = conn.execute(
        "SELECT COUNT(*) FROM jobs WHERE status = 'Interview'"
    ).fetchone()[0]

    rejected_count = conn.execute(
        "SELECT COUNT(*) FROM jobs WHERE status = 'Rejected'"
    ).fetchone()[0]

    selected_count = conn.execute(
        "SELECT COUNT(*) FROM jobs WHERE status = 'Selected'"
    ).fetchone()[0]

    conn.close()

    return render_template(
        "index.html",
        jobs=jobs,
        search=search,
        status=status,
        sort=sort,
        total_count=total_count,
        applied_count=applied_count,
        interview_count=interview_count,
        rejected_count=rejected_count,
        selected_count=selected_count
    )


@app.route("/add", methods=["POST"])
def add_job():

    company = request.form["company"]
    role = request.form["role"]
    application_date = request.form["application_date"]
    status = request.form["status"]

    interview_date = request.form.get("interview_date", "")
    job_url = request.form.get("job_url", "")
    notes = request.form.get("notes", "")

    conn = get_db_connection()

    conn.execute("""
        INSERT INTO jobs
        (
            company,
            role,
            application_date,
            status,
            interview_date,
            job_url,
            notes
        )
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


@app.route("/delete/<int:job_id>")
def delete_job(job_id):

    conn = get_db_connection()

    conn.execute(
        "DELETE FROM jobs WHERE id = ?",
        (job_id,)
    )

    conn.commit()
    conn.close()

    return redirect("/")


@app.route("/edit/<int:job_id>", methods=["GET", "POST"])
def edit_job(job_id):

    conn = get_db_connection()

    if request.method == "POST":

        company = request.form["company"]
        role = request.form["role"]
        application_date = request.form["application_date"]
        status = request.form["status"]

        interview_date = request.form.get("interview_date", "")
        job_url = request.form.get("job_url", "")
        notes = request.form.get("notes", "")

        conn.execute("""
            UPDATE jobs
            SET
                company = ?,
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

    job = conn.execute(
        "SELECT * FROM jobs WHERE id = ?",
        (job_id,)
    ).fetchone()

    conn.close()

    return render_template(
        "edit.html",
        job=job
    )


if __name__ == "__main__":
    setup_database()
    app.run(debug=True)