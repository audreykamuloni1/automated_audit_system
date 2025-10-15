
import os
import psycopg2
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

def get_db_connection():
    """Establishes a connection to the PostgreSQL database."""
    try:
        conn = psycopg2.connect(
            dbname=os.getenv("DB_NAME"),
            user=os.getenv("DB_USER"),
            password=os.getenv("DB_PASSWORD"),
            host=os.getenv("DB_HOST"),
            port=os.getenv("DB_PORT")
        )
        return conn
    except psycopg2.OperationalError as e:
        print(f"Error connecting to the database: {e}")
        return None

def setup_database():
    """Reads the schema.sql file and executes it to set up the DB tables."""
    conn = get_db_connection()
    if conn is None:
        return

    try:
        with conn.cursor() as cur:
            with open('db/schema.sql', 'r') as f:
                cur.execute(f.read())
            conn.commit()
        print("Database setup complete. Tables created successfully.")
    except Exception as e:
        print(f"Error setting up database: {e}")
    finally:
        if conn:
            conn.close()

def get_all_rules():
    """Retrieves all rules with their conditions from the database."""
    conn = get_db_connection()
    if not conn:
        return []
    try:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT r.id, r.name, r.description, r.is_active, r.match_type,
                       COALESCE(
                           json_agg(
                               json_build_object(
                                   'id', rc.id,
                                   'target_field', rc.target_field,
                                   'operator', rc.operator,
                                   'value', rc.value,
                                   'condition_order', rc.condition_order
                               ) ORDER BY rc.condition_order
                           ) FILTER (WHERE rc.id IS NOT NULL),
                           '[]'
                       ) as conditions
                FROM rules r
                LEFT JOIN rule_conditions rc ON r.id = rc.rule_id
                GROUP BY r.id, r.name, r.description, r.is_active, r.match_type
                ORDER BY r.id
            """)
            return cur.fetchall()
    except Exception as e:
        print(f"Error fetching rules: {e}")
        return []
    finally:
        if conn:
            conn.close()

def get_active_rules():
    """Retrieves all active rules with their conditions from the database."""
    conn = get_db_connection()
    if not conn:
        return []
    try:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT r.id, r.name, r.description, r.match_type,
                       COALESCE(
                           json_agg(
                               json_build_object(
                                   'target_field', rc.target_field,
                                   'operator', rc.operator,
                                   'value', rc.value,
                                   'condition_order', rc.condition_order
                               ) ORDER BY rc.condition_order
                           ) FILTER (WHERE rc.id IS NOT NULL),
                           '[]'
                       ) as conditions
                FROM rules r
                LEFT JOIN rule_conditions rc ON r.id = rc.rule_id
                WHERE r.is_active = TRUE
                GROUP BY r.id, r.name, r.description, r.match_type
                ORDER BY r.id
            """)
            return cur.fetchall()
    except Exception as e:
        print(f"Error fetching active rules: {e}")
        return []
    finally:
        if conn:
            conn.close()

def add_rule(name, description, conditions, is_active=True, match_type='AND'):
    """
    Adds a new rule with multiple conditions to the database.

    Args:
        name: Rule name
        description: Rule description
        conditions: List of dicts with keys: target_field, operator, value
                   Example: [
                       {'target_field': 'user_id', 'operator': 'LIKE', 'value': 'admin-%'},
                       {'target_field': 'resource', 'operator': 'LIKE', 'value': '%sensitive%'}
                   ]
        is_active: Whether the rule is active
        match_type: 'AND' or 'OR' - how to combine conditions
    """
    conn = get_db_connection()
    if not conn:
        return False
    try:
        with conn.cursor() as cur:
            # Insert the rule
            cur.execute(
                """
                INSERT INTO rules (name, description, is_active, match_type)
                VALUES (%s, %s, %s, %s)
                RETURNING id
                """,
                (name, description, is_active, match_type)
            )
            rule_id = cur.fetchone()[0]

            # Insert conditions
            for idx, condition in enumerate(conditions):
                cur.execute(
                    """
                    INSERT INTO rule_conditions (rule_id, target_field, operator, value, condition_order)
                    VALUES (%s, %s, %s, %s, %s)
                    """,
                    (rule_id, condition['target_field'], condition['operator'], 
                     condition['value'], idx + 1)
                )

            conn.commit()
        return True
    except Exception as e:
        print(f"Error adding rule: {e}")
        conn.rollback()
        return False
    finally:
        if conn:
            conn.close()

def update_rule(rule_id, name, description, conditions, is_active, match_type='AND'):
    """
    Updates an existing rule and its conditions in the database.

    Args:
        rule_id: ID of the rule to update
        name: New rule name
        description: New rule description
        conditions: List of dicts with keys: target_field, operator, value
        is_active: Whether the rule is active
        match_type: 'AND' or 'OR' - how to combine conditions
    """
    conn = get_db_connection()
    if not conn:
        return False
    try:
        with conn.cursor() as cur:
            # Update the rule
            cur.execute(
                """
                UPDATE rules
                SET name = %s, description = %s, is_active = %s, match_type = %s
                WHERE id = %s
                """,
                (name, description, is_active, match_type, rule_id)
            )

            # Delete old conditions
            cur.execute("DELETE FROM rule_conditions WHERE rule_id = %s", (rule_id,))

            # Insert new conditions
            for idx, condition in enumerate(conditions):
                cur.execute(
                    """
                    INSERT INTO rule_conditions (rule_id, target_field, operator, value, condition_order)
                    VALUES (%s, %s, %s, %s, %s)
                    """,
                    (rule_id, condition['target_field'], condition['operator'], 
                     condition['value'], idx + 1)
                )

            conn.commit()
        return True
    except Exception as e:
        print(f"Error updating rule: {e}")
        conn.rollback()
        return False
    finally:
        if conn:
            conn.close()

def delete_rule(rule_id):
    """Deletes a rule from the database (conditions are cascade deleted)."""
    conn = get_db_connection()
    if not conn:
        return False
    try:
        with conn.cursor() as cur:
            cur.execute("DELETE FROM rules WHERE id = %s", (rule_id,))
            conn.commit()
        return True
    except Exception as e:
        print(f"Error deleting rule: {e}")
        conn.rollback()
        return False
    finally:
        if conn:
            conn.close()

if __name__ == '__main__':
    # This allows running the script directly to initialize the database
    print("Setting up the database...")
    setup_database()

