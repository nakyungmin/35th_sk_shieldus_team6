# 0단계: 공공데이터포털 API로 동물병원과 동반시설 데이터를 받아 CSV로 저장한다.
# 실행: python collect.py
# 인증키는 .env 파일의 DATA_GO_KR_KEY 에서 읽는다. (키가 없으면 기존 CSV 파일을 그대로 쓴다)

import csv
import os

import requests

import config

HOSPITAL_URL = "https://apis.data.go.kr/1741000/animal_hospitals/info"
FACILITY_URL = "https://api.odcloud.kr/api/15111389/v1/uddi:41944402-8249-4e45-9e9d-a52d0a7db1cc"

# 동물병원 API는 항목 이름이 영어라서, 전처리 코드가 쓰는 한글 이름으로 바꿔 저장한다
HOSPITAL_FIELDS = {
    "BPLC_NM": "사업장명",
    "SALS_STTS_NM": "영업상태명",
    "ROAD_NM_ADDR": "도로명주소",
    "LOTNO_ADDR": "지번주소",
    "TELNO": "전화번호",
    "CRD_INFO_X": "좌표정보(X)",
    "CRD_INFO_Y": "좌표정보(Y)",
    "LCPMT_YMD": "인허가일자",
    "MNG_NO": "관리번호",
}


def read_key():
    """.env 파일에서 인증키를 읽는다. 없으면 빈 글자를 돌려준다."""
    if not os.path.exists(".env"):
        return ""
    with open(".env", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line.startswith("DATA_GO_KR_KEY="):
                return line.split("=", 1)[1].strip()
    return ""


def save_csv(path, rows):
    with open(path, "w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


def collect_hospital(key):
    """영업 중인 동물병원을 전국에서 받아 온다. 한 번에 100건씩이라 여러 번 나눠 요청한다."""
    rows = []
    page = 1
    while True:
        params = {
            "serviceKey": key,
            "pageNo": page,
            "numOfRows": 100,
            "returnType": "json",
            "cond[SALS_STTS_CD::EQ]": "01",  # 영업상태코드 01 = 영업/정상
        }
        response = requests.get(HOSPITAL_URL, params=params, timeout=30)
        body = response.json()["response"]["body"]
        items = body["items"]["item"]

        for item in items:
            row = {}
            for english, korean in HOSPITAL_FIELDS.items():
                row[korean] = item[english]
            rows.append(row)

        total = body["totalCount"]
        print(f"  동물병원 {len(rows)} / {total}")
        if len(rows) >= total or len(items) == 0:
            break
        page += 1
    return rows


def collect_facility(key):
    """분석 지역(서울·경기)의 동반시설 데이터를 받아 온다. 한 번에 1000건씩 요청한다."""
    rows = []
    for sido in config.SIDO_LIST:
        page = 1
        count = 0
        while True:
            params = {
                "serviceKey": key,
                "page": page,
                "perPage": 1000,
                "returnType": "JSON",
                "cond[시도 명칭::EQ]": sido,  # 이 시도 것만 달라는 조건
            }
            response = requests.get(FACILITY_URL, params=params, timeout=30)
            result = response.json()

            for item in result["data"]:
                # 빈 값은 None으로 오기 때문에 CSV 파일처럼 빈 글자로 바꾼다
                for name in item:
                    if item[name] is None:
                        item[name] = ""
                    else:
                        item[name] = str(item[name])
                rows.append(item)

            count += result["currentCount"]
            print(f"  동반시설 {sido} {count} / {result['matchCount']}")
            if count >= result["matchCount"] or result["currentCount"] == 0:
                break
            page += 1
    return rows


def main():
    key = read_key()
    if key == "":
        print("인증키가 없습니다. .env 파일에 DATA_GO_KR_KEY를 넣어 주세요. (기존 CSV 파일을 그대로 씁니다)")
        return

    print("API 수집 시작")
    # 중간에 실패하면 파일을 저장하지 않는다. 그러면 전처리는 기존 CSV 파일을 쓴다.
    try:
        hospitals = collect_hospital(key)
        save_csv(config.API_FILES["hospital"], hospitals)
        print(f"  저장: {config.API_FILES['hospital']} {len(hospitals)}건")
    except Exception as error:
        print("  동물병원 API 수집 실패:", type(error).__name__)

    try:
        facilities = collect_facility(key)
        save_csv(config.API_FILES["facility"], facilities)
        print(f"  저장: {config.API_FILES['facility']} {len(facilities)}건")
    except Exception as error:
        print("  동반시설 API 수집 실패:", type(error).__name__)

    print("API 수집 끝")


if __name__ == "__main__":
    main()
