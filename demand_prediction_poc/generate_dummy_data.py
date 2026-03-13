import os
import psycopg2
from faker import Faker
import random
from datetime import datetime, timedelta

def get_db_connection():
    return psycopg2.connect(
        dbname=os.environ.get("POSTGRES_DB", "demand_db"),
        user=os.environ.get("POSTGRES_USER", "demand_user"),
        password=os.environ.get("POSTGRES_PASSWORD", "demand_password"),
        host=os.environ.get("POSTGRES_HOST", "localhost"),
        port=os.environ.get("POSTGRES_PORT", "5433")
    )

def setup_schema(conn):
    with conn.cursor() as cur:
        with open('schema.sql', 'r') as f:
            cur.execute(f.read())
    conn.commit()

def generate_data(conn):
    fake = Faker()
    cur = conn.cursor()
    
    # Configuration
    num_days = 730
    start_date = datetime.today() - timedelta(days=num_days)
    
    staff = [
        {"id": "S001", "role": "Manager"},
        {"id": "S002", "role": "Chef"},
        {"id": "S003", "role": "Sous Chef"},
        {"id": "S004", "role": "Waiter"},
        {"id": "S005", "role": "Waiter"},
        {"id": "S006", "role": "Waiter"},
        {"id": "S007", "role": "Bartender"},
    ]
    
    age_groups = ["18-25", "26-35", "36-50", "51+"]
    weather_conditions = ["Sunny", "Rainy", "Cloudy", "Snowy"]
    seasons = ["Spring", "Summer", "Autumn", "Winter"]
    
    # Generate data day by day
    for i in range(num_days):
        current_date = start_date + timedelta(days=i)
        
        # Consistent daily weather/season
        daily_weather = random.choice(weather_conditions)
        if current_date.month in [12, 1, 2]:
            daily_season = "Winter"
        elif current_date.month in [3, 4, 5]:
            daily_season = "Spring"
        elif current_date.month in [6, 7, 8]:
            daily_season = "Summer"
        else:
            daily_season = "Autumn"
            
        # 1. Restaurant Sales
        # Simulate peak hours (lunch 12-14, dinner 18-21) and off-peak
        num_sales_today = random.randint(20, 100)
        for _ in range(num_sales_today):
            hour = random.choices(
                [11, 12, 13, 14, 17, 18, 19, 20, 21, 22],
                weights=[1, 4, 4, 2, 2, 5, 5, 4, 2, 1],
                k=1
            )[0]
            minute = random.randint(0, 59)
            sale_time = f"{hour:02d}:{minute:02d}:00"
            
            age_group = random.choice(age_groups)
            items_sold = random.randint(1, 5)
            # Higher sales amount on weekends or dinner time
            base_amount = random.uniform(20.0, 150.0)
            if hour >= 18:
                base_amount *= 1.5
            if current_date.weekday() >= 5: # weekend
                base_amount *= 1.2
            
            cur.execute("""
                INSERT INTO restaurant_sales (sale_date, sale_time, age_group, weather, season, items_sold, total_sales_amount)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
            """, (current_date.date(), sale_time, age_group, daily_weather, daily_season, items_sold, round(base_amount, 2)))

        # 2. Labour Attendance
        # Weekend needs more staff, weekday less
        staff_needed = 7 if current_date.weekday() >= 5 else random.randint(4, 6)
        daily_staff = random.sample(staff, staff_needed)
        
        for s in daily_staff:
            # Check in around 10am, checkout around 10pm usually, with some variation
            check_in_hour = random.randint(9, 11)
            check_in_minute = random.randint(0, 59)
            check_in = f"{check_in_hour:02d}:{check_in_minute:02d}:00"
            
            check_out_hour = random.randint(20, 23)
            check_out_minute = random.randint(0, 59)
            check_out = f"{check_out_hour:02d}:{check_out_minute:02d}:00"
            
            cur.execute("""
                INSERT INTO labour_attendance (staff_id, attendance_date, check_in_time, check_out_time, role)
                VALUES (%s, %s, %s, %s, %s)
            """, (s["id"], current_date.date(), check_in, check_out, s["role"]))

        # 3. Table Reservations
        num_reservations = random.randint(5, 20)
        for _ in range(num_reservations):
            res_hour = random.choice([12, 13, 18, 19, 20])
            res_minute = random.choice([0, 15, 30, 45])
            res_time = f"{res_hour:02d}:{res_minute:02d}:00"
            
            party_size = random.choices([2, 3, 4, 5, 6, 8], weights=[4, 2, 4, 1, 1, 1], k=1)[0]
            age_group_majority = random.choice(age_groups)
            
            cur.execute("""
                INSERT INTO table_reservations (reservation_date, reservation_time, party_size, age_group_majority)
                VALUES (%s, %s, %s, %s)
            """, (current_date.date(), res_time, party_size, age_group_majority))

    conn.commit()
    cur.close()
    print(f"Generated data for {num_days} days.")

if __name__ == "__main__":
    print("Connecting to database...")
    conn = get_db_connection()
    print("Setting up schema...")
    setup_schema(conn)
    print("Generating dummy data...")
    generate_data(conn)
    conn.close()
    print("Data generation complete!")
