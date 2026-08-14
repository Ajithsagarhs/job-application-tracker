import sqlite3


DATABASE = "jobs.db"


def create_database():

    conn = sqlite3.connect(DATABASE)

    cursor = conn.cursor()


    cursor.execute("""
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


    conn.commit()

    conn.close()


    print("Database and jobs table created successfully!")


if __name__ == "__main__":

    create_database()