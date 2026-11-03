{{ config(materialized='view', schema='silver') }}

WITH raw_sales AS (
    SELECT * FROM {{ source('bronze', 'sales') }}
)
SELECT
    CAST(Date AS DATE) AS sales_date,
    CAST(Revenue AS DOUBLE) AS revenue,
    CAST(COGS AS DOUBLE) AS cogs,
    (CAST(Revenue AS DOUBLE) - CAST(COGS AS DOUBLE)) AS gross_profit
FROM raw_sales
WHERE Date IS NOT NULL
