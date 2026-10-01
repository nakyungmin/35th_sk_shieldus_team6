# 프로젝트 전체에서 같이 쓰는 설정값 모음

# 분석할 지역 (시도 이름). 원본 파일에 적힌 이름 그대로 쓴다.
SIDO_LIST = ["서울특별시", "경기도"]

# 화면에 보여 줄 지역 이름
REGION_NAME = "서울·경기"

# 원본 파일 위치와 저장 방식(인코딩)
RAW_FILES = {
    "hospital": ("data/raw/동물병원_전국.csv", "cp949"),
    "facility": ("data/raw/동반시설.csv", "utf-8-sig"),
    "registration": ("data/raw/동물등록_시군구.csv", "cp949"),
    "park": ("data/raw/도시공원.csv", "utf-8-sig"),
}

# collect.py가 API로 받아서 저장하는 파일. 이 파일이 있으면 위의 원본 대신 이걸 쓴다.
API_FILES = {
    "hospital": "data/raw/동물병원_api.csv",
    "facility": "data/raw/동반시설_api.csv",
}

# 정리한 파일을 저장할 폴더
PROCESSED_DIR = "data/processed"

# 동반시설 데이터에서 "반려동물과 같이 갈 수 있는 곳"으로 볼 분류(카테고리2)
# 반려의료(동물약국·동물병원)와 반려동물 서비스(용품점·미용)는 뺀다.
FACILITY_CATEGORIES = ["반려동물식당카페", "반려동반여행", "반려문화시설"]

# 좌표가 이 범위를 벗어나면 잘못된 값으로 보고 버린다 (우리나라 범위)
LAT_MIN, LAT_MAX = 33.0, 39.0
LON_MIN, LON_MAX = 124.0, 132.0

# MongoDB 접속 정보
MONGO_URI = "mongodb://localhost:27017"
MONGO_DB = "pet_life_map"
