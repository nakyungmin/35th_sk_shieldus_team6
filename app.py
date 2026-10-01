import os

from flask import Flask, abort, render_template, request

import config
import storage
import visualize

app = Flask(__name__)


@app.context_processor
def common():
    """모든 화면에서 쓰는 값: 지역 이름, 지역 선택 목록."""
    return {"region_name": config.REGION_NAME, "sido_list": config.SIDO_LIST,
            "all_stats": storage.load("stats")}


def find_region(stats, sido, name):
    for s in stats:
        if s["sido"] == sido and s["city"] == name:
            return s
    return None


@app.route("/")
def index():
    """첫 화면: 전체 지도와 합계."""
    stats = storage.load("stats")
    total = {}
    for key in ["hospitals", "facilities", "parks", "registered"]:
        total[key] = 0
        for s in stats:
            total[key] += s[key]
    return render_template("index.html", total=total)


@app.route("/city/<sido>/<name>")
def city(sido, name):
    """지역 검색: 시·군·구 하나의 인프라 현황."""
    stats = storage.load("stats")
    info = find_region(stats, sido, name)
    if info is None:
        abort(404)

    # 지표별로 전체 시·군·구 중 몇 등인지 계산
    ranks = {}
    for key in ["hospitals_per_10k_pets", "facilities_per_10k_pets"]:
        def value_of(s):
            return s[key]

        ordered = sorted(stats, key=value_of, reverse=True)
        ranks[key] = ordered.index(info) + 1

    return render_template("city.html", info=info, ranks=ranks, total_regions=len(stats),
                           facilities=storage.load("facility", sido, name))


@app.route("/map/<sido>/<name>")
def city_map(sido, name):
    """시·군·구 하나만 찍은 지도 (city.html 안에 끼워 넣는다)."""
    if find_region(storage.load("stats"), sido, name) is None:
        abort(404)
    m = visualize.make_map(storage.load("hospital", sido, name),
                           storage.load("facility", sido, name),
                           storage.load("park", sido, name))
    return m.get_root().render()


# 지역 비교 표에서 정렬할 수 있는 항목: stats의 키와 표에 적을 이름
SORT_COLUMNS = {
    "registered": "등록동물",
    "hospitals": "동물병원",
    "facilities": "동반시설",
    "parks": "공원",
    "hospitals_per_10k_pets": "등록동물 1만 마리당 병원",
    "facilities_per_10k_pets": "등록동물 1만 마리당 동반시설",
}


@app.route("/compare")
def compare():
    """지역별 비교: 그래프와 표. 표는 고른 항목이 큰 지역부터(내림차순) 보여 준다."""
    stats = storage.load("stats")

    sort = request.args.get("sort", "registered")
    if sort not in SORT_COLUMNS:
        sort = "registered"

    def value_of(s):
        return s[sort]

    stats = sorted(stats, key=value_of, reverse=True)
    return render_template("compare.html", stats=stats, charts=visualize.CHARTS,
                           columns=SORT_COLUMNS, sort=sort)


if __name__ == "__main__":
    app.run(debug=True, port=int(os.environ.get("PORT", 5000)))
