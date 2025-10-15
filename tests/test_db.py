import pytest
from db.database import get_db_connection, setup_database

def test_db_connection():
    """Tests that a connection to the database can be established."""
    conn = get_db_connection()
    assert conn is not None, "Database connection should not be None"
    try:
        cur = conn.cursor()
        cur.execute("SELECT 1")
        result = cur.fetchone()
        assert result[0] == 1, "Database connection should be able to execute a simple query"
    finally:
        if conn:
            conn.close()

def test_setup_database():
    """Tests that the database setup runs without errors and creates tables."""
    # This is a basic test. A more robust test would inspect the schema.
    try:
        setup_database()
    except Exception as e:
        pytest.fail(f"Database setup failed with an exception: {e}")
    
    # Verify that tables were created
    conn = get_db_connection()
    assert conn is not None
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT to_regclass('public.logs');")
            assert cur.fetchone()[0] == 'logs', "The 'logs' table should exist after setup"
            cur.execute("SELECT to_regclass('public.alerts');")
            assert cur.fetchone()[0] == 'alerts', "The 'alerts' table should exist after setup"
    finally:
        if conn:
            conn.close()