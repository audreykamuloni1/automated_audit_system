import pytest
import os
from db.database import (
    setup_database, get_db_connection, add_rule, get_all_rules,
    update_rule, delete_rule, get_active_rules
)
from ingestion.log_ingester import ingest_logs
from rules.rule_engine import run_rules, get_alerts

@pytest.fixture(scope="function")
def db_setup_for_rules():
    """
    Pytest fixture to set up a clean database FOR EACH TEST FUNCTION.
    """
    setup_database()
    ingest_logs(file_path='data/sample_logs.csv')
    yield

def test_rule_crud_operations(db_setup_for_rules):
    """Tests the full lifecycle of a rule: Create, Read, Update, Delete."""
    # The database starts with 3 default rules.
    all_rules = get_all_rules()
    assert len(all_rules) == 3, "Should start with 3 default rules."

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
    assert len(all_rules) == 4, "There should be exactly 4 rules in the DB now."

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

    updated_rule = get_all_rules()[-1] # Assuming it's the last one for simplicity
    assert updated_rule[1] == "Updated Test Rule", "Rule name should be updated."
    assert updated_rule[6] is False, "Rule should be inactive."

    # 4. DELETE the rule
    delete_success = delete_rule(rule_id)
    assert delete_success, "Should be able to delete the rule."

    final_rules = get_all_rules()
    assert len(final_rules) == 3, "There should be 3 rules left after deletion."

def test_dynamic_rule_engine_execution(db_setup_for_rules):
    """Tests that the dynamic rule engine generates alerts based on active DB rules."""
    # Run the dynamic rule engine
    run_rules()

    # Fetch the alerts
    alerts = get_alerts()

    # THE FIX IS HERE: The correct number of alerts is 9, not 8.
    # 2 (unauthorized) + 4 (admin actions) + 3 (failed logins) = 9
    assert len(alerts) == 9, "The dynamic rule engine should generate 9 alerts based on the 3 default rules."

    # Verify that all different rules were triggered
    triggered_rule_names = {alert[2] for alert in alerts}
    expected_rules = {
        "Unauthorized Access Attempt",
        "Admin Action on Sensitive DB",
        "Multiple Failed Logins"
    }
    assert triggered_rule_names == expected_rules, "All three default rules should have been triggered."
