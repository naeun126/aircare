import pandas as pd
import pydeck as pdk
import streamlit as st

# utils/analysis.py: 평균, 최댓값, 최솟값, 변화 추세를 계산하는 함수
from utils.analysis import (
    calculate_average,
    calculate_max,
    calculate_min,
    calculate_trend,
)
# utils/grade.py: 물질별 등급 기준값 (좋음/보통/나쁨 경계)
from utils.grade import GRADE_LIMITS
# utils/stations.py: 측정소 이름으로 위도·경도를 찾는 함수
from utils.stations import get_station_coordinates


# ========================================
# 세션 상태 초기화
# ========================================
# 1페이지를 거치지 않고 이 페이지로 바로 들어와도 오류가 나지 않도록
# 필요한 값을 미리 만들어 둔다. 이미 있으면 덮어쓰지 않는다.

if "air_data" not in st.session_state:
    st.session_state.air_data = []

if "history" not in st.session_state:
    st.session_state.history = {}

if "selected_sido" not in st.session_state:
    st.session_state.selected_sido = "서울"


st.title("📊 대기질 분석")

# 1페이지에서 마지막으로 "조회한" 지역을 가져온다.
# air_data_sido가 있으면 그것을 쓰고, 없으면 선택만 한 지역, 그것도 없으면 서울을 쓴다.
# str(...).strip()은 값이 문자열이 아니거나 앞뒤에 공백이 있어도 안전하게 비교하기 위함이다.
selected_sido = str(
    st.session_state.get(
        "air_data_sido",
        st.session_state.get("selected_sido", "서울")
    )
).strip()

st.caption(f"📍 현재 선택 지역: **{selected_sido}**")

# ========================================
# 선택 지역 데이터 가져오기
# ========================================

# 1페이지에서 저장한 전체 측정소 데이터
all_data = st.session_state.get("air_data", [])

# [예외 처리] 아직 데이터를 조회하지 않았으면 안내 후 이 페이지의 실행을 멈춘다.
if not all_data:
    st.warning(
        "측정 데이터가 없습니다. "
        "1페이지에서 지역을 선택한 뒤 데이터를 먼저 조회해 주세요."
    )
    st.stop()


# 각 측정소 데이터가 어느 시도에 속하는지 알아내는 함수.
# 우선 1페이지에서 저장한 _selectedSido를 사용하고,
# 없으면 API 응답의 sidoName을 사용한다.
def get_record_sido(record):
    value = record.get("_selectedSido")
    if value is None or not str(value).strip():
        value = record.get("sidoName")
    # 둘 다 없으면 빈 문자열을 돌려준다.
    return str(value or "").strip()


# 지역 정보가 하나라도 있는 데이터만 모은다.
records_with_region = [
    record for record in all_data if get_record_sido(record)
]

if records_with_region:
    # 지역 정보가 있는 데이터는 선택 지역과 정확히 일치하는 것만 사용한다.
    data = [
        record
        for record in all_data
        if get_record_sido(record) == selected_sido
    ]

    # 선택 지역과 일치하는 데이터가 하나도 없는 경우
    # (예: 부산 데이터를 조회한 뒤 선택 지역만 서울로 바꾼 경우)
    if not data:
        # 지금 저장된 데이터가 어느 지역 것인지 보여 주기 위해 지역 목록을 만든다.
        available_regions = sorted(
            {get_record_sido(record) for record in records_with_region}
        )
        st.warning(
            f"{selected_sido} 지역의 데이터가 없습니다. "
            "1페이지에서 해당 지역을 선택하고 데이터를 다시 조회해 주세요."
        )
        st.caption(
            "현재 데이터에 기록된 지역: " + ", ".join(available_regions)
        )
        st.stop()
else:
    # 일부 API 응답에는 sidoName이 없을 수 있다.
    # 이 경우 1페이지에서 선택 지역을 조회해 받아온 데이터이므로
    # 전체 데이터를 사용하되, 사용자가 상황을 알 수 있도록 안내한다.
    data = all_data
    st.info(
        "API 응답에 시도 정보가 없어 지역별 추가 필터링은 할 수 없습니다. "
        "1페이지에서 선택한 지역으로 조회한 데이터를 표시합니다."
    )


# ========================================
# 대기오염물질 분석
# ========================================

# 화면에 보여 줄 물질 이름과 API 응답의 항목 이름(키)을 연결한 표.
# 이 이름은 utils/grade.py의 GRADE_LIMITS 키와 같아야 등급 기준을 찾을 수 있다.
column_map = {
    "PM10": "pm10Value",
    "PM2.5": "pm25Value",
    "오존(O₃)": "o3Value",
    "이산화질소(NO₂)": "no2Value",
    "일산화탄소(CO)": "coValue",
    "아황산가스(SO₂)": "so2Value",
}

# 분석할 물질을 사용자가 고른다.
selected_name = st.selectbox(
    "분석할 대기오염물질을 선택하세요.",
    list(column_map.keys()),
)

# 고른 물질의 API 항목 이름 (예: "PM10" -> "pm10Value")
column = column_map[selected_name]

# utils/analysis.py의 함수로 통계를 계산한다.
# 유효한 측정값이 하나도 없으면 None이 돌아온다.
average = calculate_average(data, column)
maximum = calculate_max(data, column)
minimum = calculate_min(data, column)
trend = calculate_trend(data, column)

st.subheader(f"📈 {selected_name} 분석")

# 통계값 4개를 한 줄에 나란히 보여 준다.
col1, col2, col3, col4 = st.columns(4)


# None이면 계산할 수 없다는 뜻이므로 "-"로 표시한다.
# 숫자는 소수점 둘째 자리까지 보여 준다.
with col1:
    st.metric(
        "평균 농도",
        f"{average:.2f}" if average is not None else "-"
    )

with col2:
    st.metric(
        "최고 농도",
        f"{maximum:.2f}" if maximum is not None else "-"
    )

with col3:
    st.metric(
        "최저 농도",
        f"{minimum:.2f}" if minimum is not None else "-"
    )

with col4:
    st.metric("변화 추세", trend if trend is not None else "-")

# ----------------------------------------
# 측정소별 농도 막대그래프용 데이터 만들기
# ----------------------------------------
station_values = []

for record in data:
    station = record.get("stationName", "알 수 없는 측정소")
    raw_value = record.get(column)

    # API는 측정값이 없을 때 "-" 같은 문자열을 주므로 숫자로 바꿀 수 있는지 확인한다.
    # 바꿀 수 없으면(None, "-" 등) 이 측정소는 건너뛴다.
    try:
        value = float(raw_value)
    except (TypeError, ValueError):
        continue

    # 음수는 비정상 측정값(장비 오류 등)이므로 제외한다.
    if value < 0:
        continue

    station_values.append({
        "측정소": station,
        "농도": value,
    })

# 리스트를 표(DataFrame)로 바꾼다.
station_df = pd.DataFrame(station_values)

if not station_df.empty:
    st.subheader(f"📊 측정소별 {selected_name} 농도")
    # 측정소 이름을 가로축, 농도를 세로축으로 하는 막대그래프
    st.bar_chart(station_df.set_index("측정소")["농도"])
else:
    st.warning("표시할 측정소별 농도 데이터가 없습니다.")

# ----------------------------------------
# 지도에 표시할 점(측정소) 만들기
# ----------------------------------------

# 측정소 이름 -> (위도, 경도) 사전. data/station_coordinates.csv에서 읽어 온다.
station_coordinates = get_station_coordinates()
map_points = []

# 선택한 물질의 등급 기준값 (좋음 상한, 보통 상한, 나쁨 상한)
limits = GRADE_LIMITS.get(selected_name)

# 등급 기준이 없는 물질이면 색을 정할 수 없으므로 지도를 그리지 않고 멈춘다.
# 현재는 6개 물질 모두 기준이 있어 실행되지 않는 안전장치이다.
if limits is None:
    st.info(
        f"{selected_name}은(는) 지도에 사용할 등급 기준이 없어 "
        "지도를 표시하지 않습니다."
    )
    st.stop()

map_pollutant = selected_name

# 측정소별로 지도에 찍을 점의 정보를 만든다.
for _, row in station_df.iterrows():
    station = row["측정소"]
    value = row["농도"]

    # 좌표 파일에 없는 측정소는 위치를 알 수 없으므로 건너뛴다.
    if station not in station_coordinates:
        continue

    # 값이 비어 있거나 음수이면 건너뛴다.
    if not pd.notna(value) or value < 0:
        continue

    lat, lon = station_coordinates[station]

    # 농도를 기준값과 비교해 등급과 점의 색(RGB)을 정한다.
    if value <= limits[0]:
        color = [46, 157, 80]      # 초록: 좋음
        grade = "좋음"
    elif value <= limits[1]:
        color = [229, 185, 0]      # 노랑: 보통
        grade = "보통"
    elif value <= limits[2]:
        color = [232, 117, 36]     # 주황: 나쁨
        grade = "나쁨"
    else:
        color = [217, 54, 54]      # 빨강: 매우 나쁨
        grade = "매우 나쁨"

    map_points.append({
        "측정소": station,
        "농도": value,
        "표시값": f"{value:g}",    # 원 안에 쓸 글자 (불필요한 소수점 제거)
        "등급": grade,
        "위도": lat,
        "경도": lon,
        "색상": color,
    })


# ========================================
# 지도 출력
# ========================================

if map_points:
    # 점 정보 리스트를 표로 바꿔 pydeck에 넘긴다.
    map_df = pd.DataFrame(map_points)

    # 레이어 1: 등급 색상의 원
    circle_layer = pdk.Layer(
        "ScatterplotLayer",
        data=map_df,
        get_position="[경도, 위도]",   # 원의 위치
        get_fill_color="색상",         # 원의 색
        get_radius=1000,               # 지도상 반지름(m)
        radius_min_pixels=13,          # 축소해도 최소 13px로 보이게 한다.
        radius_max_pixels=24,          # 확대해도 최대 24px를 넘지 않게 한다.
        pickable=True,                 # 마우스를 올리면 툴팁이 뜨게 한다.
        opacity=0.9,
    )

    # 레이어 2: 원 위에 농도 숫자를 적는 글자 레이어
    text_layer = pdk.Layer(
        "TextLayer",
        data=map_df,
        get_position="[경도, 위도]",
        get_text="표시값",
        get_size=13,
        get_color=[20, 20, 20, 255],
        get_text_anchor="'middle'",
        get_alignment_baseline="'center'",
        get_pixel_offset=[0, 0],
        billboard=True,                # 지도를 돌려도 글자가 항상 정면을 보게 한다.
        pickable=True,
    )

    # 처음 보이는 지도 위치: 표시되는 측정소들의 평균 좌표를 중심으로 한다.
    view = pdk.ViewState(
        latitude=float(map_df["위도"].mean()),
        longitude=float(map_df["경도"].mean()),
        zoom=8,
        pitch=0,                       # 0이면 위에서 내려다보는 평면 지도
    )

    # 두 레이어와 시점, 툴팁을 합쳐 지도를 만든다.
    deck = pdk.Deck(
        layers=[circle_layer, text_layer],
        initial_view_state=view,
        tooltip={
            # {측정소}, {농도}, {등급}은 map_df의 열 이름이다.
            "html": (
                "<b>측정소:</b> {측정소}<br/>"
                f"<b>{map_pollutant}:</b> {{농도}}<br/>"
                "<b>참고 등급:</b> {등급}"
            ),
            "style": {
                "backgroundColor": "white",
                "color": "black",
            },
        },
        map_style=None,                # 별도 지도 키 없이 기본 스타일을 사용한다.
    )

    st.pydeck_chart(deck, use_container_width=True)

    st.caption(
        f"원 안의 숫자는 {map_pollutant} 농도입니다. "
        "원에 마우스를 올리면 측정소와 참고 등급을 확인할 수 있습니다."
    )

    # 지도에 표시된 측정소를 표로도 확인할 수 있게 접이식 영역에 넣는다.
    with st.expander("지도에 표시된 측정소 확인"):
        display_df = map_df[
            ["측정소", "농도", "등급"]
        ].rename(
            columns={
                "측정소": "측정소 이름",
                "농도": f"{map_pollutant} 농도",
                "등급": "참고 등급",
            }
        )

        st.dataframe(
            display_df,
            use_container_width=True,
            hide_index=True,
        )
else:
    # 좌표가 있는 측정소가 하나도 없거나 유효한 값이 없을 때의 안내
    st.warning(
        f"{selected_sido} 지역에서 지도에 표시할 측정소가 없습니다. "
        "측정소 이름과 좌표 파일에 해당 측정소가 있는지 확인해 주세요."
    )

st.caption(
    "색상 구간은 참고용이며 공식 대기질 등급과 다를 수 있습니다."
)
