import pandas as pd
import os
import glob

CSV_DIR = '../data/csv/utf8'
EXCEL_DIR = '../data/excel'

def create_excel():
    os.makedirs(EXCEL_DIR, exist_ok=True)
    
    # 1. 월별 엑셀 파일 생성
    print("Creating monthly Excel files...")
    csv_files = sorted(glob.glob(os.path.join(CSV_DIR, '*.csv')))
    
    all_dfs = []
    
    for f in csv_files:
        month_str = f.split('_')[-2] # e.g., '201801'
        print(f"Reading {month_str}...")
        df = pd.read_csv(f, encoding='utf-8-sig')
        all_dfs.append(df)
        
        excel_path = os.path.join(EXCEL_DIR, f'seoul_bike_{month_str}.xlsx')
        df.to_excel(excel_path, index=False, engine='openpyxl')
        print(f"  -> Saved {excel_path}")
        
    # 2. 전체 1% 통합 엑셀 파일 생성 (약 10만 건, 엑셀 104만 건 제한에 충분함)
    print("Creating single merged Excel file for the 1% data...")
    merged_df = pd.concat(all_dfs, ignore_index=True)
    merged_excel_path = os.path.join(EXCEL_DIR, 'seoul_bike_2018_1pct_merged.xlsx')
    merged_df.to_excel(merged_excel_path, index=False, engine='openpyxl')
    print(f"  -> Saved merged file {merged_excel_path} ({len(merged_df)} rows)")

if __name__ == '__main__':
    create_excel()
    print("Excel generation completed!")
