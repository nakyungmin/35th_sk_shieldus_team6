import csv
import json
import os

from pyproj import Transformer

import config


def read_csv(name):

    path, encoding = config.RAW_FILES[name]
    if name in config.API_FILES and os.path.exists(config.API_FILES[name]):
        path = config.API_FILES[name]
        encoding = "utf-8-sig"
        print(f"  ({name}: API로 받은 파일 사용)")
    with open(path, encoding=encoding, newline="") as f:
        return list(csv.DictReader(f))


def save(name, rows):
    
    os.makedirs(config.PROCESSED_DIR, exist_ok=True)

    with open(f"{config.PROCESSED_DIR}/{name}.json", "w", encoding="utf-8") as f:
        json.dump(rows, f, ensure_ascii=False, indent=1)

    with open(f"{config.PROCESSED_DIR}/{name}.csv", "w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)

    print(f"  저장: {name} {len(rows)}건")


def to_number(text):
    """'34,402' 같은 글자를 숫자 34402로 바꾼다."""
    return int(text.replace(",", "").strip())


def clean_name(text):
    """이름 앞뒤 공백과, 지도 코드를 깨뜨리는 기호(`)를 없앤다."""
    return text.replace("`", "").strip()


def valid_coord(lat, lon):
    """위도·경도가 우리나라 범위 안인지 확인한다."""
    return (config.LAT_MIN <= lat <= config.LAT_MAX
            and config.LON_MIN <= lon <= config.LON_MAX)


def region_from_address(address):
    """'경기도 수원시 영통구 ...' 에서 ('경기도', '수원시')를 꺼낸다.
    서울은 '서울특별시 강남구 ...' -> ('서울특별시', '강남구')."""
    parts = address.split()
    if len(parts) >= 2 and parts[0] in config.SIDO_LIST:
        return (parts[0], parts[1])
    return None


# ---------- 동물등록 ----------
def clean_registration():
    """시·군·구별 등록 동물 수"""
    totals = {}
    for row in read_csv("registration"):
        if row["시도"] not in config.SIDO_LIST or row["시군구"] == "":
            continue

        sido = row["시도"]
        city = row["시군구"]
        if city == "여주군":
            city = "여주시"

        key = (sido, city)
        if key not in totals:
            totals[key] = {"sido": sido, "city": city, "dogs": 0, "cats": 0, "registered": 0}
        totals[key]["dogs"] += to_number(row["개등록 누계"])
        totals[key]["cats"] += to_number(row["고양이등록 누계"])
        totals[key]["registered"] += to_number(row["총 등록 누계"])
    return list(totals.values())


# ---------- 동물병원 ----------
def clean_hospital(regions):
    """영업 중인 병원만 남기고, 중복을 없애고, 좌표를 위도·경도로 바꾼다."""
    transformer = Transformer.from_crs("EPSG:5174", "EPSG:4326", always_xy=True)

    result = []
    seen = set()
    no_coord = 0
    for row in read_csv("hospital"):
        if row["영업상태명"] != "영업/정상":
            continue

        address = row["도로명주소"].strip()
        if address == "":
            address = row["지번주소"].strip()
        region = region_from_address(address)
        if region not in regions:
            continue

        key = (row["사업장명"], address)
        if key in seen:
            continue
        seen.add(key)

        item = {"name": clean_name(row["사업장명"]), "sido": region[0], "city": region[1],
                "address": address,
                "phone": row["전화번호"].strip(), "lat": None, "lon": None}

        x = row["좌표정보(X)"].strip()
        y = row["좌표정보(Y)"].strip()
        if x and y:
            lon, lat = transformer.transform(float(x), float(y))
            if valid_coord(lat, lon):
                item["lat"] = round(lat, 6)
                item["lon"] = round(lon, 6)
        if item["lat"] is None:
            no_coord += 1

        result.append(item)

    print(f"  병원 중 좌표 없음: {no_coord}건 (개수에는 포함, 지도에는 안 찍힘)")
    return result


# ---------- 동반시설 ----------
def clean_facility(regions):
    """카페·여행지·박물관 등 반려동물과 같이 갈 수 있는 곳만 남긴다."""
    result = []
    seen = set()
    for row in read_csv("facility"):
        if row["시도 명칭"] not in config.SIDO_LIST:
            continue
        if row["카테고리2"] not in config.FACILITY_CATEGORIES:
            continue

        region = (row["시도 명칭"], row["시군구 명칭"].split()[0])
        if region not in regions:
            continue

        key = (row["시설명"], row["도로명주소"])
        if key in seen:
            continue
        seen.add(key)

        try:
            lat, lon = float(row["위도"]), float(row["경도"])
        except ValueError:
            continue
        if not valid_coord(lat, lon):
            continue

        result.append({"name": clean_name(row["시설명"]), "type": row["카테고리3"],
                       "sido": region[0], "city": region[1],
                       "address": row["도로명주소"], "hours": row["운영시간"],
                       "indoor": row["장소(실내) 여부"], "outdoor": row["장소(실외)여부"],
                       "parking": row["주차 가능여부"], "lat": lat, "lon": lon})
    return result


# ---------- 공원 ----------
def clean_park(regions):

    result = []
    seen = set()
    for row in read_csv("park"):
        region = region_from_address(row["제공기관명"])
        if region not in regions:
            continue

        key = (row["공원명"], row["위도"], row["경도"])
        if key in seen:
            continue
        seen.add(key)

        try:
            lat, lon = float(row["위도"]), float(row["경도"])
        except ValueError:
            continue
        if not valid_coord(lat, lon):
            continue

        try:
            area = float(row["공원면적"].replace(",", ""))
        except ValueError:
            area = None

        result.append({"name": clean_name(row["공원명"]), "type": row["공원구분"].replace(" ", ""),
                       "sido": region[0], "city": region[1], "area": area, "lat": lat, "lon": lon})
    return result


def main():
    print("전처리 시작")

    registration = clean_registration()
    save("registration", registration)

    regions = set()
    for row in registration:
        regions.add((row["sido"], row["city"]))

    save("hospital", clean_hospital(regions))
    save("facility", clean_facility(regions))
    save("park", clean_park(regions))

    print("전처리 끝")


if __name__ == "__main__":
    main()
