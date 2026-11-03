{{ config(materialized='table', schema='gold') }}

SELECT
    o.order_id,
    o.order_date,
    o.customer_id,
    p.product_id,
    p.product_name,
    p.category,
    p.price,
    p.cogs,
    CAST(oi.quantity AS INT) AS quantity,
    CAST(oi.unit_price AS DOUBLE) AS unit_price,
    CAST(oi.discount_amount AS DOUBLE) AS discount_amount,
    (CAST(oi.quantity AS INT) * CAST(oi.unit_price AS DOUBLE)) AS total_item_revenue
FROM {{ ref('stg_orders') }} o
JOIN {{ source('bronze', 'order_items') }} oi ON o.order_id = CAST(oi.order_id AS INT)
JOIN {{ ref('stg_products') }} p ON CAST(oi.product_id AS INT) = p.product_id
