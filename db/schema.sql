-- Drop tables if they exist to ensure a clean setup
DROP TABLE IF EXISTS alerts;
DROP TABLE IF EXISTS logs;

-- Create logs table to store ingested log data
CREATE TABLE logs (
    id SERIAL PRIMARY KEY,
    timestamp TIMESTAMP NOT NULL,
    user_id VARCHAR(255) NOT NULL,
    action VARCHAR(255) NOT NULL,
    resource VARCHAR(255),
    status VARCHAR(50)
);

-- Create alerts table to store flagged compliance violations
CREATE TABLE alerts (
    id SERIAL PRIMARY KEY,
    log_id INTEGER REFERENCES logs(id),
    rule_id VARCHAR(255) NOT NULL,
    timestamp TIMESTAMP NOT NULL,
    description TEXT
);

CREATE TABLE IF NOT EXISTS rules (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    target_field VARCHAR(255) NOT NULL,
    operator VARCHAR(20) NOT NULL,
    value VARCHAR(255) NOT NULL,
    is_active BOOLEAN DEFAULT TRUE
);

INSERT INTO rules (name, description, target_field, operator, value, is_active)
VALUES
('Unauthorized Access Attempt', 'Flags logs where status is unauthorized.', 'status', '=', 'unauthorized', TRUE),
('Admin Action on Sensitive DB', 'Flags admin actions on sensitive-db.', 'user_id', 'LIKE', 'admin-%', TRUE),
('Multiple Failed Logins', 'Flags users with 3 or more failed logins.', 'status', '=', 'failed', TRUE)
ON CONFLICT DO NOTHING;