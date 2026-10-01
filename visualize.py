import os

import folium
import matplotlib
matplotlib.use("Agg")  # 창을 띄우지 않고 파일로만 저장
import matplotlib.pyplot as plt
from folium.plugins import MarkerCluster

import storage

CHART_DIR = "static/charts"

# 한글이 깨지지 않게 윈도우 기본 글꼴(맑은 고딕)을 쓴다
plt.rcParams["font.family"] = "Malgun Gothic"
plt.rcParams["axes.unicode_minus"] = False

# 그래프로 그릴 지표: (stats의 키, 제목, 파일 이름)
CHARTS = [
    ("hospitals", "시·군·구별 동물병원 수", "hospitals.png"),
    ("registered", "시·군·구별 등록동물 수 (2022년 말 기준)", "registered.png"),
    ("hospitals_per_10k_pets", "등록동물 1만 마리당 동물병원 수", "hospitals_per_pets.png"),
    ("facilities_per_10k_pets", "등록동물 1만 마리당 동반시설 수", "facilities_per_pets.png"),
]

SIDO_COLORS = {"서울특별시": "#4F6BED", "경기도": "#19A974"}

TOP_N = 10


def draw_bars(ax, regions, key, subtitle, max_value):
    """그래프 한 칸(ax)에 가로 막대를 그린다. regions의 첫 번째가 맨 위에 온다."""
    names = []
    values = []
    colors = []
    for s in regions:
        names.append(s["city"])
        values.append(s[key])
        colors.append(SIDO_COLORS.get(s["sido"], "#999999"))

    ax.barh(names, values, color=colors, height=0.68)
    ax.invert_yaxis()
    ax.set_xlim(0, max_value * 1.18)
    ax.set_title(subtitle, fontsize=12, loc="left", color="#6B645C")

    for i in range(len(values)):
        ax.text(values[i], i, f"  {values[i]:,}", va="center", fontsize=10, color="#2B2A28")

    for side in ["top", "right", "bottom", "left"]:
        ax.spines[side].set_visible(False)
    ax.set_xticks([])
    ax.tick_params(axis="y", length=0, labelsize=11)


def bar_chart(stats, key, title, filename):
    """값이 큰 10곳과 작은 10곳을 나란히 그려 저장한다. 막대 색으로 시도를 구분한다."""
    def value_of(s):
        return s[key]

    ranked = sorted(stats, key=value_of, reverse=True)
    top = ranked[:TOP_N]
    bottom = ranked[-TOP_N:]
    max_value = ranked[0][key]

    fig, (left, right) = plt.subplots(1, 2, figsize=(11, 5.2))
    draw_bars(left, top, key, f"높은 {TOP_N}곳", max_value)
    draw_bars(right, bottom, key, f"낮은 {TOP_N}곳", max_value)
    fig.suptitle(title, fontsize=15, fontweight="bold", x=0.02, ha="left")

    for sido, color in SIDO_COLORS.items():
        right.barh(0, 0, color=color, label=sido)
    right.legend(loc="lower right", frameon=False, fontsize=10)

    fig.tight_layout()
    fig.savefig(f"{CHART_DIR}/{filename}", dpi=120, facecolor="white")
    plt.close(fig)


def count_of(item):
    """정렬 기준: (종류, 개수) 묶음에서 개수."""
    return item[1]


def type_chart(facilities):
    """동반시설 종류별 개수를 가로 막대그래프로 그린다."""
    counts = {}
    for f in facilities:
        counts[f["type"]] = counts.get(f["type"], 0) + 1
    items = sorted(counts.items(), key=count_of, reverse=True)

    names = []
    sizes = []
    for name, count in items:
        names.append(name)
        sizes.append(count)

    fig, ax = plt.subplots(figsize=(11, 3.6))
    ax.barh(names, sizes, color="#FF8A3D", height=0.62)
    ax.invert_yaxis()
    ax.set_xlim(0, sizes[0] * 1.15)
    total = sum(sizes)
    for i in range(len(sizes)):
        percent = round(sizes[i] / total * 100)
        ax.text(sizes[i], i, f"  {sizes[i]:,}곳 ({percent}%)", va="center", fontsize=10, color="#2B2A28")
    for side in ["top", "right", "bottom", "left"]:
        ax.spines[side].set_visible(False)
    ax.set_xticks([])
    ax.tick_params(axis="y", length=0, labelsize=11)
    fig.suptitle("동반시설 종류별 개수", fontsize=15, fontweight="bold", x=0.02, ha="left")
    fig.tight_layout()
    fig.savefig(f"{CHART_DIR}/facility_types.png", dpi=120, facecolor="white")
    plt.close(fig)


def scatter_chart(stats):
    """등록동물 수와 시설 수의 관계를 점으로 찍는다. 점 하나가 시·군·구 하나."""
    fig, (left, right) = plt.subplots(1, 2, figsize=(11, 4.8))

    panels = [
        (left, "hospitals", "동물병원 수"),
        (right, "facilities", "동반시설 수"),
    ]
    for ax, key, label in panels:
        for s in stats:
            ax.scatter(s["registered"], s[key], color=SIDO_COLORS.get(s["sido"], "#999999"),
                       s=46, alpha=0.8)

        def value_of(s):
            return s[key]

        offsets = [(6, 8), (-40, 8)]
        top = sorted(stats, key=value_of, reverse=True)[:2]
        for i in range(len(top)):
            ax.annotate(top[i]["city"], (top[i]["registered"], top[i][key]), xytext=offsets[i],
                        textcoords="offset points", fontsize=9, color="#2B2A28")
        ax.margins(0.12)
        ax.set_xlabel("등록동물 수 (마리)", fontsize=10, color="#6B645C")
        ax.set_title(label, fontsize=12, loc="left", color="#6B645C")
        ax.grid(color="#EDE6DC", linewidth=0.8)
        ax.set_axisbelow(True)
        for side in ["top", "right"]:
            ax.spines[side].set_visible(False)
        for side in ["bottom", "left"]:
            ax.spines[side].set_color("#EDE6DC")
        ax.tick_params(length=0, labelsize=9)

    fig.suptitle("등록동물이 많은 곳에 시설도 많을까", fontsize=15, fontweight="bold", x=0.02, ha="left")
    for sido, color in SIDO_COLORS.items():
        right.scatter([], [], color=color, label=sido)
    fig.legend(loc="upper right", ncol=2, frameon=False, fontsize=10)
    fig.tight_layout()
    fig.savefig(f"{CHART_DIR}/scatter.png", dpi=120, facecolor="white")
    plt.close(fig)


def make_map(hospitals, facilities, parks):
    """병원·동반시설·공원을 찍은 지도를 만든다. 오른쪽 위에서 종류별로 켜고 끌 수 있다."""
    points = []
    for p in hospitals + facilities + parks:
        if p["lat"] is not None:
            points.append(p)

    lat_sum = 0
    lon_sum = 0
    for p in points:
        lat_sum += p["lat"]
        lon_sum += p["lon"]
    center = [lat_sum / len(points), lon_sum / len(points)]

    if len(points) > 1500:
        zoom = 10
    else:
        zoom = 12
    m = folium.Map(location=center, zoom_start=zoom)

    layers = [
        ("동물병원", hospitals, "red", "stethoscope"),
        ("동반시설", facilities, "orange", "paw"),
        ("공원", parks, "green", "tree"),
    ]
    for label, rows, color, icon in layers:
        group = MarkerCluster(name=f"{label} ({len(rows)})").add_to(m)
        for row in rows:
            if row["lat"] is None:
                continue
            text = row["name"]
            if "type" in row:
                text += f" · {row['type']}"
            folium.Marker([row["lat"], row["lon"]], tooltip=text,
                          icon=folium.Icon(color=color, icon=icon, prefix="fa")).add_to(group)

    folium.LayerControl(collapsed=False).add_to(m)
    return m


def main():
    os.makedirs(CHART_DIR, exist_ok=True)
    stats = storage.load("stats")

    for key, title, filename in CHARTS:
        bar_chart(stats, key, title, filename)
    type_chart(storage.load("facility"))
    scatter_chart(stats)
    print(f"그래프 {len(CHARTS) + 2}장 저장 -> {CHART_DIR}")

    m = make_map(storage.load("hospital"), storage.load("facility"), storage.load("park"))
    m.save("static/map_all.html")
    print("전체 지도 저장 -> static/map_all.html")


if __name__ == "__main__":
    main()
