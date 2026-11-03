{{ config(materialized='table', schema='gold') }}

WITH silver_sales AS (
    SELECT * FROM {{ ref('stg_sales') }}
)
SELECT
    sales_date,
    EXTRACT(YEAR FROM sales_date) AS sales_year,
    EXTRACT(MONTH FROM sales_date) AS sales_month,
    EXTRACT(DAYOFWEEK FROM sales_date) AS day_of_week,
    EXTRACT(DAYOFYEAR FROM sales_date) AS day_of_year,
    revenue,
    cogs,
    gross_profit,
    ROUND((gross_profit / NULLIF(revenue, 0)) * 100, 2) AS profit_margin_pct
FROM silver_sales
ORDER BY sales_date ASC
