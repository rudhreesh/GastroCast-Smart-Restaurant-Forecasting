-- Drop tables if they exist to keep the script idempotent
DROP TABLE IF EXISTS restaurant_sales CASCADE;
DROP TABLE IF EXISTS labour_attendance CASCADE;
DROP TABLE IF EXISTS table_reservations CASCADE;

CREATE TABLE restaurant_sales (
    id SERIAL PRIMARY KEY,
    sale_date DATE NOT NULL,
    sale_time TIME NOT NULL,
    age_group VARCHAR(50),
    weather VARCHAR(50),
    season VARCHAR(50),
    items_sold INTEGER,
    total_sales_amount NUMERIC(10, 2)
);

CREATE TABLE labour_attendance (
    id SERIAL PRIMARY KEY,
    staff_id VARCHAR(50) NOT NULL,
    attendance_date DATE NOT NULL,
    check_in_time TIME,
    check_out_time TIME,
    role VARCHAR(50)
);

CREATE TABLE table_reservations (
    id SERIAL PRIMARY KEY,
    reservation_date DATE NOT NULL,
    reservation_time TIME NOT NULL,
    party_size INTEGER,
    age_group_majority VARCHAR(50)
);
