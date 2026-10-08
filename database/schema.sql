USE dataguard;

CREATE TABLE IF NOT EXISTS data_quality_issues (
    issue_id INT PRIMARY KEY AUTO_INCREMENT,
    table_name VARCHAR(100),
    record_id INT,
    issue_type VARCHAR(100),
    severity VARCHAR(20),
    details TEXT,
    detected_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS anomaly_results (
    anomaly_id INT PRIMARY KEY AUTO_INCREMENT,
    metric_name VARCHAR(100),
    metric_date DATE,
    expected_value DECIMAL(15,2),
    actual_value DECIMAL(15,2),
    deviation_pct DECIMAL(10,2),
    severity VARCHAR(20),
    detected_at DATETIME DEFAULT CURRENT_TIMESTAMP
);
