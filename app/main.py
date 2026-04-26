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
import asyncio
from fastapi import FastAPI, Depends, HTTPException, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from datetime import datetime, timedelta, date

from .database import get_db
from .models import MovieIn, ScreeningIn, TicketIn
from . import tmdb

app = FastAPI(title="Silver Screen Palace")
@app.on_event("startup")
async def backfill_movie_posters():
    """
    On app startup, find any movies missing posters/descriptions and
    auto-fetch them from TMDB. Means seed movies get posters automatically
    without us hardcoding URLs in the SQL.
    """
    from .database import connection_pool
    conn = connection_pool.get_connection()
    cur = conn.cursor(dictionary=True)
    try:
        cur.execute("""
            SELECT MOVIE_ID, MOVIE_TITLE FROM MOVIE
            WHERE MOVIE_POSTER IS NULL OR MOVIE_DESCRIPTION IS NULL
        """)
        missing = cur.fetchall()
        if not missing:
            return
        print(f"[startup] Fetching TMDB data for {len(missing)} movies...")
        for m in missing:
            try:
                details = await tmdb.lookup_by_title(m["MOVIE_TITLE"])
                if details:
                    cur.execute(
                        "UPDATE MOVIE SET MOVIE_POSTER=%s, MOVIE_DESCRIPTION=%s "
                        "WHERE MOVIE_ID=%s",
                        (details["poster"], details["description"], m["MOVIE_ID"])
                    )
                    print(f"[startup]   ✓ {m['MOVIE_TITLE']}")
            except Exception as e:
                print(f"[startup]   ✗ {m['MOVIE_TITLE']}: {e}")
        conn.commit()
    finally:
        cur.close()
        conn.close()

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
    cur.execute("SELECT * FROM MOVIE ORDER BY MOVIE_ACTIVE DESC, MOVIE_TITLE")
    return cur.fetchall()

@app.get("/api/movies/active")
def list_active_movies(db=Depends(get_db)):
    conn, cur = db
    cur.execute("SELECT * FROM MOVIE WHERE MOVIE_ACTIVE = 1 ORDER BY MOVIE_ACTIVE DESC, MOVIE_TITLE")
    return cur.fetchall()

@app.get("/api/movies/{movie_id}")
def get_movie(movie_id: int, db=Depends(get_db)):
    conn, cur = db
    cur.execute("SELECT * FROM MOVIE WHERE MOVIE_ID = %s", (movie_id,))
    return cur.fetchone()

@app.post("/api/movies", status_code=201)
def create_movie(movie: MovieIn, db=Depends(get_db)):
    conn, cur = db
    cur.execute(
        "INSERT INTO MOVIE (MOVIE_TITLE, MOVIE_RATING, MOVIE_RUNTIME, "
        "MOVIE_POSTER, MOVIE_DESCRIPTION) VALUES (%s, %s, %s, %s, %s)",
        (movie.title, movie.rating, movie.runtime,
         movie.poster, movie.description),
    )
    conn.commit()
    return {"movie_id": cur.lastrowid, **movie.model_dump()}

@app.put("/api/movies/{movie_id}/active")
def update_movie_active(movie_id: int, active: bool, db=Depends(get_db)):
    """
    Toggle whether a movie is active in the catalog.
    Soft delete pattern - preserves screenings/tickets for FK integrity.
    Call as: PUT /api/movies/5/active?active=true
    """
    conn, cur = db
    cur.execute("SELECT MOVIE_ACTIVE FROM MOVIE WHERE MOVIE_ID = %s", (movie_id,))
    row = cur.fetchone()
    if not row:
        raise HTTPException(404, "Movie not found")
    if bool(row["MOVIE_ACTIVE"]) != active:
        cur.execute("UPDATE MOVIE SET MOVIE_ACTIVE = %s WHERE MOVIE_ID = %s",
                    (int(active), movie_id))
        conn.commit()
    return {"movie_id": movie_id, "movie_active": active}
    


# ============================================================
# TMDB (The Movie Database) - auto-fill movie info
# ============================================================
@app.get("/api/tmdb/search")
async def tmdb_search(q: str):
    """Search TMDB by title. Returns 6 matches with posters for the user
    to pick from."""
    if not q or len(q.strip()) < 2:
        raise HTTPException(400, "Search query must be at least 2 characters")
    return await tmdb.search_movies(q.strip())


@app.get("/api/tmdb/details/{tmdb_id}")
async def tmdb_details(tmdb_id: int):
    """Given a TMDB movie ID, return the full info (runtime, rating,
    poster, description) so the Add Movie form can auto-fill."""
    return await tmdb.get_movie_details(tmdb_id)


@app.get("/api/tmdb/lookup")
async def tmdb_lookup(title: str):
    """Auto-lookup: given just a title, return best-match full details.
    Used as the fallback when the user types a title and clicks Add
    without picking from search results."""
    if not title or len(title.strip()) < 2:
        raise HTTPException(400, "Title must be at least 2 characters")
    result = await tmdb.lookup_by_title(title.strip())
    if not result:
        raise HTTPException(404, f"No match found for '{title}'")
    return result


# ============================================================
# THEATERS & EMPLOYEES (small helpers used by dropdowns)
# ============================================================
@app.get("/api/theaters")
def list_theaters(db=Depends(get_db)):
    conn, cur = db
    cur.execute("SELECT * FROM THEATER ORDER BY THEATER_ID")
    return cur.fetchall()

@app.put("/api/theaters/{theater_id}")
def update_theater(theater_id: int, capacity: int, db=Depends(get_db)):
    """
    Update a theater's seating capacity.
    Used by managers to adjust theater configuration.
    """
    conn, cur = db
    if capacity < 1:
        raise HTTPException(400, "Capacity must be at least 1")

    cur.execute("SELECT THEATER_ID FROM THEATER WHERE THEATER_ID = %s",
                (theater_id,))
    if not cur.fetchone():
        raise HTTPException(404, "Theater not found")

    cur.execute("UPDATE THEATER SET THEATER_CAPACITY = %s WHERE THEATER_ID = %s",
                (capacity, theater_id))
    conn.commit()
    return {"theater_id": theater_id, "theater_capacity": capacity}

@app.get("/api/employees")
def list_employees(db=Depends(get_db)):
    """Returns every employee with their role (manager/cashier)."""
    conn, cur = db
    cur.execute("""
        SELECT EMPLOYEE_ID, EMPLOYEE_NAME, EMPLOYEE_HIRE_DATE,
               EMPLOYEE_ROLE AS ROLE
        FROM EMPLOYEE
        ORDER BY EMPLOYEE_NAME
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
               m.MOVIE_POSTER, m.MOVIE_DESCRIPTION,
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
    # Look up the movie's runtime + active status
    cur.execute("SELECT MOVIE_RUNTIME, MOVIE_ACTIVE FROM MOVIE WHERE MOVIE_ID = %s",
                (s.movie_id,))
    row = cur.fetchone()
    if not row:
        raise HTTPException(404, "Movie not found")
    if not bool(row["MOVIE_ACTIVE"]):
        raise HTTPException(400, "Movie is not active in catalog")
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
