from flask import Flask, render_template, request, redirect, flash, jsonify, session
import sqlite3
import re
from functools import wraps
from werkzeug.security import generate_password_hash, check_password_hash


app = Flask(__name__)

app.secret_key = "jobtracker-secret-key"

DATABASE = "jobs.db"


# =========================================================
# DATABASE
# =========================================================

def get_db():

    conn = sqlite3.connect(DATABASE)

    conn.row_factory = sqlite3.Row

    return conn


def initialize_database():

    conn = get_db()

    # USERS TABLE
    conn.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL
        )
    """)

    # JOBS TABLE
    conn.execute("""
        CREATE TABLE IF NOT EXISTS jobs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            company TEXT NOT NULL,
            role TEXT NOT NULL,
            application_date TEXT NOT NULL,
            status TEXT NOT NULL,
            interview_date TEXT,
            job_url TEXT,
            notes TEXT
        )
    """)

    conn.commit()

    # -----------------------------------------------------
    # Add user_id to old jobs.db if column doesn't exist
    # -----------------------------------------------------

    columns = conn.execute("""
        PRAGMA table_info(jobs)
    """).fetchall()

    column_names = [
        column["name"]
        for column in columns
    ]

    if "user_id" not in column_names:

        conn.execute("""
            ALTER TABLE jobs
            ADD COLUMN user_id INTEGER
        """)

        conn.commit()

    # -----------------------------------------------------
    # Assign old applications to first user
    # -----------------------------------------------------

    first_user = conn.execute("""
        SELECT id
        FROM users
        ORDER BY id
        LIMIT 1
    """).fetchone()

    if first_user:

        conn.execute("""
            UPDATE jobs
            SET user_id = ?
            WHERE user_id IS NULL
        """, (
            first_user["id"],
        ))

        conn.commit()

    conn.close()


# Create tables BEFORE any route uses them
initialize_database()


# =========================================================
# LOGIN REQUIRED
# =========================================================

def login_required(route_function):

    @wraps(route_function)
    def wrapper(*args, **kwargs):

        if "user_id" not in session:

            flash(
                "Please login to continue.",
                "error"
            )

            return redirect("/login")

        return route_function(*args, **kwargs)

    return wrapper


# =========================================================
# SIGNUP
# =========================================================

@app.route("/signup", methods=["GET", "POST"])
def signup():

    if request.method == "POST":

        name = request.form.get(
            "name",
            ""
        ).strip()

        email = request.form.get(
            "email",
            ""
        ).strip().lower()

        password = request.form.get(
            "password",
            ""
        )

        confirm_password = request.form.get(
            "confirm_password",
            ""
        )

        # Required fields

        if not name or not email or not password:

            flash(
                "Please fill all required fields.",
                "error"
            )

            return redirect("/signup")

        # Password match

        if password != confirm_password:

            flash(
                "Passwords do not match.",
                "error"
            )

            return redirect("/signup")

        # Password length

        if len(password) < 6:

            flash(
                "Password must be at least 6 characters.",
                "error"
            )

            return redirect("/signup")

        conn = get_db()

        # Check existing user

        existing_user = conn.execute("""
            SELECT id
            FROM users
            WHERE email = ?
        """, (
            email,
        )).fetchone()

        if existing_user:

            conn.close()

            flash(
                "Email already registered. Please login.",
                "error"
            )

            return redirect("/login")

        # Hash password

        password_hash = generate_password_hash(
            password
        )

        # Create user

        cursor = conn.execute("""
            INSERT INTO users (
                name,
                email,
                password
            )
            VALUES (?, ?, ?)
        """, (
            name,
            email,
            password_hash
        ))

        user_id = cursor.lastrowid

        # If this is the first user,
        # assign old applications to this user

        user_count = conn.execute("""
            SELECT COUNT(*)
            FROM users
        """).fetchone()[0]

        if user_count == 1:

            conn.execute("""
                UPDATE jobs
                SET user_id = ?
                WHERE user_id IS NULL
            """, (
                user_id,
            ))

        conn.commit()

        conn.close()

        flash(
            "Account created successfully. Please login.",
            "success"
        )

        return redirect("/login")

    return render_template(
        "signup.html"
    )


# =========================================================
# LOGIN
# =========================================================

@app.route("/login", methods=["GET", "POST"])
def login():

    if request.method == "POST":

        email = request.form.get(
            "email",
            ""
        ).strip().lower()

        password = request.form.get(
            "password",
            ""
        )

        if not email or not password:

            flash(
                "Please enter email and password.",
                "error"
            )

            return redirect("/login")

        conn = get_db()

        user = conn.execute("""
            SELECT *
            FROM users
            WHERE email = ?
        """, (
            email,
        )).fetchone()

        conn.close()

        if user is None:

            flash(
                "Invalid email or password.",
                "error"
            )

            return redirect("/login")

        if not check_password_hash(
            user["password"],
            password
        ):

            flash(
                "Invalid email or password.",
                "error"
            )

            return redirect("/login")

        # Create session

        session.clear()

        session["user_id"] = user["id"]

        session["user_name"] = user["name"]

        session["user_email"] = user["email"]

        flash(
            "Login successful!",
            "success"
        )

        return redirect("/")

    return render_template(
        "login.html"
    )


# =========================================================
# LOGOUT
# =========================================================

@app.route("/logout")
def logout():

    session.clear()

    flash(
        "You have been logged out.",
        "success"
    )

    return redirect("/login")


# =========================================================
# DASHBOARD
# =========================================================

@app.route("/")
@login_required
def index():

    conn = get_db()

    user_id = session["user_id"]

    # All applications for current user

    jobs = conn.execute("""
        SELECT *
        FROM jobs
        WHERE user_id = ?
        ORDER BY id DESC
    """, (
        user_id,
    )).fetchall()

    # Total

    total = conn.execute("""
        SELECT COUNT(*)
        FROM jobs
        WHERE user_id = ?
    """, (
        user_id,
    )).fetchone()[0]

    # Applied

    applied = conn.execute("""
        SELECT COUNT(*)
        FROM jobs
        WHERE user_id = ?
        AND status = ?
    """, (
        user_id,
        "Applied"
    )).fetchone()[0]

    # Interviews

    interviews = conn.execute("""
        SELECT COUNT(*)
        FROM jobs
        WHERE user_id = ?
        AND status = ?
    """, (
        user_id,
        "Interview"
    )).fetchone()[0]

    # Rejected

    rejected = conn.execute("""
        SELECT COUNT(*)
        FROM jobs
        WHERE user_id = ?
        AND status = ?
    """, (
        user_id,
        "Rejected"
    )).fetchone()[0]

    # Selected

    selected = conn.execute("""
        SELECT COUNT(*)
        FROM jobs
        WHERE user_id = ?
        AND status = ?
    """, (
        user_id,
        "Selected"
    )).fetchone()[0]

    # Offers

    offers = conn.execute("""
        SELECT COUNT(*)
        FROM jobs
        WHERE user_id = ?
        AND status = ?
    """, (
        user_id,
        "Offer"
    )).fetchone()[0]

    # Rates

    if total > 0:

        interview_rate = round(
            (interviews / total) * 100,
            1
        )

        selection_rate = round(
            (selected / total) * 100,
            1
        )

        rejection_rate = round(
            (rejected / total) * 100,
            1
        )

    else:

        interview_rate = 0

        selection_rate = 0

        rejection_rate = 0

    conn.close()

    return render_template(
        "index.html",

        jobs=jobs,

        total=total,

        applied=applied,

        interviews=interviews,

        rejected=rejected,

        selected=selected,

        offers=offers,

        interview_rate=interview_rate,

        selection_rate=selection_rate,

        rejection_rate=rejection_rate
    )


# =========================================================
# APPLICATIONS
# =========================================================

@app.route("/applications")
@login_required
def applications():

    search = request.args.get(
        "search",
        ""
    ).strip()

    status = request.args.get(
        "status",
        ""
    ).strip()

    conn = get_db()

    query = """
        SELECT *
        FROM jobs
        WHERE user_id = ?
    """

    params = [
        session["user_id"]
    ]

    # Search

    if search:

        query += """
            AND (
                company LIKE ?
                OR role LIKE ?
            )
        """

        search_value = f"%{search}%"

        params.append(search_value)

        params.append(search_value)

    # Status

    if status:

        query += """
            AND status = ?
        """

        params.append(status)

    query += """
        ORDER BY id DESC
    """

    jobs = conn.execute(
        query,
        params
    ).fetchall()

    conn.close()

    return render_template(
        "applications.html",
        jobs=jobs
    )


# =========================================================
# PIPELINE
# =========================================================

@app.route("/pipeline")
@login_required
def pipeline():

    conn = get_db()

    user_id = session["user_id"]

    applied_jobs = conn.execute("""
        SELECT *
        FROM jobs
        WHERE user_id = ?
        AND status = ?
        ORDER BY id DESC
    """, (
        user_id,
        "Applied"
    )).fetchall()

    interview_jobs = conn.execute("""
        SELECT *
        FROM jobs
        WHERE user_id = ?
        AND status = ?
        ORDER BY id DESC
    """, (
        user_id,
        "Interview"
    )).fetchall()

    selected_jobs = conn.execute("""
        SELECT *
        FROM jobs
        WHERE user_id = ?
        AND status = ?
        ORDER BY id DESC
    """, (
        user_id,
        "Selected"
    )).fetchall()

    offer_jobs = conn.execute("""
        SELECT *
        FROM jobs
        WHERE user_id = ?
        AND status = ?
        ORDER BY id DESC
    """, (
        user_id,
        "Offer"
    )).fetchall()

    rejected_jobs = conn.execute("""
        SELECT *
        FROM jobs
        WHERE user_id = ?
        AND status = ?
        ORDER BY id DESC
    """, (
        user_id,
        "Rejected"
    )).fetchall()

    conn.close()

    return render_template(
        "pipeline.html",

        applied_jobs=applied_jobs,

        interview_jobs=interview_jobs,

        selected_jobs=selected_jobs,

        offer_jobs=offer_jobs,

        rejected_jobs=rejected_jobs
    )


# =========================================================
# DRAG & DROP STATUS UPDATE
# =========================================================

@app.route(
    "/update-status/<int:id>",
    methods=["POST"]
)
@login_required
def update_status(id):

    data = request.get_json()

    if not data:

        return jsonify({
            "success": False,
            "message": "No data received."
        }), 400

    new_status = data.get(
        "status"
    )

    allowed_statuses = [
        "Applied",
        "Interview",
        "Selected",
        "Offer",
        "Rejected"
    ]

    if new_status not in allowed_statuses:

        return jsonify({
            "success": False,
            "message": "Invalid status."
        }), 400

    conn = get_db()

    # IMPORTANT:
    # Check application belongs to current user

    job = conn.execute("""
        SELECT *
        FROM jobs
        WHERE id = ?
        AND user_id = ?
    """, (
        id,
        session["user_id"]
    )).fetchone()

    if job is None:

        conn.close()

        return jsonify({
            "success": False,
            "message": "Application not found."
        }), 404

    conn.execute("""
        UPDATE jobs
        SET status = ?
        WHERE id = ?
        AND user_id = ?
    """, (
        new_status,
        id,
        session["user_id"]
    ))

    conn.commit()

    conn.close()

    return jsonify({
        "success": True,
        "message": "Status updated successfully.",
        "status": new_status
    })


# =========================================================
# ANALYTICS
# =========================================================

@app.route("/analytics")
@login_required
def analytics():

    conn = get_db()

    user_id = session["user_id"]

    # Total

    total = conn.execute("""
        SELECT COUNT(*)
        FROM jobs
        WHERE user_id = ?
    """, (
        user_id,
    )).fetchone()[0]

    # Applied

    applied = conn.execute("""
        SELECT COUNT(*)
        FROM jobs
        WHERE user_id = ?
        AND status = ?
    """, (
        user_id,
        "Applied"
    )).fetchone()[0]

    # Interviews

    interviews = conn.execute("""
        SELECT COUNT(*)
        FROM jobs
        WHERE user_id = ?
        AND status = ?
    """, (
        user_id,
        "Interview"
    )).fetchone()[0]

    # Selected

    selected = conn.execute("""
        SELECT COUNT(*)
        FROM jobs
        WHERE user_id = ?
        AND status = ?
    """, (
        user_id,
        "Selected"
    )).fetchone()[0]

    # Offers

    offers = conn.execute("""
        SELECT COUNT(*)
        FROM jobs
        WHERE user_id = ?
        AND status = ?
    """, (
        user_id,
        "Offer"
    )).fetchone()[0]

    # Rejected

    rejected = conn.execute("""
        SELECT COUNT(*)
        FROM jobs
        WHERE user_id = ?
        AND status = ?
    """, (
        user_id,
        "Rejected"
    )).fetchone()[0]

    # Rates

    if total > 0:

        interview_rate = round(
            (interviews / total) * 100,
            1
        )

        selection_rate = round(
            (selected / total) * 100,
            1
        )

        offer_rate = round(
            (offers / total) * 100,
            1
        )

    else:

        interview_rate = 0

        selection_rate = 0

        offer_rate = 0

    # Monthly applications

    monthly_data = conn.execute("""
        SELECT
            substr(application_date, 1, 7) AS month,
            COUNT(*) AS count
        FROM jobs
        WHERE user_id = ?
        GROUP BY month
        ORDER BY month ASC
    """, (
        user_id,
    )).fetchall()

    # Top companies

    company_data = conn.execute("""
        SELECT
            company,
            COUNT(*) AS count
        FROM jobs
        WHERE user_id = ?
        GROUP BY company
        ORDER BY count DESC
        LIMIT 10
    """, (
        user_id,
    )).fetchall()

    conn.close()

    return render_template(
        "analytics.html",

        total=total,

        applied=applied,

        interviews=interviews,

        selected=selected,

        offers=offers,

        rejected=rejected,

        interview_rate=interview_rate,

        selection_rate=selection_rate,

        offer_rate=offer_rate,

        monthly_data=monthly_data,

        company_data=company_data
    )


# =========================================================
# INTERVIEWS
# =========================================================

@app.route("/interviews")
@login_required
def interviews_page():

    conn = get_db()

    interviews = conn.execute("""
        SELECT *
        FROM jobs
        WHERE user_id = ?
        AND interview_date IS NOT NULL
        AND interview_date != ''
        ORDER BY interview_date ASC
    """, (
        session["user_id"],
    )).fetchall()

    conn.close()

    return render_template(
        "interviews.html",
        interviews=interviews
    )


# =========================================================
# SETTINGS
# =========================================================

@app.route("/settings")
@login_required
def settings():

    return render_template(
        "settings.html"
    )


# =========================================================
# ADD APPLICATION
# =========================================================

@app.route(
    "/add",
    methods=["GET", "POST"]
)
@login_required
def add_application():

    if request.method == "POST":

        company = request.form.get(
            "company",
            ""
        ).strip()

        role = request.form.get(
            "role",
            ""
        ).strip()

        application_date = request.form.get(
            "date",
            ""
        ).strip()

        status = request.form.get(
            "status",
            ""
        ).strip()

        interview_date = request.form.get(
            "interview",
            ""
        ).strip()

        job_url = request.form.get(
            "url",
            ""
        ).strip()

        notes = request.form.get(
            "notes",
            ""
        ).strip()

        # Required company

        if not company:

            flash(
                "Company name is required.",
                "error"
            )

            return render_template(
                "add.html"
            )

        # Required role

        if not role:

            flash(
                "Job role is required.",
                "error"
            )

            return render_template(
                "add.html"
            )

        # Required date

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
            "Selected",
            "Offer",
            "Rejected"
        ]

        if status not in allowed_statuses:

            flash(
                "Please select a valid application status.",
                "error"
            )

            return render_template(
                "add.html"
            )

        # URL validation

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

        conn = get_db()

        conn.execute("""
            INSERT INTO jobs (
                user_id,
                company,
                role,
                application_date,
                status,
                interview_date,
                job_url,
                notes
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            session["user_id"],
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


# =========================================================
# VIEW APPLICATION
# =========================================================

@app.route("/view/<int:id>")
@login_required
def view_application(id):

    conn = get_db()

    job = conn.execute("""
        SELECT *
        FROM jobs
        WHERE id = ?
        AND user_id = ?
    """, (
        id,
        session["user_id"]
    )).fetchone()

    conn.close()

    if job is None:

        flash(
            "Application not found.",
            "error"
        )

        return redirect("/applications")

    return render_template(
        "view.html",
        job=job
    )


# =========================================================
# EDIT APPLICATION
# =========================================================

@app.route(
    "/edit/<int:id>",
    methods=["GET", "POST"]
)
@login_required
def edit_application(id):

    conn = get_db()

    # Only current user's application

    job = conn.execute("""
        SELECT *
        FROM jobs
        WHERE id = ?
        AND user_id = ?
    """, (
        id,
        session["user_id"]
    )).fetchone()

    if job is None:

        conn.close()

        flash(
            "Application not found.",
            "error"
        )

        return redirect("/applications")

    if request.method == "POST":

        company = request.form.get(
            "company",
            ""
        ).strip()

        role = request.form.get(
            "role",
            ""
        ).strip()

        application_date = request.form.get(
            "date",
            ""
        ).strip()

        status = request.form.get(
            "status",
            ""
        ).strip()

        interview_date = request.form.get(
            "interview",
            ""
        ).strip()

        job_url = request.form.get(
            "url",
            ""
        ).strip()

        notes = request.form.get(
            "notes",
            ""
        ).strip()

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
            "Selected",
            "Offer",
            "Rejected"
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
            AND user_id = ?
        """, (
            company,
            role,
            application_date,
            status,
            interview_date,
            job_url,
            notes,
            id,
            session["user_id"]
        ))

        conn.commit()

        conn.close()

        flash(
            "Application updated successfully!",
            "success"
        )

        return redirect("/applications")

    conn.close()

    return render_template(
        "edit.html",
        job=job
    )


# =========================================================
# DELETE CONFIRMATION
# =========================================================

@app.route(
    "/delete/<int:job_id>",
    methods=["GET"]
)
@login_required
def delete_confirmation(job_id):

    conn = get_db()

    job = conn.execute("""
        SELECT *
        FROM jobs
        WHERE id = ?
        AND user_id = ?
    """, (
        job_id,
        session["user_id"]
    )).fetchone()

    conn.close()

    if job is None:

        flash(
            "Application not found.",
            "error"
        )

        return redirect("/applications")

    return render_template(
        "delete.html",
        job=job
    )


# =========================================================
# DELETE APPLICATION
# =========================================================

@app.route(
    "/delete/<int:job_id>",
    methods=["POST"]
)
@login_required
def delete_application(job_id):

    conn = get_db()

    conn.execute("""
        DELETE FROM jobs
        WHERE id = ?
        AND user_id = ?
    """, (
        job_id,
        session["user_id"]
    ))

    conn.commit()

    conn.close()

    flash(
        "Application deleted successfully.",
        "success"
    )

    return redirect("/applications")


# =========================================================
# RUN APPLICATION
# =========================================================

if __name__ == "__main__":

    app.run(
        debug=True
    )