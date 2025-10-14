import pytest
from db.database import setup_database, get_db_connection
from ingestion.log_ingester import ingest_logs
from rules.rule_engine import run_rules, get_alerts

@pytest.fixture(scope="module")
def db_setup():
    """Pytest fixture to set up a clean database for tests."""
    # Run setup once for the entire test module
    setup_database()
    # Ingest test data
    ingest_logs(file_path='data/sample_logs.csv')
    yield
    # Teardown: clean up the database if necessary, but for now we'll just re-run setup_database
    # which drops tables first.

def test_run_rules_generates_alerts(db_setup):
    """Tests that the rule engine correctly identifies violations and creates alerts."""
    # Clear any existing alerts before running the test
    conn = get_db_connection()
    with conn.cursor() as cur:
        cur.execute("DELETE FROM alerts")
    conn.commit()
    conn.close()

    # Run the rule engine
    run_rules()

    # Fetch alerts and verify
    alerts = get_alerts()

    # Based on sample_logs.csv, there are two 'unauthorized' entries
    assert len(alerts) == 2, "There should be exactly two alerts for unauthorized access"

    # Check that the rule ID is correct
    for alert in alerts:
        # alert format: (id, timestamp, rule_id, description, user_id, action, resource)
        assert alert[2] == "unauthorized_access_attempt", "The rule_id should be correct"
        assert "unauthorized" in alert[3].lower(), "The description should mention unauthorized access"

def test_get_alerts_retrieves_data(db_setup):
    """Tests that get_alerts returns data in the correct format."""
    # Ensure rules have run at least once
    run_rules()

    alerts = get_alerts()
    assert isinstance(alerts, list), "get_alerts should return a list"

    if alerts:
        # Check the structure of the first alert
        first_alert = alerts[0]
        assert len(first_alert) == 7, "Each alert should have 7 fields"
        assert isinstance(first_alert[0], int), "Alert ID should be an integer"
        assert isinstance(first_alert[3], str), "Description should be a string"