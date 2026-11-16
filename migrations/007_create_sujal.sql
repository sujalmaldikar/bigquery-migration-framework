-- UP

CREATE TABLE IF NOT EXISTS
`optimum-phalanx-514316-j3.automation_dataset.employee_sujal`
(
    employee_id INT64,
    employee_name STRING,
    department STRING,
    email STRING,
    joining_date DATE,
    created_at TIMESTAMP
);

-- DOWN

DROP TABLE IF EXISTS
`optimum-phalanx-514316-j3.automation_dataset.employee_sujal`;