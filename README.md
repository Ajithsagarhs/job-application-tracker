# Job Application Tracker

A web-based Job Application Tracker built using Python, Flask, SQLite, SQL, HTML and CSS.

## Project Description

Job Application Tracker helps job seekers manage and track their job applications from one application.

Users can add, update, search, filter and delete job applications.

## Features

- Add job application
- Company name
- Job role
- Application date
- Application status
- Interview date
- Job URL
- Notes
- Search applications
- Filter by application status
- Edit applications
- Delete applications
- Dashboard with application statistics

## Technologies Used

- Python
- Flask
- SQLite
- SQL
- HTML
- CSS
- Git
- GitHub
- Render

## Application Status

The application supports the following statuses:

- Applied
- Interview
- Rejected
- Selected

## Database

SQLite is used as the database.

The main table is:

`jobs`

Columns:

- id
- company
- role
- application_date
- status
- interview_date
- job_url
- notes

SQL operations used in the project:

- CREATE TABLE
- INSERT
- SELECT
- UPDATE
- DELETE
- WHERE
- LIKE

## Project Structure

JOB_APPLICATION_TRACKER/

├── app.py

├── database.py

├── jobs.db

├── .gitignore

├── static/

└── templates/

    ├── index.html

    └── edit.html

## How to Run Locally

### 1. Clone the repository

```bash
git clone https://github.com/Ajithsagarhs/job-application-tracker.git