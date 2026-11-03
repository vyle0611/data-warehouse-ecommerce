{{ config(materialized='view', schema='silver') }}

WITH raw_orders AS (
    SELECT * FROM {{ source('bronze', 'orders') }}
)
SELECT
    CAST(order_id AS INT) AS order_id,
    CAST(order_date AS DATE) AS order_date,
    CAST(customer_id AS INT) AS customer_id,
    CAST(zip AS INT) AS shipping_zip,
    LOWER(TRIM(order_status)) AS order_status,
    LOWER(TRIM(payment_method)) AS payment_method,
    COALESCE(LOWER(TRIM(device_type)), 'unknown') AS device_type,
    COALESCE(LOWER(TRIM(order_source)), 'direct') AS order_source
FROM raw_orders
WHERE order_id IS NOT NULL 
  AND order_date IS NOT NULL
