{{ config(materialized='view', schema='silver') }}

WITH raw_products AS (
    SELECT * FROM {{ source('bronze', 'products') }}
)
SELECT
    CAST(product_id AS INT) AS product_id,
    TRIM(product_name) AS product_name,
    TRIM(category) AS category,
    TRIM(segment) AS segment,
    UPPER(TRIM(size)) AS size,
    TRIM(color) AS color,
    CAST(price AS DOUBLE) AS price,
    CAST(cogs AS DOUBLE) AS cogs,
    (CAST(price AS DOUBLE) - CAST(cogs AS DOUBLE)) AS margin
FROM raw_products
WHERE product_id IS NOT NULL
