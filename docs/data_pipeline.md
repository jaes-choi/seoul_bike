# 서울시 따릉이 (2018) 데이터 파이프라인 및 구조 명세

## 1. 파이프라인 개요
이 문서는 원본 따릉이 렌탈 및 기상 데이터를 전처리하여 분석용 SQLite 데이터베이스(`seoul_bike_2018.sqlite` 및 1/10 샘플링 버전)로 변환하는 파이프라인(ETL) 프로세스를 설명합니다.

* **스크립트 구성 (총 2개 파일로 단순화)**:
  1. `build_db.py`: 원본 CSV/ZIP 데이터를 읽고, 클렌징 및 전처리하여 통합된 메인 데이터베이스(`seoul_bike_2018.sqlite`)를 생성합니다.
  2. `create_sample_db.py`: Power BI 등 대시보드 실습에 최적화된 1/10 크기의 샘플 데이터베이스(`seoul_bike_2018_10pct.sqlite`)를 계통 추출(Systematic Sampling) 기법으로 생성합니다.

---

## 2. 원본 데이터의 문제점 및 해결 과정 (Data Preprocessing)

원본 데이터 적재 과정에서 발견된 주요 이슈와 파이프라인(Pandas) 내 해결 방식은 다음과 같습니다.

### 2.1 불필요한 중복 데이터 (Redundancy)
* **이슈**: 대여 이력(`rentals`) 파일 안에 대여소 번호와 함께 대여소명, 대여소 ID 컬럼이 매번 중복으로 기록되어 있어 용량 낭비가 심함.
* **해결**: `build_db.py` 적재 단계에서 대여소명, ID 등은 Drop 처리하고 **대여소 번호(`station_no`)만을 Foreign Key로 남겨 정규화(3NF)를 달성**함.

### 2.2 대여소 번호 패딩 포맷 불일치 (Format Inconsistency)
* **이슈**: 마스터 데이터(`stations`)의 번호는 `825` 형태인 반면, 이력 데이터(`rentals`)의 번호는 `00825` 처럼 앞에 '0'이 패딩된 문자열로 존재. 이로 인해 JOIN 연산 시 일치하지 않는 현상 발생.
* **해결**: Pandas 전처리 과정 중 `str.lstrip('0')`을 일괄 적용하여 포맷을 숫자형 문자열로 완벽히 통일함.

### 2.3 기상 데이터와의 일자 조인 문제
* **이슈**: 기상 데이터(`weather`)는 'YYYY-MM-DD' 일자 형태이나, 이력 데이터(`rentals`)는 'YYYY-MM-DD HH:MM:SS' 일시 형태임.
* **해결**: 대여 및 반납 일시에서 날짜 부분(10자리)만 추출하여 `rent_date`, `return_date` 파생 컬럼을 생성하고, 이를 `weather(date)` PK와 연결함.

### 2.4 고아 레코드 및 참조 무결성 (Referential Integrity) 이슈
* **이슈**: 과거 임시 대여소 등으로 인해 이력 데이터에는 존재하나 대여소 마스터 정보 3개 파일(2018, 마스터, 2021) 어디에도 존재하지 않는 미상 대여소 번호가 1,554개 발견됨 (전체 이력의 1.2%).
* **해결**: 적재 중 마스터 테이블에 없는 번호가 등장할 시, `station_name`을 '미상 대여소 (정보 없음)'으로 지정하여 `stations` 테이블에 실시간 Dummy 추가 처리. 이를 통해 엄격한 FK 제약 조건을 만족하는 무결한 DB 확보.

---

## 3. 최종 산출물 데이터베이스 스키마

파이프라인을 거친 후 생성되는 `rentals` 테이블 스키마는 아래와 같습니다.

```sql
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
);

CREATE INDEX idx_rent_time ON rentals(rent_time);
CREATE INDEX idx_rent_station_no ON rentals(rent_station_no);
CREATE INDEX idx_rent_date ON rentals(rent_date);
```

### 최종 산출 파일
1. **`seoul_bike_2018.sqlite`**: 모든 전처리가 완료된 원본 데이터 100% 통합 DB (용량 약 1.8GB)
2. **`seoul_bike_2018_10pct.sqlite`**: Power BI 실습 등을 위한 1/10 계통 추출(시간순) DB (용량 약 180MB)
