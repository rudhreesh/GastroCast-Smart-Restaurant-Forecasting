# AI Agent POC: 12 Test Cases and Results

This document contains the execution results of 12 distinct test cases querying the AI agent. The AI agent generated SQL, executed it, and fed the data to the dummy ML Model.

## Test 1
**Prompt:** `I need a prediction for the period between Jan 12, 2026 to Jan 20, 2026. Give me the daily breakdown of our revenue and the number of people who made bookings.`

**Generated SQL:**
```sql
WITH daily_revenue AS (
  SELECT 
    sale_date, 
    SUM(total_sales_amount) AS daily_total_sales
  FROM 
    restaurant_sales
  WHERE 
    sale_date BETWEEN '2026-01-12' AND '2026-01-20'
  GROUP BY 
    sale_date
),
daily_bookings AS (
  SELECT 
    reservation_date, 
    COUNT(id) AS daily_bookings_count
  FROM 
    table_reservations
  WHERE 
    reservation_date BETWEEN '2026-01-12' AND '2026-01-20'
  GROUP BY 
    reservation_date
)
SELECT 
  COALESCE(dr.sale_date, db.reservation_date) AS date,
  COALESCE(dr.daily_total_sales, 0) AS daily_revenue,
  COALESCE(db.daily_bookings_count, 0) AS daily_bookings
FROM 
  daily_revenue dr
  FULL OUTER JOIN daily_bookings db ON dr.sale_date = db.reservation_date
ORDER BY 
  date;
```

**Data Execution:** Success! Retrieved 9 rows and 3 columns.

**Sample Data (Top 2 rows):**
```text
         date  daily_revenue  daily_bookings
0  2026-01-12        9996.05              14
1  2026-01-13        9841.80               5
```

**ML Output:**
```text
Prediction Output:
  - Expected Customers: 13
  - Recommended Staffing: 4 members
  - Recommended Grocery Inventory multiplier: 1.4
```

---

## Test 2
**Prompt:** `Can you compare the sales performance and the number of servers working on Christmas Eve last year vs New Year's Eve? Assume dates are Dec 24, 2025 and Dec 31, 2025.`

**Generated SQL:**
```sql
SELECT 
    sale_date, 
    SUM(total_sales_amount) AS total_sales, 
    COUNT(DISTINCT staff_id) AS num_servers
FROM 
    restaurant_sales
JOIN 
    labour_attendance ON sale_date = attendance_date
WHERE 
    sale_date IN ('2025-12-24', '2025-12-31') 
    AND role = 'server'
GROUP BY 
    sale_date
ORDER BY 
    sale_date;
```

**Data Execution:** Success! Retrieved 0 rows and 3 columns.

**Sample Data:** No data matched the query conditions.

**ML Output:**
```text
No data to predict on!
```

---

## Test 3
**Prompt:** `We want to know if there's a link between young adults coming in and the amount of food purchased when it's raining.`

**Generated SQL:**
```sql
SELECT 
    DATE_TRUNC('day', sale_date) AS sale_date,
    COUNT(*) AS total_visits,
    SUM(items_sold) AS total_items_sold,
    SUM(total_sales_amount) AS total_sales,
    weather,
    age_group
FROM 
    restaurant_sales
WHERE 
    weather = 'rain'
GROUP BY 
    DATE_TRUNC('day', sale_date),
    weather,
    age_group
ORDER BY 
    sale_date,
    age_group; 

WITH young_adults AS (
    SELECT 
        DATE_TRUNC('day', sale_date) AS sale_date,
        SUM(items_sold) AS total_items_sold,
        SUM(total_sales_amount) AS total_sales
    FROM 
        restaurant_sales
    WHERE 
        age_group = 'young adults' AND weather = 'rain'
    GROUP BY 
        DATE_TRUNC('day', sale_date)
)
SELECT 
    sale_date,
    total_items_sold,
    total_sales
FROM 
    young_adults
ORDER BY 
    sale_date; 

WITH rain_days AS (
    SELECT 
        DATE_TRUNC('day', sale_date) AS sale_date,
        COUNT(*) AS total_visits,
        SUM(items_sold) AS total_items_sold,
        SUM(total_sales_amount) AS total_sales
    FROM 
        restaurant_sales
    WHERE 
        weather = 'rain'
    GROUP BY 
        DATE_TRUNC('day', sale_date)
),
young_adults_rain AS (
    SELECT 
        DATE_TRUNC('day', sale_date) AS sale_date,
        SUM(items_sold) AS total_items_sold,
        SUM(total_sales_amount) AS total_sales
    FROM 
        restaurant_sales
    WHERE 
        age_group = 'young adults' AND weather = 'rain'
    GROUP BY 
        DATE_TRUNC('day', sale_date)
)
SELECT 
    rd.sale_date,
    rd.total_visits,
    rd.total_items_sold AS total_items_sold_all,
    rd.total_sales AS total_sales_all,
    yar.total_items_sold AS total_items_sold_young_adults,
    yar.total_sales AS total_sales_young_adults
FROM 
    rain_days rd
JOIN 
    young_adults_rain yar ON rd.sale_date = yar.sale_date
ORDER BY 
    rd.sale_date;
```

**Data Execution:** Success! Retrieved 0 rows and 6 columns.

**Sample Data:** No data matched the query conditions.

**ML Output:**
```text
No data to predict on!
```

---

## Test 4
**Prompt:** `What was the demand like exactly two weeks ago from today? I need the staff count and total money made.`

**Generated SQL:**
```sql
WITH daily_sales AS (
  SELECT 
    sale_date, 
    COUNT(DISTINCT id) AS total_transactions, 
    SUM(items_sold) AS total_items_sold, 
    SUM(total_sales_amount) AS total_sales
  FROM 
    restaurant_sales
  GROUP BY 
    sale_date
),
daily_labour AS (
  SELECT 
    attendance_date, 
    COUNT(DISTINCT staff_id) AS total_staff
  FROM 
    labour_attendance
  GROUP BY 
    attendance_date
)
SELECT 
  ds.sale_date, 
  dl.total_staff, 
  ds.total_sales
FROM 
  daily_sales ds
JOIN 
  daily_labour dl ON ds.sale_date = dl.attendance_date
WHERE 
  ds.sale_date = CURRENT_DATE - INTERVAL '2 weeks'
```

**Data Execution:** Success! Retrieved 1 rows and 3 columns.

**Sample Data (Top 2 rows):**
```text
    sale_date  total_staff  total_sales
0  2026-02-26            4      3300.69
```

**ML Output:**
```text
Prediction Output:
  - Expected Customers: 1
  - Recommended Staffing: 4 members
  - Recommended Grocery Inventory multiplier: 1.2
```

---

## Test 5
**Prompt:** `Predict demand for February 30th, 2026. How many cooks should we schedule?`

**Generated SQL:**
```sql
WITH daily_sales AS (
  SELECT 
    sale_date, 
    SUM(items_sold) AS total_items_sold, 
    SUM(total_sales_amount) AS total_sales_amount
  FROM 
    restaurant_sales
  GROUP BY 
    sale_date
),
labour_hours AS (
  SELECT 
    attendance_date, 
    role, 
    SUM(EXTRACT(EPOCH FROM (check_out_time - check_in_time))) / 3600 AS total_hours_worked
  FROM 
    labour_attendance
  GROUP BY 
    attendance_date, 
    role
),
reservations AS (
  SELECT 
    reservation_date, 
    SUM(party_size) AS total_party_size
  FROM 
    table_reservations
  GROUP BY 
    reservation_date
),
historical_data AS (
  SELECT 
    rs.sale_date, 
    rs.age_group, 
    rs.weather, 
    rs.season, 
    rs.items_sold, 
    rs.total_sales_amount, 
    la.total_hours_worked AS cook_hours_worked, 
    tr.total_party_size
  FROM 
    restaurant_sales rs
  LEFT JOIN 
    labour_hours la ON rs.sale_date = la.attendance_date AND la.role = 'cook'
  LEFT JOIN 
    reservations tr ON rs.sale_date = tr.reservation_date
)
SELECT 
  DATE_PART('day', sale_date) AS day_of_month, 
  DATE_PART('dow', sale_date) AS day_of_week, 
  season, 
  weather, 
  AVG(items_sold) AS avg_items_sold, 
  AVG(total_sales_amount) AS avg_total_sales_amount, 
  AVG(cook_hours_worked) AS avg_cook_hours_worked, 
  AVG(total_party_size) AS avg_total_party_size
FROM 
  historical_data
WHERE 
  EXTRACT(MONTH FROM sale_date) = 2
GROUP BY 
  DATE_PART('day', sale_date), 
  DATE_PART('dow', sale_date), 
  season, 
  weather
ORDER BY 
  DATE_PART('day', sale_date);
```

**Data Execution:** Success! Retrieved 28 rows and 8 columns.

**Sample Data (Top 2 rows):**
```text
   day_of_month  day_of_week  season weather  avg_items_sold  avg_total_sales_amount avg_cook_hours_worked  avg_total_party_size
0           1.0          0.0  Winter   Rainy        3.197917              138.448958                  None                  65.0
1           2.0          1.0  Winter   Sunny        3.194444              103.562500                  None                  71.0
```

**ML Output:**
```text
No data to predict on!
```

---

## Test 6
**Prompt:** `How many large groups (more than 5 people) usually book tables for dinner time during the winter months?`

**Generated SQL:**
```sql
WITH dinner_reservations AS (
  SELECT 
    reservation_date, 
    reservation_time, 
    party_size, 
    age_group_majority
  FROM 
    table_reservations
  WHERE 
    EXTRACT(HOUR FROM reservation_time) BETWEEN 17 AND 22
),
winter_reservations AS (
  SELECT 
    reservation_date, 
    party_size
  FROM 
    dinner_reservations
  WHERE 
    EXTRACT(MONTH FROM reservation_date) IN (12, 1, 2)
)
SELECT 
  COUNT(*) 
FROM 
  winter_reservations
WHERE 
  party_size > 5
```

**Data Execution:** Success! Retrieved 1 rows and 1 columns.

**Sample Data (Top 2 rows):**
```text
   count
0     95
```

**ML Output:**
```text
Prediction Output:
  - Expected Customers: 1
  - Recommended Staffing: 4 members
  - Recommended Grocery Inventory multiplier: 1.4
```

---

## Test 7
**Prompt:** `Give me a week-by-week trend of our busiest hours and how many shifts our employees are taking.`

**Generated SQL:**
```sql
SELECT 
    EXTRACT(WEEK FROM rs.sale_date) AS week_number,
    DATE_PART('hour', rs.sale_time) AS hour_of_day,
    COUNT(DISTINCT rs.id) AS total_sales,
    SUM(rs.items_sold) AS total_items_sold,
    COUNT(DISTINCT la.staff_id) AS unique_staff,
    SUM(CASE WHEN la.role = 'server' THEN 1 ELSE 0 END) AS server_shifts,
    SUM(CASE WHEN la.role = 'cook' THEN 1 ELSE 0 END) AS cook_shifts,
    SUM(CASE WHEN la.role = 'host' THEN 1 ELSE 0 END) AS host_shifts
FROM 
    restaurant_sales rs
JOIN 
    labour_attendance la ON DATE(rs.sale_date) = DATE(la.attendance_date)
GROUP BY 
    EXTRACT(WEEK FROM rs.sale_date),
    DATE_PART('hour', rs.sale_time)
ORDER BY 
    week_number,
    hour_of_day;
```

**Data Execution:** Success! Retrieved 140 rows and 8 columns.

**Sample Data (Top 2 rows):**
```text
   week_number  hour_of_day  total_sales  total_items_sold  unique_staff  server_shifts  cook_shifts  host_shifts
0          1.0         11.0           15               297             7              0            0            0
1          1.0         12.0           56               935             7              0            0            0
```

**ML Output:**
```text
Prediction Output:
  - Expected Customers: 210
  - Recommended Staffing: 10 members
  - Recommended Grocery Inventory multiplier: 1.1
```

---

## Test 8
**Prompt:** `How many pizzas did we sell on January 15, 2026?`

**Generated SQL:**
```sql
SELECT SUM(items_sold) FROM restaurant_sales WHERE sale_date = '2026-01-15'
```

**Data Execution:** Success! Retrieved 1 rows and 1 columns.

**Sample Data (Top 2 rows):**
```text
   sum
0  195
```

**ML Output:**
```text
Prediction Output:
  - Expected Customers: 1
  - Recommended Staffing: 4 members
  - Recommended Grocery Inventory multiplier: 1.1
```

---

## Test 9
**Prompt:** `I need data for days where we made over $5,000 in revenue but we had fewer than 3 waiters on the floor.`

**Generated SQL:**
```sql
WITH daily_revenue AS (
  SELECT 
    sale_date, 
    SUM(total_sales_amount) AS total_daily_sales,
    COUNT(DISTINCT id) AS total_transactions
  FROM 
    restaurant_sales
  GROUP BY 
    sale_date
),
waiter_count AS (
  SELECT 
    attendance_date, 
    COUNT(DISTINCT staff_id) AS num_waiters
  FROM 
    labour_attendance
  WHERE 
    role = 'waiter'
  GROUP BY 
    attendance_date
)
SELECT 
  dr.sale_date, 
  dr.total_daily_sales, 
  dr.total_transactions, 
  wc.num_waiters
FROM 
  daily_revenue dr
JOIN 
  waiter_count wc ON dr.sale_date = wc.attendance_date
WHERE 
  dr.total_daily_sales > 5000 AND wc.num_waiters < 3;
```

**Data Execution:** Success! Retrieved 0 rows and 4 columns.

**Sample Data:** No data matched the query conditions.

**ML Output:**
```text
No data to predict on!
```

---

## Test 10
**Prompt:** `Show me the sales history for the 2 hours right before our largest bookings (parties over 6) usually happen.`

**Generated SQL:**
```sql
WITH large_bookings AS (
  SELECT reservation_date, reservation_time, party_size
  FROM table_reservations
  WHERE party_size > 6
),
booking_windows AS (
  SELECT 
    reservation_date, 
    reservation_time - INTERVAL '2 hours' AS start_time, 
    reservation_time AS end_time
  FROM large_bookings
),
sales_history AS (
  SELECT 
    sale_date, 
    sale_time, 
    age_group, 
    weather, 
    season, 
    SUM(items_sold) AS total_items_sold, 
    SUM(total_sales_amount) AS total_sales
  FROM restaurant_sales
  WHERE (sale_date, sale_time) IN (
    SELECT reservation_date, start_time 
    FROM booking_windows
  )
  GROUP BY sale_date, sale_time, age_group, weather, season
),
combined_data AS (
  SELECT 
    bw.reservation_date, 
    bw.reservation_time, 
    bw.start_time, 
    bw.end_time, 
    sh.age_group, 
    sh.weather, 
    sh.season, 
    sh.total_items_sold, 
    sh.total_sales
  FROM booking_windows bw
  LEFT JOIN sales_history sh 
  ON bw.reservation_date = sh.sale_date AND bw.start_time = sh.sale_time
)
SELECT 
  reservation_date, 
  reservation_time, 
  start_time, 
  end_time, 
  age_group, 
  weather, 
  season, 
  total_items_sold, 
  total_sales
FROM combined_data
ORDER BY reservation_date, reservation_time;
```

**Data Execution:** Failed.

**Error:**
```text
Execution failed on sql 'WITH large_bookings AS (
  SELECT reservation_date, reservation_time, party_size
  FROM table_reservations
  WHERE party_size > 6
),
booking_windows AS (
  SELECT 
    reservation_date, 
    reservation_time - INTERVAL '2 hours' AS start_time, 
    reservation_time AS end_time
  FROM large_bookings
),
sales_history AS (
  SELECT 
    sale_date, 
    sale_time, 
    age_group, 
    weather, 
    season, 
    SUM(items_sold) AS total_items_sold, 
    SUM(total_sales_amount) AS total_sales
  FROM restaurant_sales
  WHERE (sale_date, sale_time) IN (
    SELECT reservation_date, start_time 
    FROM booking_windows
  )
  GROUP BY sale_date, sale_time, age_group, weather, season
),
combined_data AS (
  SELECT 
    bw.reservation_date, 
    bw.reservation_time, 
    bw.start_time, 
    bw.end_time, 
    sh.age_group, 
    sh.weather, 
    sh.season, 
    sh.total_items_sold, 
    sh.total_sales
  FROM booking_windows bw
  LEFT JOIN sales_history sh 
  ON bw.reservation_date = sh.sale_date AND bw.start_time = sh.sale_time
)
SELECT 
  reservation_date, 
  reservation_time, 
  start_time, 
  end_time, 
  age_group, 
  weather, 
  season, 
  total_items_sold, 
  total_sales
FROM combined_data
ORDER BY reservation_date, reservation_time;': (psycopg2.errors.UndefinedColumn) column bw.reservation_time does not exist
LINE 32:     bw.reservation_time, 
             ^
HINT:  Perhaps you meant to reference the column "bw.reservation_date".

[SQL: WITH large_bookings AS (
  SELECT reservation_date, reservation_time, party_size
  FROM table_reservations
  WHERE party_size > 6
),
booking_windows AS (
  SELECT 
    reservation_date, 
    reservation_time - INTERVAL '2 hours' AS start_time, 
    reservation_time AS end_time
  FROM large_bookings
),
sales_history AS (
  SELECT 
    sale_date, 
    sale_time, 
    age_group, 
    weather, 
    season, 
    SUM(items_sold) AS total_items_sold, 
    SUM(total_sales_amount) AS total_sales
  FROM restaurant_sales
  WHERE (sale_date, sale_time) IN (
    SELECT reservation_date, start_time 
    FROM booking_windows
  )
  GROUP BY sale_date, sale_time, age_group, weather, season
),
combined_data AS (
  SELECT 
    bw.reservation_date, 
    bw.reservation_time, 
    bw.start_time, 
    bw.end_time, 
    sh.age_group, 
    sh.weather, 
    sh.season, 
    sh.total_items_sold, 
    sh.total_sales
  FROM booking_windows bw
  LEFT JOIN sales_history sh 
  ON bw.reservation_date = sh.sale_date AND bw.start_time = sh.sale_time
)
SELECT 
  reservation_date, 
  reservation_time, 
  start_time, 
  end_time, 
  age_group, 
  weather, 
  season, 
  total_items_sold, 
  total_sales
FROM combined_data
ORDER BY reservation_date, reservation_time;]
(Background on this error at: https://sqlalche.me/e/20/f405)
```

---

## Test 11
**Prompt:** `What's the usual checkout time for our bartenders on weekends when the revenue exceeds average?`

**Generated SQL:**
```sql
WITH labour_data AS (
  SELECT 
    attendance_date, 
    check_out_time, 
    role,
    DATE_PART('dow', attendance_date) AS day_of_week
  FROM 
    labour_attendance
),
sales_data AS (
  SELECT 
    sale_date, 
    total_sales_amount
  FROM 
    restaurant_sales
),
avg_sales AS (
  SELECT 
    AVG(total_sales_amount) AS avg_total_sales
  FROM 
    restaurant_sales
),
combined_data AS (
  SELECT 
    ld.attendance_date, 
    ld.check_out_time, 
    ld.role,
    sd.total_sales_amount,
    ld.day_of_week
  FROM 
    labour_data ld
  JOIN 
    sales_data sd ON ld.attendance_date = sd.sale_date
)
SELECT 
  check_out_time, 
  role, 
  AVG(total_sales_amount) AS avg_total_sales
FROM 
  combined_data
WHERE 
  role = 'bartender' 
  AND day_of_week IN (0, 6) 
  AND total_sales_amount > (SELECT avg_total_sales FROM avg_sales)
GROUP BY 
  check_out_time, 
  role
ORDER BY 
  check_out_time;
```

**Data Execution:** Success! Retrieved 0 rows and 3 columns.

**Sample Data:** No data matched the query conditions.

**ML Output:**
```text
No data to predict on!
```

---

## Test 12
**Prompt:** `Just give me all the data I need to predict how busy we will be next week.`

**Generated SQL:**
```sql
WITH daily_sales AS (
  SELECT 
    sale_date, 
    SUM(items_sold) AS total_items_sold, 
    SUM(total_sales_amount) AS total_sales_amount, 
    COUNT(DISTINCT age_group) AS age_groups_present, 
    COUNT(DISTINCT weather) AS weather_conditions, 
    COUNT(DISTINCT season) AS seasons_present
  FROM 
    restaurant_sales
  GROUP BY 
    sale_date
),
labour_data AS (
  SELECT 
    attendance_date, 
    COUNT(DISTINCT staff_id) AS staff_present, 
    COUNT(DISTINCT role) AS roles_present
  FROM 
    labour_attendance
  GROUP BY 
    attendance_date
),
reservation_data AS (
  SELECT 
    reservation_date, 
    SUM(party_size) AS total_party_size, 
    COUNT(DISTINCT age_group_majority) AS age_groups_reserved
  FROM 
    table_reservations
  GROUP BY 
    reservation_date
)
SELECT 
  ds.sale_date, 
  ds.total_items_sold, 
  ds.total_sales_amount, 
  ds.age_groups_present, 
  ds.weather_conditions, 
  ds.seasons_present, 
  ld.staff_present, 
  ld.roles_present, 
  rd.total_party_size, 
  rd.age_groups_reserved, 
  DATE_PART('day', ds.sale_date) AS day_of_month, 
  DATE_PART('dow', ds.sale_date) AS day_of_week, 
  DATE_PART('month', ds.sale_date) AS month, 
  DATE_PART('year', ds.sale_date) AS year
FROM 
  daily_sales ds
  LEFT JOIN labour_data ld ON ds.sale_date = ld.attendance_date
  LEFT JOIN reservation_data rd ON ds.sale_date = rd.reservation_date
ORDER BY 
  ds.sale_date;
```

**Data Execution:** Success! Retrieved 90 rows and 14 columns.

**Sample Data (Top 2 rows):**
```text
    sale_date  total_items_sold  total_sales_amount  age_groups_present  weather_conditions  seasons_present  staff_present  roles_present  total_party_size  age_groups_reserved  day_of_month  day_of_week  month    year
0  2025-12-12                88             4001.12                   4                   1                1              6              5                36                    3          12.0          5.0   12.0  2025.0
1  2025-12-13               260            11506.21                   4                   1                1              7              5                34                    4          13.0          6.0   12.0  2025.0
```

**ML Output:**
```text
Prediction Output:
  - Expected Customers: 135
  - Recommended Staffing: 6 members
  - Recommended Grocery Inventory multiplier: 1.3
```

---

