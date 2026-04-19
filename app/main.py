"""
main.py
-------
The FastAPI application. Run it with:
    uvicorn app.main:app --reload

Routes fall into three groups:
  1. Web pages     -> serve the HTML files in /templates
  2. API endpoints -> JSON in / JSON out, under /api/...
  3. Reports       -> sales / occupancy reports for managers
"""

from fastapi import FastAPI, Depends, HTTPException, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from datetime import datetime, timedelta, date

from .database import get_db
from .models import MovieIn, ScreeningIn, TicketIn

app = FastAPI(title="Silver Screen Palace")

# Serve /static (css, js) and /templates (html)
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")


# ============================================================
# PAGES  (just render HTML - the JS on each page calls the API)
# ============================================================
@app.get("/", response_class=HTMLResponse)
def home(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.get("/movies", response_class=HTMLResponse)
def movies_page(request: Request):
    return templates.TemplateResponse("movies.html", {"request": request})

@app.get("/screenings", response_class=HTMLResponse)
def screenings_page(request: Request):
    return templates.TemplateResponse("screenings.html", {"request": request})

@app.get("/tickets", response_class=HTMLResponse)
def tickets_page(request: Request):
    return templates.TemplateResponse("tickets.html", {"request": request})

@app.get("/reports", response_class=HTMLResponse)
def reports_page(request: Request):
    return templates.TemplateResponse("reports.html", {"request": request})


# ============================================================
# MOVIES
# ============================================================
@app.get("/api/movies")
def list_movies(db=Depends(get_db)):
    conn, cur = db
    cur.execute("SELECT * FROM MOVIE ORDER BY MOVIE_TITLE")
    return cur.fetchall()

@app.post("/api/movies", status_code=201)
def create_movie(movie: MovieIn, db=Depends(get_db)):
    conn, cur = db
    cur.execute(
        "INSERT INTO MOVIE (MOVIE_TITLE, MOVIE_RATING, MOVIE_RUNTIME) "
        "VALUES (%s, %s, %s)",
        (movie.title, movie.rating, movie.runtime),
    )
    conn.commit()
    return {"movie_id": cur.lastrowid, **movie.model_dump()}


# ============================================================
# THEATERS & EMPLOYEES (small helpers used by dropdowns)
# ============================================================
@app.get("/api/theaters")
def list_theaters(db=Depends(get_db)):
    conn, cur = db
    cur.execute("SELECT * FROM THEATER ORDER BY THEATER_ID")
    return cur.fetchall()

@app.get("/api/employees")
def list_employees(db=Depends(get_db)):
    """Returns every employee with their role (manager/cashier/usher)."""
    conn, cur = db
    cur.execute("""
        SELECT e.EMPLOYEE_ID, e.EMPLOYEE_NAME, e.EMPLOYEE_HIRE_DATE,
               CASE
                 WHEN m.EMPLOYEE_ID IS NOT NULL THEN 'MANAGER'
                 WHEN c.EMPLOYEE_ID IS NOT NULL THEN 'CASHIER'
                 WHEN u.EMPLOYEE_ID IS NOT NULL THEN 'USHER'
                 ELSE 'STAFF'
               END AS ROLE
        FROM EMPLOYEE e
        LEFT JOIN MANAGER m ON m.EMPLOYEE_ID = e.EMPLOYEE_ID
        LEFT JOIN CASHIER c ON c.EMPLOYEE_ID = e.EMPLOYEE_ID
        LEFT JOIN USHER   u ON u.EMPLOYEE_ID = e.EMPLOYEE_ID
        ORDER BY e.EMPLOYEE_NAME
    """)
    return cur.fetchall()


# ============================================================
# SCREENINGS
# ============================================================
@app.get("/api/screenings")
def list_screenings(movie_id: int | None = None,
                    on_date: date | None = None,
                    db=Depends(get_db)):
    """
    Functional req: "Movie Screenings (Read)" and "All Screenings (Read)".
    Optional filters: ?movie_id=1  or  ?on_date=2026-04-20
    """
    conn, cur = db
    sql = """
        SELECT s.SCREENING_ID, s.SCREENING_DATE, s.SCREENING_START_TIME,
               m.MOVIE_ID, m.MOVIE_TITLE, m.MOVIE_RATING, m.MOVIE_RUNTIME,
               t.THEATER_ID, t.THEATER_CAPACITY,
               (t.THEATER_CAPACITY
                - COALESCE((SELECT COUNT(*) FROM TICKET
                            WHERE SCREENING_ID = s.SCREENING_ID
                              AND TICKET_STATUS = 'ACTIVE'), 0)) AS SEATS_AVAILABLE
        FROM SCREENING s
        JOIN MOVIE   m ON m.MOVIE_ID   = s.MOVIE_ID
        JOIN THEATER t ON t.THEATER_ID = s.THEATER_ID
        WHERE 1=1
    """
    params = []
    if movie_id is not None:
        sql += " AND s.MOVIE_ID = %s"
        params.append(movie_id)
    if on_date is not None:
        sql += " AND s.SCREENING_DATE = %s"
        params.append(on_date)
    sql += " ORDER BY s.SCREENING_DATE, s.SCREENING_START_TIME"
    cur.execute(sql, params)
    return cur.fetchall()


@app.post("/api/screenings", status_code=201)
def create_screening(s: ScreeningIn, db=Depends(get_db)):
    """
    Scheduling Constraint: a theater room can't host two screenings
    that overlap in time (start_time + runtime).
    """
    conn, cur = db

    # Look up the movie's runtime so we can compute the end time
    cur.execute("SELECT MOVIE_RUNTIME FROM MOVIE WHERE MOVIE_ID = %s",
                (s.movie_id,))
    row = cur.fetchone()
    if not row:
        raise HTTPException(404, "Movie not found")
    runtime_min = row["MOVIE_RUNTIME"]

    new_start = datetime.combine(s.date, s.start_time)
    new_end   = new_start + timedelta(minutes=runtime_min)

    # Check every existing screening in the same theater on the same day
    cur.execute("""
        SELECT s.SCREENING_START_TIME, m.MOVIE_RUNTIME
        FROM SCREENING s
        JOIN MOVIE m ON m.MOVIE_ID = s.MOVIE_ID
        WHERE s.THEATER_ID = %s AND s.SCREENING_DATE = %s
    """, (s.theater_id, s.date))

    for existing in cur.fetchall():
        # existing start/end
        ex_start_time = existing["SCREENING_START_TIME"]
        # MySQL TIME comes back as a timedelta - convert it
        if isinstance(ex_start_time, timedelta):
            ex_start_time = (datetime.min + ex_start_time).time()
        ex_start = datetime.combine(s.date, ex_start_time)
        ex_end   = ex_start + timedelta(minutes=existing["MOVIE_RUNTIME"])
        # Overlap test: A starts before B ends AND B starts before A ends
        if new_start < ex_end and ex_start < new_end:
            raise HTTPException(
                409,
                f"Time conflict: theater already has a screening from "
                f"{ex_start.time()} to {ex_end.time()}"
            )

    cur.execute(
        "INSERT INTO SCREENING (SCREENING_DATE, SCREENING_START_TIME, "
        "MOVIE_ID, THEATER_ID) VALUES (%s, %s, %s, %s)",
        (s.date, s.start_time, s.movie_id, s.theater_id),
    )
    conn.commit()
    return {"screening_id": cur.lastrowid}


# ============================================================
# TICKETS
# ============================================================
@app.get("/api/tickets")
def list_tickets(db=Depends(get_db)):
    conn, cur = db
    cur.execute("""
        SELECT t.TICKET_ID, t.TICKET_TYPE, t.TICKET_SALEPRICE, t.TICKET_STATUS,
               m.MOVIE_TITLE, s.SCREENING_DATE, s.SCREENING_START_TIME,
               e.EMPLOYEE_NAME AS SOLD_BY
        FROM TICKET t
        JOIN SCREENING s ON s.SCREENING_ID = t.SCREENING_ID
        JOIN MOVIE     m ON m.MOVIE_ID     = s.MOVIE_ID
        JOIN EMPLOYEE  e ON e.EMPLOYEE_ID  = t.EMPLOYEE_ID
        ORDER BY t.TICKET_ID DESC
    """)
    return cur.fetchall()


@app.post("/api/tickets", status_code=201)
def sell_ticket(ticket: TicketIn, db=Depends(get_db)):
    """
    Enforces two constraints from the doc:
      - Capacity Constraint: active tickets <= theater capacity
      - Age Verification:    R-rated requires age >= 17
    """
    conn, cur = db

    # Pull the screening + movie + theater info we need
    cur.execute("""
        SELECT s.SCREENING_ID, m.MOVIE_RATING, t.THEATER_CAPACITY,
               (SELECT COUNT(*) FROM TICKET
                WHERE SCREENING_ID = s.SCREENING_ID
                  AND TICKET_STATUS = 'ACTIVE') AS ACTIVE_TICKETS
        FROM SCREENING s
        JOIN MOVIE   m ON m.MOVIE_ID   = s.MOVIE_ID
        JOIN THEATER t ON t.THEATER_ID = s.THEATER_ID
        WHERE s.SCREENING_ID = %s
    """, (ticket.screening_id,))
    info = cur.fetchone()
    if not info:
        raise HTTPException(404, "Screening not found")

    # Age check
    if info["MOVIE_RATING"] == "R":
        if ticket.customer_age is None or ticket.customer_age < 17:
            raise HTTPException(
                400,
                "R-rated movie: customer must be 17 or older (age required)."
            )

    # Capacity check
    if info["ACTIVE_TICKETS"] >= info["THEATER_CAPACITY"]:
        raise HTTPException(409, "Screening is sold out.")

    cur.execute(
        "INSERT INTO TICKET (TICKET_TYPE, TICKET_SALEPRICE, TICKET_STATUS, "
        "SCREENING_ID, EMPLOYEE_ID) VALUES (%s, %s, 'ACTIVE', %s, %s)",
        (ticket.ticket_type, ticket.sale_price,
         ticket.screening_id, ticket.employee_id),
    )
    conn.commit()
    return {"ticket_id": cur.lastrowid}


@app.post("/api/tickets/{ticket_id}/cancel")
def cancel_ticket(ticket_id: int, db=Depends(get_db)):
    """
    Soft delete: set status to CANCELLED (preserves the sales log).
    """
    conn, cur = db
    cur.execute("SELECT TICKET_STATUS FROM TICKET WHERE TICKET_ID = %s",
                (ticket_id,))
    row = cur.fetchone()
    if not row:
        raise HTTPException(404, "Ticket not found")
    if row["TICKET_STATUS"] == "CANCELLED":
        raise HTTPException(400, "Ticket already cancelled")

    cur.execute("UPDATE TICKET SET TICKET_STATUS='CANCELLED' WHERE TICKET_ID=%s",
                (ticket_id,))
    conn.commit()
    return {"ticket_id": ticket_id, "status": "CANCELLED"}


# ============================================================
# REPORTS  (for managers)
# ============================================================
@app.get("/api/reports/sales-by-movie")
def sales_by_movie(db=Depends(get_db)):
    conn, cur = db
    cur.execute("""
        SELECT m.MOVIE_TITLE,
               COUNT(CASE WHEN t.TICKET_STATUS='ACTIVE'    THEN 1 END) AS TICKETS_SOLD,
               COUNT(CASE WHEN t.TICKET_STATUS='CANCELLED' THEN 1 END) AS TICKETS_CANCELLED,
               COALESCE(SUM(CASE WHEN t.TICKET_STATUS='ACTIVE'
                                 THEN t.TICKET_SALEPRICE END), 0) AS REVENUE
        FROM MOVIE m
        LEFT JOIN SCREENING s ON s.MOVIE_ID = m.MOVIE_ID
        LEFT JOIN TICKET    t ON t.SCREENING_ID = s.SCREENING_ID
        GROUP BY m.MOVIE_ID, m.MOVIE_TITLE
        ORDER BY REVENUE DESC
    """)
    return cur.fetchall()


@app.get("/api/reports/occupancy")
def occupancy(db=Depends(get_db)):
    conn, cur = db
    cur.execute("""
        SELECT s.SCREENING_ID, m.MOVIE_TITLE,
               s.SCREENING_DATE, s.SCREENING_START_TIME,
               t.THEATER_CAPACITY,
               COUNT(CASE WHEN tk.TICKET_STATUS='ACTIVE' THEN 1 END) AS SEATS_SOLD,
               ROUND(100 *
                 COUNT(CASE WHEN tk.TICKET_STATUS='ACTIVE' THEN 1 END)
                 / t.THEATER_CAPACITY, 1) AS OCCUPANCY_PCT
        FROM SCREENING s
        JOIN MOVIE   m  ON m.MOVIE_ID   = s.MOVIE_ID
        JOIN THEATER t  ON t.THEATER_ID = s.THEATER_ID
        LEFT JOIN TICKET tk ON tk.SCREENING_ID = s.SCREENING_ID
        GROUP BY s.SCREENING_ID
        ORDER BY s.SCREENING_DATE, s.SCREENING_START_TIME
    """)
    return cur.fetchall()
