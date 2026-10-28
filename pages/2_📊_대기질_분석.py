import pandas as pd
import pydeck as pdk
import streamlit as st

from utils.analysis import (
    calculate_average,
    calculate_max,
    calculate_min,
    calculate_trend,
)
from utils.stations import get_station_coordinates


# ========================================
# 세션 상태 초기화
# ========================================

if "air_data" not in st.session_state:
    st.session_state.air_data = []

if "history" not in st.session_state:
    st.session_state.history = {}

if "selected_sido" not in st.session_state:
    st.session_state.selected_sido = "서울"


st.title("📊 대기질 분석")

# 1페이지에서 선택한 지역
selected_sido = str(st.session_state.get("selected_sido", "서울")).strip()
st.caption(f"📍 현재 선택 지역: **{selected_sido}**")


# ========================================
# 선택 지역 데이터 가져오기
# ========================================

all_data = st.session_state.get("air_data", [])

if not all_data:
    st.warning(
        "측정 데이터가 없습니다. "
        "1페이지에서 지역을 선택한 뒤 데이터를 먼저 조회해 주세요."
    )
    st.stop()

# 우선 1페이지에서 저장한 _selectedSido를 사용하고,
# 없으면 API 응답의 sidoName을 사용한다.
def get_record_sido(record):
    value = record.get("_selectedSido")
    if value is None or not str(value).strip():
        value = record.get("sidoName")
    return str(value or "").strip()


records_with_region = [
    record for record in all_data if get_record_sido(record)
]

if records_with_region:
    # 지역 정보가 있는 데이터는 선택 지역과 정확히 일치하는 것만 사용
    data = [
        record
        for record in all_data
        if get_record_sido(record) == selected_sido
    ]

    if not data:
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


    if not pd.notna(value) or value < 0:
        continue

    lat, lon = station_coordinates[station]

    if value <= limits[0]:
        color = [46, 157, 80]
        grade = "좋음"
    elif value <= limits[1]:
        color = [229, 185, 0]
        grade = "보통"
    elif value <= limits[2]:
        color = [232, 117, 36]
        grade = "나쁨"
    else:
        color = [217, 54, 54]
        grade = "매우 나쁨"

    map_points.append({
        "측정소": station,
        "농도": value,
        "표시값": f"{value:g}",
        "등급": grade,
        "위도": lat,
        "경도": lon,
        "색상": color,
    })


# ========================================
# 지도 출력
# ========================================

if map_points:
    map_df = pd.DataFrame(map_points)

    circle_layer = pdk.Layer(
        "ScatterplotLayer",
        data=map_df,
        get_position="[경도, 위도]",
        get_fill_color="색상",
        get_radius=1000,
        radius_min_pixels=13,
        radius_max_pixels=24,
        pickable=True,
        opacity=0.9,
    )

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
        billboard=True,
        pickable=True,
    )

    view = pdk.ViewState(
        latitude=float(map_df["위도"].mean()),
        longitude=float(map_df["경도"].mean()),
        zoom=8,
        pitch=0,
    )

    deck = pdk.Deck(
        layers=[circle_layer, text_layer],
        initial_view_state=view,
        tooltip={
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
        map_style=None,
    )

    st.pydeck_chart(deck, use_container_width=True)

    st.caption(
        f"원 안의 숫자는 {map_pollutant} 농도입니다. "
        "원에 마우스를 올리면 측정소와 참고 등급을 확인할 수 있습니다."
    )

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
    st.warning(
        f"{selected_sido} 지역에서 지도에 표시할 측정소가 없습니다. "
        "측정소 이름과 좌표 파일에 해당 측정소가 있는지 확인해 주세요."
    )

st.caption(
    "색상 구간은 참고용이며 공식 대기질 등급과 다를 수 있습니다."
)
