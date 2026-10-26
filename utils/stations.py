
from pathlib import Path

import pandas as pd
import streamlit as st


# 프로젝트 최상위 폴더의 data 폴더
BASE_DIR = Path(__file__).resolve().parent.parent
COORDINATE_FILE = BASE_DIR / "data" / "station_coordinates.csv"


@st.cache_data(ttl=86400)
def get_station_coordinates():
    """CSV 파일에서 전국 측정소별 위도와 경도를 가져온다."""

    if not COORDINATE_FILE.exists():
        raise RuntimeError(
            f"측정소 좌표 파일을 찾을 수 없어: {COORDINATE_FILE}"
        )

    # 공공데이터 CSV가 CP949로 저장된 경우도 처리
    try:
        df = pd.read_csv(COORDINATE_FILE, encoding="cp949")
    except UnicodeDecodeError:
        df = pd.read_csv(COORDINATE_FILE, encoding="utf-8-sig")

    required_columns = {"측정소명", "경도", "위도"}

    if not required_columns.issubset(df.columns):
        raise RuntimeError(
            "CSV에 필요한 열이 없어. 필요한 열: 측정소명, 경도, 위도. "
            f"현재 열: {list(df.columns)}"
        )

    coordinates = {}

    for _, row in df.iterrows():
        station = str(row["측정소명"]).strip()

        try:
            lon = float(row["경도"])
            lat = float(row["위도"])
        except (ValueError, TypeError):
            continue

        if station and -90 <= lat <= 90 and -180 <= lon <= 180:
            coordinates[station] = (lat, lon)

    if not coordinates:
        raise RuntimeError("CSV 파일에서 유효한 측정소 좌표를 찾지 못했어.")

    return coordinates
