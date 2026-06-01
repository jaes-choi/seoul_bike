# 🚲 Seoul Bike (따릉이) Data Analysis Project 2018

이 저장소는 2018년도 서울시 공공자전거(따릉이) 대여 이력과 기상청 날씨 데이터를 결합하여 **데이터베이스(DB) 모델링 실습, 데이터 분석, Power BI 시각화 실습 및 Python 데이터 전처리 실습**을 목적으로 구축된 교육 및 실습용 프로젝트입니다.

## 🎯 프로젝트 목적
* **DB 개념 및 SQL 실습**: 대용량 데이터를 관계형 데이터베이스(SQLite)로 설계하고 정규화, PK/FK 무결성 제약, 인덱스 최적화 등을 직접 적용해 보는 실습
* **데이터 분석 및 시각화 (BI)**: 기상 조건(기온, 강수량 등)이 자전거 대여량에 미치는 영향을 파악하고 Power BI 등 시각화 툴을 통해 인터랙티브 대시보드 구축
* **Python 기반 ETL 전처리 실습**: 결측치 처리, 포맷 불일치(Zero-padding) 해결, 고아 레코드(Orphan record) 복원 등 Pandas를 활용한 대용량 데이터 파이프라인 설계 경험

## 📊 데이터 소스
본 프로젝트의 원본 데이터는 아래의 공공 데이터 포털에서 수집하였습니다.
* **서울시 공공자전거 데이터**: [서울 열린데이터 광장 (data.seoul.go.kr)](https://data.seoul.go.kr/)
  - 따릉이 대여소 마스터 정보 및 2018년 월별 대여/반납 이력 데이터 (약 1,000만 건 이상)
* **기상청 날씨 데이터**: [기상청 기상자료개방포털 (data.kma.go.kr)](https://data.kma.go.kr/)
  - 2018년 서울(108) 지점 종관기상관측(ASOS) 일별 관측 데이터
* **서울시 행정구역 공간 데이터 (GeoJSON)**: [southkorea/seoul-maps GitHub](https://github.com/southkorea/seoul-maps)
  - 서울시 구별 경계 좌표 데이터 (`seoul_municipalities_geo_simple.json`)

> **참고:** 제공된 다수의 원본 파일(CSV/ZIP/JSON)은 파이썬 스크립트를 통한 데이터 클렌징 및 정규화 과정을 거쳐, 분석에 즉시 활용할 수 있는 단일 **SQLite 데이터베이스 (`.sqlite`)** 파일 및 엑셀/파이썬 실습용 **분할 CSV 파일**, 그리고 지도 시각화용 **GeoJSON 파일**로 구성되어 있습니다.

## 📂 저장소 구조
* `docs/`: 데이터베이스 스키마(DDL) 설계도 및 데이터 파이프라인 구축 과정을 담은 명세서
* `scripts/`: 원본 데이터로부터 SQLite DB 구축, 5% 샘플링 및 CSV 추출을 수행하는 Python ETL 파이프라인 코드
* `data/`: 정제 및 가공이 완료된 최종 산출물 디렉토리 (※ 용량 제한으로 GitHub 업로드 시 제외될 수 있음)
  - `data/db/`: 완성된 SQLite 데이터베이스 파일 저장 (`seoul_bike_2018.sqlite` 등)
  - `data/csv/`: 월별로 1/100 추출 및 정제된 이력 데이터 CSV 파일 저장 (`cp949`, `utf8` 인코딩별 제공)
* `raw/`: 가공 전 원본 CSV, ZIP 데이터 및 공간 데이터(`seoul_municipalities_geo_simple.json`)

## 🛠️ 활용 방법 (How to use)

### 1. Power BI 시각화 실습
* 추출된 `data/db/seoul_bike_2018_5pct.sqlite` (전체 이력의 5% 계통 추출 샘플, 약 90MB) 파일을 Power BI로 불러옵니다. (ODBC 드라이버 필요)
* 대여일자(`rent_date`)를 기준으로 날씨(`weather`) 테이블과, 대여소번호(`rent_station_no`)를 기준으로 대여소(`stations`) 테이블과 조인(Relationship)을 맺습니다.
* **추천 분석 과제**: 
  - 비 오는 날과 맑은 날의 대여량 차이 비교
  - 출/퇴근 시간대 가장 대여 및 반납이 붐비는 핫스팟 대여소 랭킹 산출
  - **지도 시각화 (Geospatial Analysis)**: `raw/seoul_municipalities_geo_simple.json` 형태 맵(Shape Map) 기능에 연동하여, 서울시 구별 대여량 밀도를 나타내는 히트맵(Heatmap) 혹은 등치지역도(Choropleth Map) 구현

### 2. SQL 쿼리 및 DB 성능 실습
* 전체 통합본인 `data/db/seoul_bike_2018.sqlite` (1.8GB 원본) 파일을 DBeaver, DataGrip, 또는 SQLite CLI 도구로 엽니다.
* `PRAGMA foreign_keys = ON;` 명령어를 통해 제약조건을 활성화하고, 1,000만 건이 넘는 대용량 테이블에서 인덱스(Index) 유무에 따른 `JOIN`, `GROUP BY`, `Window Function` 쿼리의 성능(Execution Plan) 차이를 직접 체감해 보세요.

### 3. 기초 데이터 분석 및 공간 시각화 실습 (Pandas, Excel, Folium)
* `data/csv/` 폴더에 제공되는 월별 1/100 축소 데이터(`seoul_bike_YYYYMM.csv`)를 활용하여 가벼운 환경에서 실습을 진행합니다.
* **엑셀 사용자**: 한글 깨짐 방지를 위해 `cp949` 폴더의 데이터를 활용하세요.
* **파이썬(Pandas) 사용자**: 호환성이 높은 `utf8` 폴더의 데이터를 활용하여 시계열 데이터 분석을 진행해 보세요. 특히 **Folium** 등의 라이브러리와 `seoul_municipalities_geo_simple.json` 공간 데이터를 결합하면, 자전거 대여소의 위경도 좌표를 활용하여 지도 위에 구역별 자전거 트래픽을 표현하는 멋진 공간 시각화 포트폴리오를 만들 수 있습니다.

### 4. Python 데이터 엔지니어링 실습
* `scripts/` 내부의 파이프라인 코드(`build_db.py`, `extract_csv_1pct.py`)를 참고하여 대용량 데이터를 메모리 오버플로우 없이 가공(Chunking)하는 기법을 배울 수 있습니다.
* 대여소 번호에 '0'이 패딩되어 조인이 깨지는 문제 등 실무에서 흔히 마주치는 '더티 데이터(Dirty Data)'를 어떻게 정제하여 무결성을 맞추는지 학습해 보세요.
