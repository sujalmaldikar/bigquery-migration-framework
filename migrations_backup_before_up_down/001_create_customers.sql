
CREATE TABLE IF NOT EXISTS `optimum-phalanx-514316-j3.automation_dataset.customers` (
    customer_id INT64 NOT NULL,
    customer_name STRING NOT NULL,
    email STRING,
    city STRING,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP()
);
