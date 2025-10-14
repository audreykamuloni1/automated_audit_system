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

-- You can add indexes later for performance optimization
-- CREATE INDEX idx_logs_timestamp ON logs(timestamp);
-- CREATE INDEX idx_alerts_timestamp ON alerts(timestamp);