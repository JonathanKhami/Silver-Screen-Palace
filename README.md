# Silver Screen Palace

CSI 3450 Database Design Project — Winter 2026
Movie theater management system (FastAPI + MySQL)

## Project Structure
```
silver_screen/
├── app/
│   ├── __init__.py
│   ├── database.py      <- MySQL connection (the key "how do I connect?" file)
│   ├── main.py          <- FastAPI routes
│   └── models.py        <- Pydantic request schemas
├── sql/
│   ├── 01_schema.sql    <- Creates database + 8 tables
│   └── 02_seed.sql      <- Sample data
├── static/              <- CSS + JS
│   ├── app.js           <- Web utilities and REST API convenience functions
│   └── style.css        <- Styling used throughout the website
├── templates/           <- HTML pages (Jinja2)
│   ├── base.html        <- The base HTML file that other templates build from
│   ├── index.html       <- Homepage, promotes featured films and upcoming screenings
│   ├── movies.html      <- Add/remove movies to/from the catalog
│   ├── reports.html     <- Theater sales reports
│   ├── screenings.html  <- Schedule new screenings, list existing ones
│   └── tickets.html     <- Record ticket sales, cancel existing tickets
├── .env.example         <- Copy to .env and fill in your password
└── requirements.txt
```

## Setup

### 1. Install MySQL
Download MySQL Community Server + MySQL Workbench from
https://dev.mysql.com/downloads/. During install, set a root password and
remember it.

### 2. Create the database
Open MySQL Workbench, connect to your local server, then File > Open SQL Script
and run:
1. `sql/01_schema.sql` (creates the database and tables)
2. `sql/02_seed.sql` (fills in sample data)

### 3. Install Python dependencies
```
cd silver_screen
python -m venv venv
# Windows:
venv\Scripts\activate
# Mac/Linux:
source venv/bin/activate

pip install -r requirements.txt
```

### 4. Configure the connection
```
# Windows:
copy .env.example .env
# Mac/Linux:
cp .env.example .env
```
Open `.env` and set `DB_PASSWORD` to your MySQL root password.

### 5. Run the app
```
uvicorn app.main:app --reload
```
Open http://localhost:8000

API docs are auto-generated at http://localhost:8000/docs

## Features mapped to project requirements

| Requirement                      | Where it lives                                   |
|----------------------------------|--------------------------------------------------|
| Movie Management (Create/Update) | `POST /api/movies`, `/movies` page               |
| Screening Scheduling             | `POST /api/screenings`, `/screenings` page       |
| Sales Logging                    | `POST /api/tickets`, `/tickets` page             |
| Movie/All Screenings (Read)      | `GET /api/screenings?movie_id=` or `?on_date=`   |
| Sales Report                     | `GET /api/reports/sales-by-movie`, `/reports`    |
| Ticket Cancellation (soft delete)| `POST /api/tickets/{id}/cancel`                  |
| Capacity Constraint              | Checked in `sell_ticket()` in `main.py`          |
| Age Verification (R-rated)       | Checked in `sell_ticket()` in `main.py`          |
| Scheduling Constraint (overlap)  | Checked in `create_screening()` in `main.py`    |
| Soft Delete Audit Trail          | `TICKET_STATUS` column, never DELETE rows        |
| Entity Integrity                 | Every table has `AUTO_INCREMENT PRIMARY KEY`     |
