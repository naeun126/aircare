"""측정소 이름으로 위도·경도를 찾기 위한 좌표 데이터를 불러오는 모듈.

2페이지(대기질 분석)의 지도에서 측정소 위치를 표시할 때 사용한다.
"""

from pathlib import Path

import pandas as pd
import streamlit as st


# 프로젝트 최상위 폴더의 data 폴더.
# __file__은 이 파일(utils/stations.py)의 위치이다.
# .parent를 두 번 쓰면 utils 폴더 -> 프로젝트 최상위 폴더로 올라간다.
# 이렇게 하면 앱을 어느 위치에서 실행해도 CSV 파일을 올바르게 찾을 수 있다.
BASE_DIR = Path(__file__).resolve().parent.parent
COORDINATE_FILE = BASE_DIR / "data" / "station_coordinates.csv"


# 결과를 하루(86400초) 동안 저장해 둔다.
# 페이지가 다시 그려질 때마다 CSV를 새로 읽지 않아 속도가 빨라진다.
@st.cache_data(ttl=86400)
def get_station_coordinates():
    """CSV 파일에서 전국 측정소별 위도와 경도를 가져온다.

    반환값은 {측정소 이름: (위도, 경도)} 형태의 딕셔너리이다.
    """

    # [예외 처리 1] 좌표 파일이 없는 경우
    if not COORDINATE_FILE.exists():
        raise RuntimeError(
            f"측정소 좌표 파일을 찾을 수 없습니다: {COORDINATE_FILE}"
        )

    # 공공데이터 CSV가 CP949(한글 윈도우 인코딩)로 저장된 경우도 처리한다.
    # 먼저 cp949로 읽어 보고, 글자가 깨져 읽을 수 없으면 utf-8-sig로 다시 읽는다.
    try:
        df = pd.read_csv(COORDINATE_FILE, encoding="cp949")
    except UnicodeDecodeError:
        df = pd.read_csv(COORDINATE_FILE, encoding="utf-8-sig")

    # [예외 처리 2] 꼭 필요한 열이 모두 있는지 확인한다.
    required_columns = {"측정소명", "경도", "위도"}

    if not required_columns.issubset(df.columns):
        raise RuntimeError(
            "CSV에 필요한 열이 없습니다. 필요한 열: 측정소명, 경도, 위도. "
            f"현재 열: {list(df.columns)}"
        )

    # 측정소 이름 -> (위도, 경도)
    coordinates = {}

    # CSV의 각 줄(측정소 한 곳)을 차례로 확인한다.
    for _, row in df.iterrows():
        # 이름 앞뒤의 공백을 제거해야 API의 측정소 이름과 정확히 비교할 수 있다.
        station = str(row["측정소명"]).strip()

        # 위도·경도가 숫자가 아니거나 비어 있는 줄은 건너뛴다.
        try:
            lon = float(row["경도"])
            lat = float(row["위도"])
        except (ValueError, TypeError):
            continue

        # 이름이 있고, 위도(-90~90)와 경도(-180~180)가 올바른 범위일 때만 저장한다.
        if station and -90 <= lat <= 90 and -180 <= lon <= 180:
            coordinates[station] = (lat, lon)

    # [예외 처리 3] 유효한 좌표가 하나도 없는 경우
    if not coordinates:
        raise RuntimeError("CSV 파일에서 유효한 측정소 좌표를 찾지 못했습니다.")

    return coordinates
