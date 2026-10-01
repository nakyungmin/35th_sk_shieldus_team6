# 2단계: 시·군·구별 지표를 계산해 CSV, JSON, MongoDB에 저장한다.
# 실행: python analyze.py

import csv
import json
import math

import config
import storage


def region_key(row):
    """(시도, 시·군·구). 이름이 같은 구(중구 등)를 구분하려고 시도까지 묶는다."""
    return (row["sido"], row["city"])


def count_by_region(rows):
    counts = {}
    for row in rows:
        key = region_key(row)
        counts[key] = counts.get(key, 0) + 1
    return counts


def per_10000(count, base):
    """base 1만당 count."""
    if base == 0:
        return 0
    return round(count / base * 10000, 2)


def correlation(xs, ys):
    """피어슨 상관계수 (-1 ~ 1)."""
    n = len(xs)
    mean_x = sum(xs) / n
    mean_y = sum(ys) / n

    top = 0
    spread_x = 0
    spread_y = 0
    for i in range(n):
        top += (xs[i] - mean_x) * (ys[i] - mean_y)
        spread_x += (xs[i] - mean_x) ** 2
        spread_y += (ys[i] - mean_y) ** 2
    return round(top / math.sqrt(spread_x * spread_y), 2)


def print_summary(stats):
    """발표용 요약: 상관계수와 시도별 지표."""
    registered = []
    hospitals = []
    facilities = []
    for s in stats:
        registered.append(s["registered"])
        hospitals.append(s["hospitals"])
        facilities.append(s["facilities"])

    print()
    print("[상관계수] 등록동물 수와 얼마나 같이 늘어나는가")
    print("  동물병원 수:", correlation(registered, hospitals))
    print("  동반시설 수:", correlation(registered, facilities))

    print()
    print("[시도별 합계로 계산한 지표]")
    for sido in config.SIDO_LIST:
        pets = 0
        n_hospital = 0
        n_facility = 0
        for s in stats:
            if s["sido"] == sido:
                pets += s["registered"]
                n_hospital += s["hospitals"]
                n_facility += s["facilities"]
        print(f"  {sido}: 등록동물 1만 마리당 병원 {per_10000(n_hospital, pets)}"
              f" / 등록동물 1만 마리당 동반시설 {per_10000(n_facility, pets)}")


def sido_then_city(s):
    return (s["sido"], s["city"])


def main():
    registration = storage.load("registration")
    hospitals = storage.load("hospital")
    facilities = storage.load("facility")
    parks = storage.load("park")

    hospital_count = count_by_region(hospitals)
    facility_count = count_by_region(facilities)
    park_count = count_by_region(parks)

    # 동물등록 자료의 지역 목록이 기준
    stats = []
    for reg in registration:
        key = region_key(reg)
        n_hospital = hospital_count.get(key, 0)
        n_facility = facility_count.get(key, 0)
        n_park = park_count.get(key, 0)

        stats.append({
            "sido": reg["sido"],
            "city": reg["city"],
            "registered": reg["registered"],
            "dogs": reg["dogs"],
            "cats": reg["cats"],
            "hospitals": n_hospital,
            "facilities": n_facility,
            "parks": n_park,
            "hospitals_per_10k_pets": per_10000(n_hospital, reg["registered"]),
            "facilities_per_10k_pets": per_10000(n_facility, reg["registered"]),
        })

    stats.sort(key=sido_then_city)

    with open(f"{config.PROCESSED_DIR}/stats.json", "w", encoding="utf-8") as f:
        json.dump(stats, f, ensure_ascii=False, indent=1)
    with open(f"{config.PROCESSED_DIR}/stats.csv", "w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(stats[0].keys()))
        writer.writeheader()
        writer.writerows(stats)

    if storage.save_one("stats", stats):
        print(f"지표 계산 끝: {len(stats)}개 시·군·구 저장 (CSV, JSON, MongoDB)")
    else:
        print(f"지표 계산 끝: {len(stats)}개 시·군·구 저장 (CSV, JSON) - MongoDB에 연결하지 못해 파일로만 저장")

    # 지표별 상위 5곳, 하위 3곳 출력
    for key, label in [("hospitals_per_10k_pets", "등록동물 1만 마리당 병원"),
                       ("facilities_per_10k_pets", "등록동물 1만 마리당 동반시설")]:
        def value_of(s):
            return s[key]

        ranked = sorted(stats, key=value_of, reverse=True)
        print(f"\n[{label}] 많은 곳 / 적은 곳")
        for s in ranked[:5]:
            print(f"  {s['sido'][:2]} {s['city']:6} {s[key]}")
        print("  ...")
        for s in ranked[-3:]:
            print(f"  {s['sido'][:2]} {s['city']:6} {s[key]}")

    print_summary(stats)


if __name__ == "__main__":
    main()
