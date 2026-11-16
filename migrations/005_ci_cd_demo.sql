-- UP
CREATE TABLE IF NOT EXISTS
`optimum-phalanx-514316-j3.automation_dataset.Automation`
(
    test_id INT64,
    message STRING,
    created_at TIMESTAMP
);

-- DOWN
DROP TABLE IF EXISTS
`optimum-phalanx-514316-j3.automation_dataset.Automation`;
