import pandas as pd
import sqlite3
import zipfile
import os

DB_PATH = '../data/seoul_bike_2018.sqlite'
RAW_DIR = '../raw'

def setup_db(conn):
    cursor = conn.cursor()
    cursor.execute("PRAGMA foreign_keys = OFF;")
    
    # 1. 마스터 테이블 생성 (stations, weather)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS stations (
        id INTEGER PRIMARY KEY,
        station_type TEXT,
        station_id TEXT,
        station_no TEXT UNIQUE,
        station_name TEXT,
        rack_count INTEGER,
        latitude REAL,
        longitude REAL
    )
    """)
    
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS weather (
        date TEXT PRIMARY KEY,
        station INTEGER,
        avg_temp REAL,
        min_temp REAL,
        max_temp REAL,
        rain_amt REAL,
        avg_wind REAL,
        avg_humidity REAL,
        snow_amt REAL
    )
    """)
    
    # 2. 이력 테이블 생성 (중복 컬럼 제외, 일자 컬럼 추가, FK 제약조건 설정)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS rentals (
        bicycle_id TEXT,
        rent_time TEXT,
        rent_date TEXT,
        rent_station_no TEXT,
        rent_rack INTEGER,
        return_time TEXT,
        return_date TEXT,
        return_station_no TEXT,
        return_rack INTEGER,
        use_time_min INTEGER,
        use_dist_m REAL,
        birth_year TEXT,
        gender TEXT,
        user_type TEXT,
        bicycle_type TEXT,
        FOREIGN KEY(rent_station_no) REFERENCES stations(station_no),
        FOREIGN KEY(return_station_no) REFERENCES stations(station_no),
        FOREIGN KEY(rent_date) REFERENCES weather(date)
    )
    """)
    conn.commit()

def load_master_data(conn):
    print("Loading weather data...")
    df_w = pd.read_csv(os.path.join(RAW_DIR, 'SURFACE_ASOS_108_DAY_2018_2018_2019.csv'), encoding='cp949')
    df_w = df_w[df_w['일시'].str.startswith('2018')]
    weather_df = pd.DataFrame({
        'date': df_w['일시'], 'station': df_w['지점'], 'avg_temp': df_w['평균기온(°C)'],
        'min_temp': df_w['최저기온(°C)'], 'max_temp': df_w['최고기온(°C)'], 'rain_amt': df_w['일강수량(mm)'],
        'avg_wind': df_w['평균 풍속(m/s)'], 'avg_humidity': df_w['평균 상대습도(%)'], 'snow_amt': df_w['일 최심적설(cm)']
    })
    weather_df.to_sql('weather', conn, if_exists='append', index=False)
    
    print("Loading stations data...")
    # 메인 대여소 파일
    df_s1 = pd.read_csv(os.path.join(RAW_DIR, '서울시 공공자전거 대여소 정보_20181129.csv'), encoding='cp949')
    df_s1.columns = ['id', 'station_type', 'station_id', 'station_no', 'station_name', 'rack_count', 'latitude', 'longitude']
    df_s1['station_no'] = df_s1['station_no'].astype(str).str.lstrip('0')
    df_s1.to_sql('stations', conn, if_exists='append', index=False)
    
    # 누락된 대여소 추출을 위해 나머지 파일들도 처리
    df_s2 = pd.read_csv(os.path.join(RAW_DIR, '공공자전거 대여소 정보(21.01.31 기준).csv'), encoding='cp949', skiprows=5, header=None)
    new_stations = []
    known_stations = set(df_s1['station_no'].dropna())
    
    for _, row in df_s2.iterrows():
        st_no = str(row[0]).split('.')[0] if pd.notna(row[0]) else ''
        st_no = st_no.lstrip('0')
        if st_no and st_no not in known_stations:
            new_stations.append({
                'station_no': st_no, 'station_name': row[1], 'latitude': row[4], 'longitude': row[5],
                'rack_count': row[7] if pd.notna(row[7]) else (row[8] if pd.notna(row[8]) else 0)
            })
            known_stations.add(st_no)
            
    if new_stations:
        pd.DataFrame(new_stations).to_sql('stations', conn, if_exists='append', index=False)

def load_rentals_and_apply_fks(conn):
    print("Loading rentals and preprocessing on-the-fly...")
    zip_path = os.path.join(RAW_DIR, '서울특별시 공공자전거 대여이력 정보_2018.zip')
    
    # 현재 DB에 등록된 대여소 번호 목록
    known_stations = set(pd.read_sql("SELECT station_no FROM stations WHERE station_no IS NOT NULL", conn)['station_no'])
    
    col_map = {
        '자전거번호': 'bicycle_id', '대여일시': 'rent_time', '대여 대여소번호': 'rent_station_no',
        '대여거치대': 'rent_rack', '반납일시': 'return_time', '반납대여소번호': 'return_station_no',
        '반납거치대': 'return_rack', '이용시간(분)': 'use_time_min', '이용거리(M)': 'use_dist_m',
        '생년': 'birth_year', '성별': 'gender', '이용자종류': 'user_type', '자전거구분': 'bicycle_type'
    }
    
    with zipfile.ZipFile(zip_path, 'r') as z:
        for filename in z.namelist():
            if filename.endswith('.csv'):
                print(f"Processing {filename}...")
                with z.open(filename) as f:
                    chunk_iter = pd.read_csv(f, encoding='cp949', chunksize=200000, on_bad_lines='skip', low_memory=False)
                    for chunk in chunk_iter:
                        chunk.columns = chunk.columns.str.replace(' ', '').str.strip()
                        clean_map = {k.replace(' ', ''): v for k, v in col_map.items()}
                        available_cols = [c for c in chunk.columns if c in clean_map]
                        chunk = chunk[available_cols].rename(columns=clean_map)
                        
                        # 전처리: 날짜 파싱 및 앞의 '0' 제거
                        if 'rent_time' in chunk.columns:
                            chunk['rent_date'] = chunk['rent_time'].str[:10]
                        if 'return_time' in chunk.columns:
                            chunk['return_date'] = chunk['return_time'].str[:10]
                        if 'rent_station_no' in chunk.columns:
                            chunk['rent_station_no'] = chunk['rent_station_no'].astype(str).str.lstrip('0')
                        if 'return_station_no' in chunk.columns:
                            chunk['return_station_no'] = chunk['return_station_no'].astype(str).str.lstrip('0')
                        
                        # 무결성을 위해 청크 내의 누락된 대여소 번호를 더미 데이터로 실시간 추가
                        chunk_stations = set(chunk['rent_station_no'].dropna()) | set(chunk['return_station_no'].dropna())
                        missing = chunk_stations - known_stations
                        missing.discard('')
                        missing.discard('nan')
                        
                        if missing:
                            dummy_df = pd.DataFrame([{'station_no': m, 'station_name': '미상 대여소 (정보 없음)'} for m in missing])
                            dummy_df.to_sql('stations', conn, if_exists='append', index=False)
                            known_stations.update(missing)
                            
                        chunk.to_sql('rentals', conn, if_exists='append', index=False)

def create_indexes(conn):
    print("Creating indexes...")
    cursor = conn.cursor()
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_rent_time ON rentals(rent_time)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_rent_station_no ON rentals(rent_station_no)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_rent_date ON rentals(rent_date)")
    conn.commit()

if __name__ == '__main__':
    if os.path.exists(DB_PATH):
        os.remove(DB_PATH)
    conn = sqlite3.connect(DB_PATH)
    setup_db(conn)
    load_master_data(conn)
    load_rentals_and_apply_fks(conn)
    create_indexes(conn)
    conn.close()
    print("Unified Data Pipeline completed successfully!")
