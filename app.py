from flask import Flask, render_template, request, redirect, url_for
import database

app = Flask(__name__)


# =========================
# DASHBOARD / HOME
# =========================

@app.route("/")
def index():

    search = request.args.get("search", "")
    status_filter = request.args.get("status", "")

    conn = database.get_connection()

    query = "SELECT * FROM jobs WHERE 1=1"
    params = []

    # Search
    if search:
        query += """
            AND (
                company LIKE ?
                OR role LIKE ?
                OR notes LIKE ?
            )
        """

        search_value = f"%{search}%"

        params.extend([
            search_value,
            search_value,
            search_value
        ])

    # Status filter
    if status_filter:
        query += " AND status = ?"
        params.append(status_filter)

    query += " ORDER BY id DESC"

    jobs = conn.execute(
        query,
        params
    ).fetchall()

    # Dashboard counts
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
        selected=selected,
        search=search,
        status_filter=status_filter
    )


# =========================
# ADD JOB
# =========================

@app.route("/add", methods=["POST"])
def add_job():

    company = request.form.get("company")
    role = request.form.get("role")
    application_date = request.form.get("application_date")
    status = request.form.get("status")
    interview_date = request.form.get("interview_date")
    job_url = request.form.get("job_url")
    notes = request.form.get("notes")

    database.add_job(
        company,
        role,
        application_date,
        status,
        interview_date,
        job_url,
        notes
    )

    return redirect(url_for("index"))


# =========================
# DELETE JOB
# =========================

@app.route("/delete/<int:job_id>", methods=["POST"])
def delete_job(job_id):

    database.delete_job(job_id)

    return redirect(url_for("index"))


# =========================
# EDIT JOB
# =========================

@app.route("/edit/<int:job_id>")
def edit_job(job_id):

    conn = database.get_connection()

    job = conn.execute(
        "SELECT * FROM jobs WHERE id = ?",
        (job_id,)
    ).fetchone()

    conn.close()

    return render_template(
        "edit.html",
        job=job
    )


# =========================
# UPDATE JOB
# =========================

@app.route("/update/<int:job_id>", methods=["POST"])
def update_job(job_id):

    company = request.form.get("company")
    role = request.form.get("role")
    application_date = request.form.get("application_date")
    status = request.form.get("status")
    interview_date = request.form.get("interview_date")
    job_url = request.form.get("job_url")
    notes = request.form.get("notes")

    conn = database.get_connection()

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

    return redirect(url_for("index"))


# =========================
# RUN APPLICATION
# =========================

if __name__ == "__main__":
    app.run(
        debug=True,
        host="0.0.0.0",
        port=5000
    )