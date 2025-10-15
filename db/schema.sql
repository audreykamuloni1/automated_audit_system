-- Drop tables if they exist to ensure a clean setup
DROP TABLE IF EXISTS anomalies;
DROP TABLE IF EXISTS alerts;
DROP TABLE IF EXISTS logs;
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
    target_field VARCHAR(100) NOT NULL, -- e.g., 'action', 'status', 'user_id'
    operator VARCHAR(50) NOT NULL,     -- e.g., '=', '!=', 'LIKE', 'IN'
    value VARCHAR(255) NOT NULL,
    is_active BOOLEAN DEFAULT TRUE
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

-- Add some default rules to get started (idempotent insert)
INSERT INTO rules (name, description, target_field, operator, value, is_active) VALUES
('Unauthorized Access Attempt', 'Flags any log entry where the status is unauthorized.', 'status', '=', 'unauthorized', TRUE),
('Admin Action on Sensitive DB', 'Flags actions by admins on sensitive databases.', 'user_id', 'LIKE', 'admin-%', TRUE),
('Multiple Failed Logins', 'Flags users with 3 or more failed login attempts.', 'status', '=', 'failed', TRUE)
ON CONFLICT (name) DO NOTHING;

-- Indexes for performance
CREATE INDEX idx_logs_timestamp ON logs(timestamp);
CREATE INDEX idx_alerts_timestamp ON alerts(timestamp);
CREATE INDEX idx_anomalies_timestamp ON anomalies(timestamp);
CREATE INDEX idx_logs_user_id ON logs(user_id);
CREATE INDEX idx_logs_action ON logs(action);
CREATE INDEX idx_logs_status ON logs(status);