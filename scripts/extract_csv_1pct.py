import pandas as pd
import zipfile
import os
import re

RAW_DIR = '../raw'
ZIP_PATH = os.path.join(RAW_DIR, '서울특별시 공공자전거 대여이력 정보_2018.zip')
CSV_DIR_CP949 = '../data/csv/cp949'
CSV_DIR_UTF8 = '../data/csv/utf8'

def extract_csv():
    os.makedirs(CSV_DIR_CP949, exist_ok=True)
    os.makedirs(CSV_DIR_UTF8, exist_ok=True)
    
    col_map = {
        '자전거번호': 'bicycle_id', '대여일시': 'rent_time', '대여 대여소번호': 'rent_station_no',
        '대여거치대': 'rent_rack', '반납일시': 'return_time', '반납대여소번호': 'return_station_no',
        '반납거치대': 'return_rack', '이용시간(분)': 'use_time_min', '이용거리(M)': 'use_dist_m',
        '생년': 'birth_year', '성별': 'gender', '이용자종류': 'user_type', '자전거구분': 'bicycle_type'
    }
    
    with zipfile.ZipFile(ZIP_PATH, 'r') as z:
        for filename in z.namelist():
            if filename.endswith('.csv'):
                # Extract month from filename (e.g. "..._1801.csv" -> "01")
                match = re.search(r'_18(\d{2})\.csv', filename)
                if not match:
                    continue
                month = match.group(1)
                print(f"Processing month 2018-{month} from {filename}...")
                
                with z.open(filename) as f:
                    # Read the entire monthly file
                    df = pd.read_csv(f, encoding='cp949', on_bad_lines='skip', low_memory=False)
                    
                    # Clean column names
                    df.columns = df.columns.str.replace(' ', '').str.strip()
                    clean_map = {k.replace(' ', ''): v for k, v in col_map.items()}
                    available_cols = [c for c in df.columns if c in clean_map]
                    df = df[available_cols].rename(columns=clean_map)
                    
                    # Sort by rent_time to apply systematic sampling
                    if 'rent_time' in df.columns:
                        df = df.sort_values(by='rent_time').reset_index(drop=True)
                    
                    # Extract 1/100 (Systematic sampling)
                    df_sample = df.iloc[::100].copy()
                    
                    # Clean data formatting (Remove zero padding from stations)
                    if 'rent_station_no' in df_sample.columns:
                        df_sample['rent_station_no'] = df_sample['rent_station_no'].astype(str).str.lstrip('0')
                    if 'return_station_no' in df_sample.columns:
                        df_sample['return_station_no'] = df_sample['return_station_no'].astype(str).str.lstrip('0')
                        
                    # Save to both encodings
                    out_name_cp949 = f'seoul_bike_2018{month}_cp949.csv'
                    out_name_utf8 = f'seoul_bike_2018{month}_utf8.csv'
                    
                    path_cp949 = os.path.join(CSV_DIR_CP949, out_name_cp949)
                    df_sample.to_csv(path_cp949, encoding='cp949', index=False)
                    
                    path_utf8 = os.path.join(CSV_DIR_UTF8, out_name_utf8)
                    df_sample.to_csv(path_utf8, encoding='utf-8-sig', index=False) # utf-8-sig for excel compatibility
                    
                    print(f"  -> Saved {len(df_sample)} rows to {out_name_cp949} and {out_name_utf8}")

if __name__ == '__main__':
    extract_csv()
    print("CSV extraction completed!")
