
CREATE TABLE IF NOT EXISTS `optimum-phalanx-514316-j3.automation_dataset.pooja` (
    order_id INT64 NOT NULL,
    customer_id INT64 NOT NULL,
    order_date DATE,
    order_amount NUMERIC,
    order_status STRING,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP()
);
