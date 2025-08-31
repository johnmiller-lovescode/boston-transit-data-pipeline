-- Vehicles per route today
SELECT route_id, COUNT(*) AS vehicle_count
FROM "boston-transit_db"."vehicles"
WHERE "date" = date_format(current_date, '%Y-%m-%d')
GROUP BY route_id
ORDER BY vehicle_count DESC;

-- Last partition present
SHOW PARTITIONS "boston-transit_db"."vehicles";

-- Peek a route
SELECT * FROM "boston-transit_db"."vehicles"
WHERE route_id = 'Red'
  AND "date" = date_format(current_date, '%Y-%m-%d')
LIMIT 50;
