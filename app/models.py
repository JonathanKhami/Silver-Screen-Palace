"""
models.py
---------
Pydantic schemas describe what data the API accepts (request bodies)
and what it returns (responses). FastAPI uses these to auto-validate
input and generate docs.
"""

from pydantic import BaseModel, Field
from datetime import date, time, datetime
from decimal import Decimal
from typing import Optional


# ----- Movie -----
class MovieIn(BaseModel):
    title:   str
    rating:  str = Field(pattern="^(G|PG|PG-13|R|NC-17)$")
    runtime: int = Field(gt=0)


# ----- Screening -----
class ScreeningIn(BaseModel):
    movie_id:    int
    theater_id:  int
    date:        date
    start_time:  time


# ----- Ticket -----
class TicketIn(BaseModel):
    screening_id: int
    employee_id:  int           # the cashier selling it
    ticket_type:  str = Field(pattern="^(ADULT|CHILD|SENIOR)$")
    sale_price:   Decimal
    customer_age: Optional[int] = None   # required for R-rated screenings
