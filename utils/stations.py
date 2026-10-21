
import requests
import streamlit as st


@st.cache_data(ttl=86400)
def get_station_coordinates(service_key):
    """에어코리아 측정소 목록에서 측정소별 위도·경도를 가져온다."""

    url = (
        "https://apis.data.go.kr/"
        "B552584/MsrstnInfoInqireSvc/getMsrstnList"
    )

    params = {
        "serviceKey": service_key,
        "returnType": "json",
        "numOfRows": 1000,
        "pageNo": 1,
    }

    try:
        response = requests.get(
            url,
            params=params,
            timeout=15,
        )
        response.raise_for_status()
        result = response.json()

    except (requests.RequestException, ValueError) as e:
        raise RuntimeError(
            f"측정소 위치 정보를 가져오지 못했어: {e}"
        ) from e

    body = result.get("response", {}).get("body", {})
    header = result.get("response", {}).get("header", {})

    if str(header.get("resultCode", "00")) != "00":
        raise RuntimeError(
            "에어코리아 API 오류: "
            + str(header.get("resultMsg", "원인을 확인할 수 없음"))
        )

    items = body.get("items", [])

    # API 응답이 목록 또는 딕셔너리로 오는 경우를 모두 처리
    if isinstance(items, dict):
        items = items.get("item", [])

    if isinstance(items, dict):
        items = [items]

    coordinates = {}

    for item in items:
        station = item.get("stationName")
        raw_lat = item.get("dmX")
        raw_lon = item.get("dmY")

        if not station or raw_lat is None or raw_lon is None:
            continue

        try:
            lat = float(raw_lat)
            lon = float(raw_lon)
        except (TypeError, ValueError):
            continue

        # 유효한 위도·경도만 등록
        if -90 <= lat <= 90 and -180 <= lon <= 180:
            coordinates[station.strip()] = (lat, lon)

    if not coordinates:
        raise RuntimeError(
            "측정소 좌표가 없어. API 응답과 서비스 키를 확인해 줘."
        )

    return coordinates
