from flask import Flask, render_template, request, redirect, flash
import sqlite3
import re

app = Flask(__name__)

app.secret_key = "jobtracker-secret-key"


# ==========================================
# DATABASE CONNECTION
# ==========================================

def get_db():

    conn = sqlite3.connect("jobs.db")

    conn.row_factory = sqlite3.Row

    return conn


# ==========================================
# DASHBOARD
# ==========================================

@app.route("/")
def index():

    conn = get_db()

    jobs = conn.execute("""
        SELECT *
        FROM jobs
        ORDER BY id DESC
    """).fetchall()


    total = conn.execute("""
        SELECT COUNT(*)
        FROM jobs
    """).fetchone()[0]


    applied = conn.execute("""
        SELECT COUNT(*)
        FROM jobs
        WHERE status = ?
    """, ("Applied",)).fetchone()[0]


    interviews = conn.execute("""
        SELECT COUNT(*)
        FROM jobs
        WHERE status = ?
    """, ("Interview",)).fetchone()[0]


    rejected = conn.execute("""
        SELECT COUNT(*)
        FROM jobs
        WHERE status = ?
    """, ("Rejected",)).fetchone()[0]


    selected = conn.execute("""
        SELECT COUNT(*)
        FROM jobs
        WHERE status = ?
    """, ("Selected",)).fetchone()[0]


    offers = conn.execute("""
        SELECT COUNT(*)
        FROM jobs
        WHERE status = ?
    """, ("Offer",)).fetchone()[0]


    conn.close()


    return render_template(
        "index.html",
        jobs=jobs,
        total=total,
        applied=applied,
        interviews=interviews,
        rejected=rejected,
        selected=selected,
        offers=offers
    )


# ==========================================
# APPLICATIONS PAGE
# ==========================================

@app.route("/applications")
def applications():

    conn = get_db()

    jobs = conn.execute("""
        SELECT *
        FROM jobs
        ORDER BY id DESC
    """).fetchall()

    conn.close()


    return render_template(
        "applications.html",
        jobs=jobs
    )


# ==========================================
# INTERVIEWS PAGE
# ==========================================

@app.route("/interviews")
def interviews_page():

    conn = get_db()

    interviews = conn.execute("""
        SELECT *
        FROM jobs
        WHERE interview_date IS NOT NULL
        AND interview_date != ''
        ORDER BY interview_date ASC
    """).fetchall()

    conn.close()


    return render_template(
        "interviews.html",
        interviews=interviews
    )


# ==========================================
# SETTINGS
# ==========================================

@app.route("/settings")
def settings():

    return render_template("settings.html")


# ==========================================
# ADD APPLICATION
# ==========================================

@app.route("/add", methods=["GET", "POST"])
def add_application():

    if request.method == "POST":

        company = request.form.get(
            "company", ""
        ).strip()


        role = request.form.get(
            "role", ""
        ).strip()


        application_date = request.form.get(
            "date", ""
        ).strip()


        status = request.form.get(
            "status", ""
        ).strip()


        interview_date = request.form.get(
            "interview", ""
        ).strip()


        job_url = request.form.get(
            "url", ""
        ).strip()


        notes = request.form.get(
            "notes", ""
        ).strip()


        # ==================================
        # VALIDATION
        # ==================================

        if not company:

            flash(
                "Company name is required.",
                "error"
            )

            return render_template(
                "add.html"
            )


        if not role:

            flash(
                "Job role is required.",
                "error"
            )

            return render_template(
                "add.html"
            )


        if not application_date:

            flash(
                "Application date is required.",
                "error"
            )

            return render_template(
                "add.html"
            )


        allowed_statuses = [
            "Applied",
            "Interview",
            "Rejected",
            "Selected",
            "Offer"
        ]


        if status not in allowed_statuses:

            flash(
                "Please select a valid application status.",
                "error"
            )

            return render_template(
                "add.html"
            )


        # ==================================
        # URL VALIDATION
        # ==================================

        if job_url:

            url_pattern = r"^https?://.+"


            if not re.match(
                url_pattern,
                job_url
            ):

                flash(
                    "Job URL must start with http:// or https://",
                    "error"
                )

                return render_template(
                    "add.html"
                )


        # ==================================
        # INSERT APPLICATION
        # ==================================

        conn = get_db()


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


        flash(
            "Application added successfully!",
            "success"
        )


        return redirect("/")


    return render_template(
        "add.html"
    )


# ==========================================
# VIEW APPLICATION
# ==========================================

@app.route("/view/<int:id>")
def view_application(id):

    conn = get_db()


    job = conn.execute("""
        SELECT *
        FROM jobs
        WHERE id = ?
    """, (id,)).fetchone()


    conn.close()


    if job is None:

        flash(
            "Application not found.",
            "error"
        )

        return redirect("/")


    return render_template(
        "view.html",
        job=job
    )


# ==========================================
# EDIT APPLICATION
# ==========================================

@app.route(
    "/edit/<int:id>",
    methods=["GET", "POST"]
)
def edit_application(id):

    conn = get_db()


    job = conn.execute("""
        SELECT *
        FROM jobs
        WHERE id = ?
    """, (id,)).fetchone()


    if job is None:

        conn.close()

        flash(
            "Application not found.",
            "error"
        )

        return redirect("/")


    # ==================================
    # UPDATE
    # ==================================

    if request.method == "POST":

        company = request.form.get(
            "company", ""
        ).strip()


        role = request.form.get(
            "role", ""
        ).strip()


        application_date = request.form.get(
            "date", ""
        ).strip()


        status = request.form.get(
            "status", ""
        ).strip()


        interview_date = request.form.get(
            "interview", ""
        ).strip()


        job_url = request.form.get(
            "url", ""
        ).strip()


        notes = request.form.get(
            "notes", ""
        ).strip()


        # ==================================
        # VALIDATION
        # ==================================

        if not company:

            conn.close()

            flash(
                "Company name is required.",
                "error"
            )

            return render_template(
                "edit.html",
                job=job
            )


        if not role:

            conn.close()

            flash(
                "Job role is required.",
                "error"
            )

            return render_template(
                "edit.html",
                job=job
            )


        if not application_date:

            conn.close()

            flash(
                "Application date is required.",
                "error"
            )

            return render_template(
                "edit.html",
                job=job
            )


        allowed_statuses = [
            "Applied",
            "Interview",
            "Rejected",
            "Selected",
            "Offer"
        ]


        if status not in allowed_statuses:

            conn.close()

            flash(
                "Please select a valid application status.",
                "error"
            )

            return render_template(
                "edit.html",
                job=job
            )


        # ==================================
        # URL VALIDATION
        # ==================================

        if job_url:

            url_pattern = r"^https?://.+"


            if not re.match(
                url_pattern,
                job_url
            ):

                conn.close()

                flash(
                    "Job URL must start with http:// or https://",
                    "error"
                )

                return render_template(
                    "edit.html",
                    job=job
                )


        # ==================================
        # UPDATE DATABASE
        # ==================================

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
            id
        ))


        conn.commit()

        conn.close()


        flash(
            "Application updated successfully!",
            "success"
        )


        return redirect("/")


    conn.close()


    return render_template(
        "edit.html",
        job=job
    )


# ==========================================
# DELETE APPLICATION
# ==========================================

@app.route("/delete/<int:id>")
def delete_application(id):

    conn = get_db()


    conn.execute("""
        DELETE FROM jobs
        WHERE id = ?
    """, (id,))


    conn.commit()

    conn.close()


    flash(
        "Application deleted successfully.",
        "success"
    )


    return redirect("/")


# ==========================================
# RUN APPLICATION
# ==========================================

if __name__ == "__main__":

    app.run(
        debug=True
    )