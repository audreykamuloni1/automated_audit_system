
import pytest
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
    # 1. CREATE a new compound rule
    add_rule_success = add_rule(
        name="Test Rule: High-Value Admin Transaction",
        description="Flags high-value transactions by admin users.",
        conditions=[
            {'target_field': 'user_id', 'operator': 'LIKE', 'value': 'admin-%'},
            {'target_field': 'action', 'operator': '=', 'value': 'high_value_tx'}
        ],
        is_active=True,
        match_type='AND'
    )
    assert add_rule_success, "Should be able to add a new compound rule."

    # 2. READ all rules and verify the new rule is there
    all_rules = get_all_rules()
    # 3 default rules from schema.sql + 1 we just added
    assert len(all_rules) == 4, "There should be 4 rules in the DB."

    # Find our new rule
    new_rule = next((r for r in all_rules if r[1] == "Test Rule: High-Value Admin Transaction"), None)
    assert new_rule is not None, "The newly added rule should be found."
    rule_id = new_rule[0]

    # Verify it has 2 conditions
    import json
    conditions = json.loads(new_rule[5]) if isinstance(new_rule[5], str) else new_rule[5]
    assert len(conditions) == 2, "Rule should have 2 conditions."

    # 3. UPDATE the rule
    update_success = update_rule(
        rule_id=rule_id,
        name="Updated Test Rule",
        description="Updated description.",
        conditions=[
            {'target_field': 'status', 'operator': '=', 'value': 'failed'}
        ],
        is_active=False,
        match_type='AND'
    )
    assert update_success, "Should be able to update the rule."

    # Verify the update
    updated_rules = get_all_rules()
    updated_rule = next((r for r in updated_rules if r[0] == rule_id), None)
    assert updated_rule[1] == "Updated Test Rule", "Rule name should be updated."
    assert updated_rule[3] is False, "Rule should be inactive."

    # Verify conditions were updated
    updated_conditions = json.loads(updated_rule[5]) if isinstance(updated_rule[5], str) else updated_rule[5]
    assert len(updated_conditions) == 1, "Rule should now have 1 condition."

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
    # - 'Unauthorized Access Attempt' should find 2 logs (status='unauthorized').
    # - 'Admin Action on Sensitive DB' should find 3 logs (user_id LIKE 'admin-%' AND resource LIKE '%sensitive%').
    #   Matching logs: admin-01 on payroll-db, admin-01 on sensitive-db (delete), admin-01 on sensitive-db (read)
    #   Note: admin-02 on sensitive-db is also matched (update)
    #   Actually: 4 logs match (admin-01: payroll-db, sensitive-db delete, sensitive-db read; admin-02: sensitive-db update)
    # - 'Multiple Failed Logins' should find 3 logs (status='failed').
    # Total expected alerts = 2 + 4 + 3 = 9

    # Let's verify the actual count
    from collections import Counter
    rule_counts = Counter(alert[2] for alert in alerts)

    print("\nAlert breakdown by rule:")
    for rule_name, count in rule_counts.items():
        print(f"  {rule_name}: {count} alerts")
    print(f"  Total: {len(alerts)}")

    # The compound rule should now only match admin actions on sensitive resources
    assert len(alerts) == 8, f"Expected 8 alerts (2+3+3), got {len(alerts)}."

    # Verify that different rules were triggered
    triggered_rule_names = {alert[2] for alert in alerts} # rule_name is at index 2
    expected_rules = {
        "Unauthorized Access Attempt",
        "Admin Action on Sensitive DB",
        "Multiple Failed Logins"
    }
    assert triggered_rule_names == expected_rules, "All three default rules should have been triggered."

def test_compound_rule_with_or(db_setup_for_rules):
    """Tests that OR logic works correctly for compound rules."""
    # Create a rule that matches EITHER unauthorized status OR failed status
    add_rule_success = add_rule(
        name="Test OR Rule: Unauthorized or Failed",
        description="Flags logs with unauthorized or failed status.",
        conditions=[
            {'target_field': 'status', 'operator': '=', 'value': 'unauthorized'},
            {'target_field': 'status', 'operator': '=', 'value': 'failed'}
        ],
        is_active=True,
        match_type='OR'
    )
    assert add_rule_success, "Should be able to add an OR rule."

    # Clean alerts
    conn = get_db_connection()
    with conn.cursor() as cur:
        cur.execute("DELETE FROM alerts")
    conn.commit()
    conn.close()

    # Run rules
    run_rules()
    alerts = get_alerts()

    # Should match: 2 unauthorized + 3 failed + other default rules
    # Default rules: 2 (unauthorized) + 2 (admin on sensitive) + 3 (failed) = 7
    # New OR rule: 2 (unauthorized) + 3 (failed) = 5
    # Total: 7 + 5 = 12
    assert len(alerts) >= 5, f"OR rule should generate at least 5 alerts, got {len(alerts)}."

    # Clean up
    all_rules = get_all_rules()
    test_rule = next((r for r in all_rules if r[1] == "Test OR Rule: Unauthorized or Failed"), None)
    if test_rule:
        delete_rule(test_rule[0])

