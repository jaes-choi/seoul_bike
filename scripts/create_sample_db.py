import sqlite3
import os

SOURCE_DB = '../data/seoul_bike_2018.sqlite'
# Naming it '10pct' to clearly indicate it contains 1/10 (10%) of the data
TARGET_DB = '../data/seoul_bike_2018_10pct.sqlite'

def create_sampled_db():
    if os.path.exists(TARGET_DB):
        os.remove(TARGET_DB)
        
    conn = sqlite3.connect(SOURCE_DB)
    cursor = conn.cursor()
    
    print(f"Attaching new database: {TARGET_DB}")
    cursor.execute(f"ATTACH DATABASE '{TARGET_DB}' AS target_db")
    
    print("Copying stations table (Master Data)...")
    cursor.execute("""
    CREATE TABLE target_db.stations AS SELECT * FROM stations
    """)
    
    print("Copying weather table (Master Data)...")
    cursor.execute("""
    CREATE TABLE target_db.weather AS SELECT * FROM weather
    """)
    
    print("Extracting 1/10 of rentals sorted by rent_time (Systematic Sampling)...")
    # Using window function ROW_NUMBER() to sort by rent_time and pick every 10th row
    cursor.execute("""
    CREATE TABLE target_db.rentals AS
    SELECT 
        bicycle_id, rent_time, rent_date, rent_station_no, rent_rack,
        return_time, return_date, return_station_no, return_rack,
        use_time_min, use_dist_m, birth_year, gender, user_type, bicycle_type
    FROM (
        SELECT *, ROW_NUMBER() OVER (ORDER BY rent_time) as rn
        FROM rentals
    )
    WHERE rn % 10 = 0
    """)
    
    print("Creating indexes on the sampled database...")
    cursor.execute("CREATE INDEX target_db.idx_rent_time ON rentals(rent_time)")
    cursor.execute("CREATE INDEX target_db.idx_rent_station_no ON rentals(rent_station_no)")
    cursor.execute("CREATE INDEX target_db.idx_rent_date ON rentals(rent_date)")
    cursor.execute("CREATE UNIQUE INDEX target_db.idx_stations_no ON stations(station_no)")
    cursor.execute("CREATE UNIQUE INDEX target_db.idx_weather_date ON weather(date)")
    
    conn.commit()
    conn.close()
    
    new_size = os.path.getsize(TARGET_DB) / (1024**2)
    print(f"Sample DB created successfully! Size: {new_size:.2f} MB")

if __name__ == '__main__':
    create_sampled_db()
