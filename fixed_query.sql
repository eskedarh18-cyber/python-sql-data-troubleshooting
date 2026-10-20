-- FIXED: filter completed orders, use EXISTS to prevent payment fan-out,
-- and sum only deduplicated line items inserted by fixed_pipeline.py.
SELECT substr(o.order_date, 1, 7) AS month,
       ROUND(SUM(oi.quantity * oi.unit_price), 2) AS revenue_cad,
       COUNT(DISTINCT o.order_id) AS paid_order_count
FROM orders AS o
JOIN order_items AS oi ON oi.order_id = o.order_id
WHERE o.status = 'completed'
  AND EXISTS (
      SELECT 1 FROM payments AS p
      WHERE p.order_id = o.order_id AND p.status = 'captured'
  )
GROUP BY substr(o.order_date, 1, 7)
ORDER BY month;
