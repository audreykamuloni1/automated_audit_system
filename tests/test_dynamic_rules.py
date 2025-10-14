import pytest
import os
import sys

# Add project root to the Python path if tests are run from the root
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from db.database import (
    setup_database, get_db_connection, add_rule, get_all_rules,
    update_rule, delete_rule, get_active_rules
)
from ingestion.log_ingester import ingest_logs
from rules.rule_engine import run_rules, get_alerts

@pytest.fixture(scope="module")
def db_setup_for_rules():
    """Pytest fixture to set up a clean database with sample logs for rule tests."""
    setup_database()  # This will drop existing tables and recreate them
    ingest_logs(file_path='data/sample_logs.csv')
    yield
    # No explicit teardown needed as setup_database cleans up on each run

def test_rule_crud_operations(db_setup_for_rules):
    """Tests the full lifecycle of a rule: Create, Read, Update, Delete."""
    # 1. CREATE a new rule
    add_rule_success = add_rule(
        name="Test Rule: High-Value Transaction",
        description="Flags transactions over a certain value.",
        target_field="action",
        operator="=",
        value="high_value_tx",
        is_active=True
    )
    assert add_rule_success, "Should be able to add a new rule."

    # 2. READ all rules and verify the new rule is there
    all_rules = get_all_rules()
    # 3 default rules from schema.sql + 1 we just added
    assert len(all_rules) == 4, "There should be 4 rules in the DB."

    # Find our new rule
    new_rule = next((r for r in all_rules if r[1] == "Test Rule: High-Value Transaction"), None)
    assert new_rule is not None, "The newly added rule should be found."
    rule_id = new_rule[0]

    # 3. UPDATE the rule
    update_success = update_rule(
        rule_id=rule_id,
        name="Updated Test Rule",
        description="Updated description.",
        target_field="action",
        operator="=",
        value="high_value_tx_updated",
        is_active=False
    )
    assert update_success, "Should be able to update the rule."

    # Verify the update
    updated_rules = get_all_rules()
    updated_rule = next((r for r in updated_rules if r[0] == rule_id), None)
    assert updated_rule[1] == "Updated Test Rule", "Rule name should be updated."
    assert updated_rule[6] is False, "Rule should be inactive."

    # 4. DELETE the rule
    delete_success = delete_rule(rule_id)
    assert delete_success, "Should be able to delete the rule."

    # Verify deletion
    final_rules = get_all_rules()
    assert len(final_rules) == 3, "There should be 3 rules left after deletion."
    assert all(r[0] != rule_id for r in final_rules), "The deleted rule should be gone."

def test_dynamic_rule_engine_execution(db_setup_for_rules):
    """Tests that the dynamic rule engine generates alerts based on active DB rules."""
    # The db is already set up with 3 default rules.
    # Let's clean alerts table before running the engine.
    conn = get_db_connection()
    with conn.cursor() as cur:
        cur.execute("DELETE FROM alerts")
    conn.commit()
    conn.close()

    # Run the dynamic rule engine
    run_rules()

    # Fetch the alerts
    alerts = get_alerts()

    # Based on sample_logs.csv and the 3 default rules:
    # - 'Unauthorized Access Attempt' should find 2 logs.
    # - 'Admin Action on Sensitive DB' should find 3 logs (admin-01 actions).
    # - 'Multiple Failed Logins' should find 3 logs.
    # Total expected alerts = 2 + 3 + 3 = 8
    assert len(alerts) == 8, "The dynamic rule engine should generate 8 alerts based on the 3 default rules."

    # Verify that different rules were triggered
    triggered_rule_names = {alert[2] for alert in alerts} # rule_name is at index 2
    expected_rules = {
        "Unauthorized Access Attempt",
        "Admin Action on Sensitive DB",
        "Multiple Failed Logins"
    }
    assert triggered_rule_names == expected_rules, "All three default rules should have been triggered."