import pandas as pd
import sqlite3
import os

DB_PATH = '../data/db/seoul_bike_2018.sqlite'
EXCEL_PATH = '../data/excel/seoul_bike_2018_1pct_merged.xlsx'

def add_master_sheets():
    print(f"Connecting to database: {DB_PATH}")
    conn = sqlite3.connect(DB_PATH)
    
    print("Reading weather and stations tables...")
    df_weather = pd.read_sql("SELECT * FROM weather", conn)
    df_stations = pd.read_sql("SELECT * FROM stations", conn)
    conn.close()
    
    print(f"Adding sheets to existing Excel file: {EXCEL_PATH}")
    # Use pandas ExcelWriter in append mode with openpyxl
    with pd.ExcelWriter(EXCEL_PATH, engine='openpyxl', mode='a', if_sheet_exists='replace') as writer:
        print("Writing 'weather' sheet...")
        df_weather.to_excel(writer, sheet_name='weather', index=False)
        print("Writing 'stations' sheet...")
        df_stations.to_excel(writer, sheet_name='stations', index=False)
        
    print("Successfully added weather and stations sheets!")

if __name__ == '__main__':
    add_master_sheets()
