{{ config(materialized='table', schema='gold') }}

WITH raw_customers AS (
    SELECT * FROM {{ source('bronze', 'customers') }}
)
SELECT
    CAST(c.customer_id AS INT) AS customer_id,
    CAST(c.signup_date AS DATE) AS signup_date,
    COALESCE(TRIM(c.gender), 'Unspecified') AS gender,
    COALESCE(TRIM(c.age_group), 'Unknown') AS age_group,
    COALESCE(TRIM(c.acquisition_channel), 'Organic') AS acquisition_channel,
    CAST(c.zip AS INT) AS zip_code
FROM raw_customers c
WHERE c.customer_id IS NOT NULL
