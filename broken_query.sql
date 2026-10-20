-- INTENTIONALLY BROKEN: multiple captured payment rows multiply line items.
-- Also missing the completed-order filter.
SELECT substr(replace(o.order_date, '/', '-'), 1, 7) AS month,
       ROUND(SUM(oi.quantity * oi.unit_price), 2) AS revenue_cad
FROM orders o
JOIN order_items oi ON oi.order_id = o.order_id
JOIN payments p ON p.order_id = o.order_id
WHERE p.status = 'captured'
GROUP BY 1
ORDER BY 1;
