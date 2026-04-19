"""
database.py
-----------
This is the bridge between FastAPI and MySQL.

Connection settings are read from environment variables (see .env file).
Using a connection pool means we don't open/close a new connection
for every web request - we reuse a pool of them.
"""

import os
from mysql.connector import pooling
from dotenv import load_dotenv

# Load values from the .env file (DB_HOST, DB_USER, etc.)
load_dotenv()

db_config = {
    "host":     os.getenv("DB_HOST", "localhost"),
    "port":     int(os.getenv("DB_PORT", 3306)),
    "user":     os.getenv("DB_USER", "root"),
    "password": os.getenv("DB_PASSWORD", ""),
    "database": os.getenv("DB_NAME", "silver_screen"),
}

# Create a pool of 5 reusable connections
connection_pool = pooling.MySQLConnectionPool(
    pool_name="silver_screen_pool",
    pool_size=5,
    **db_config,
)


def get_db():
    """
    FastAPI dependency.
    Gives each request its own connection + dict cursor,
    then closes them when the request is done.

    Usage in a route:
        def my_route(db = Depends(get_db)):
            conn, cursor = db
            cursor.execute("SELECT ...")
    """
    conn = connection_pool.get_connection()
    cursor = conn.cursor(dictionary=True)   # results come back as dicts
    try:
        yield (conn, cursor)
    finally:
        cursor.close()
        conn.close()
