
-- Drop tables if they exist to ensure a clean setup
DROP TABLE IF EXISTS anomalies;
DROP TABLE IF EXISTS alerts;
DROP TABLE IF EXISTS logs;
DROP TABLE IF EXISTS rule_conditions;
DROP TABLE IF EXISTS rules;

-- Create logs table to store ingested log data
CREATE TABLE logs (
    id SERIAL PRIMARY KEY,
    timestamp TIMESTAMP NOT NULL,
    user_id VARCHAR(255) NOT NULL,
    action VARCHAR(255) NOT NULL,
    resource VARCHAR(255),
    status VARCHAR(50)
);

-- Create rules table to store dynamic compliance rules
CREATE TABLE rules (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL UNIQUE,
    description TEXT,
    is_active BOOLEAN DEFAULT TRUE,
    match_type VARCHAR(10) DEFAULT 'AND' CHECK (match_type IN ('AND', 'OR'))
    -- match_type determines how multiple conditions are combined
    -- 'AND' = all conditions must match
    -- 'OR' = at least one condition must match
);

-- Create rule_conditions table for compound rules (multiple conditions per rule)
CREATE TABLE rule_conditions (
    id SERIAL PRIMARY KEY,
    rule_id INTEGER REFERENCES rules(id) ON DELETE CASCADE,
    target_field VARCHAR(100) NOT NULL, -- e.g., 'action', 'status', 'user_id', 'resource'
    operator VARCHAR(50) NOT NULL,      -- e.g., '=', '!=', 'LIKE', 'IN', 'NOT LIKE'
    value VARCHAR(255) NOT NULL,
    condition_order INTEGER DEFAULT 0   -- Order for evaluation
);

-- Create alerts table to store flagged compliance violations
CREATE TABLE alerts (
    id SERIAL PRIMARY KEY,
    log_id INTEGER REFERENCES logs(id) ON DELETE CASCADE,
    rule_id INTEGER REFERENCES rules(id) ON DELETE CASCADE,
    timestamp TIMESTAMP NOT NULL,
    description TEXT
);

-- Create anomalies table to store results from the ML model
CREATE TABLE anomalies (
    id SERIAL PRIMARY KEY,
    log_id INTEGER REFERENCES logs(id) ON DELETE CASCADE,
    timestamp TIMESTAMP NOT NULL,
    score DECIMAL(10, 5) NOT NULL, -- The anomaly score from the model
    details TEXT -- Details about why it was flagged (e.g., unusual action for user)
);



-- Rule 1: Unauthorized Access Attempt (simple rule)
INSERT INTO rules (name, description, is_active, match_type) VALUES
('Unauthorized Access Attempt', 'Flags any log entry where the status is unauthorized.', TRUE, 'AND')
ON CONFLICT (name) DO NOTHING;

INSERT INTO rule_conditions (rule_id, target_field, operator, value, condition_order)
SELECT id, 'status', '=', 'unauthorized', 1
FROM rules WHERE name = 'Unauthorized Access Attempt'
ON CONFLICT DO NOTHING;

-- Rule 2: Admin Action on Sensitive DB (compound rule with AND)
INSERT INTO rules (name, description, is_active, match_type) VALUES
('Admin Action on Sensitive DB', 'Flags actions by admins on sensitive databases.', TRUE, 'AND')
ON CONFLICT (name) DO NOTHING;

INSERT INTO rule_conditions (rule_id, target_field, operator, value, condition_order)
SELECT id, 'user_id', 'LIKE', 'admin-%', 1
FROM rules WHERE name = 'Admin Action on Sensitive DB'
ON CONFLICT DO NOTHING;

INSERT INTO rule_conditions (rule_id, target_field, operator, value, condition_order)
SELECT id, 'resource', 'LIKE', '%sensitive%', 2
FROM rules WHERE name = 'Admin Action on Sensitive DB'
ON CONFLICT DO NOTHING;

-- Rule 3: Multiple Failed Logins (simple rule)
INSERT INTO rules (name, description, is_active, match_type) VALUES
('Multiple Failed Logins', 'Flags users with failed login attempts.', TRUE, 'AND')
ON CONFLICT (name) DO NOTHING;

INSERT INTO rule_conditions (rule_id, target_field, operator, value, condition_order)
SELECT id, 'status', '=', 'failed', 1
FROM rules WHERE name = 'Multiple Failed Logins'
ON CONFLICT DO NOTHING;

-- Indexes for performance
CREATE INDEX idx_logs_timestamp ON logs(timestamp);
CREATE INDEX idx_alerts_timestamp ON alerts(timestamp);
CREATE INDEX idx_anomalies_timestamp ON anomalies(timestamp);
CREATE INDEX idx_logs_user_id ON logs(user_id);
CREATE INDEX idx_logs_action ON logs(action);
CREATE INDEX idx_logs_status ON logs(status);
CREATE INDEX idx_logs_resource ON logs(resource);
CREATE INDEX idx_rule_conditions_rule_id ON rule_conditions(rule_id);


