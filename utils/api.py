"""에어코리아(한국환경공단) 공공데이터 API를 호출하는 함수 모음.

- get_air_quality_data: 시도별 실시간 측정소 대기질 조회 (1페이지에서 사용)
- get_air_quality_forecast: 미세먼지 공식 예보 조회 (3페이지에서 사용)

두 함수 모두 오류가 나면 아래 두 종류의 예외를 발생시킨다.
- ConnectionError: 네트워크 연결 실패, HTTP 오류
- ValueError: 인증키 없음, 잘못된 응답 형식, 빈 데이터 등
호출하는 페이지에서 이 예외를 잡아 st.error로 사용자에게 안내한다.
"""

import urllib.request
import urllib.parse
import urllib.error
import json

# 시도별 실시간 측정정보 조회 API 주소 (에어코리아 대기오염정보 서비스)
API_URL = (
    "https://apis.data.go.kr/"
    "B552584/ArpltnInforInqireSvc/"
    "getCtprvnRltmMesureDnsty"
)

def get_air_quality_data(service_key, sido_name):
    """시도 이름(예: '서울')을 받아 그 지역 측정소들의 실시간 측정값 목록을 반환한다."""

    # [예외 처리] 인증키가 비어 있으면 API를 호출하지 않고 바로 오류를 낸다.
    if not service_key:
        raise ValueError("공공데이터 API 인증키가 설정되지 않았습니다.")

    # 공공데이터포털의 인증키는 URL 인코딩된 형태로 발급되는 경우가 있다.
    # 아래 urlencode가 한 번 더 인코딩하므로, 먼저 원래 형태로 되돌리고(unquote)
    # 앞뒤 공백도 제거한다. (이중 인코딩으로 인증이 실패하는 것을 막는다.)
    service_key = urllib.parse.unquote(service_key.strip())

    # API에 보낼 요청 변수
    params = {
        "serviceKey": service_key,   # 인증키
        "returnType": "json",        # 응답 형식 (기본값은 xml)
        "numOfRows": 100,            # 한 번에 받을 측정소 수
        "pageNo": 1,                 # 페이지 번호
        "sidoName": sido_name,       # 조회할 시도 이름
        "ver": "1.0",                # API 버전
    }
    # 요청 변수를 "키=값&키=값" 형태로 바꿔 주소 뒤에 붙인다.
    url = f"{API_URL}?{urllib.parse.urlencode(params)}"

    # GET 요청 만들기. 일부 서버는 User-Agent가 없는 요청을 막으므로 함께 보낸다.
    request = urllib.request.Request(
        url,
        headers={
            "User-Agent": "Mozilla/5.0",
            "Accept": "application/json",
        },
        method="GET",
    )

    # [예외 처리] 실제 API 호출
    try:
        # timeout=10: 10초 안에 응답이 없으면 포기한다.
        with urllib.request.urlopen(request, timeout=10) as response:
            data = response.read().decode("utf-8")

    # 서버가 오류 코드(401, 500 등)로 응답한 경우.
    # 원인을 알 수 있도록 응답 본문의 앞 300자를 오류 메시지에 포함한다.
    except urllib.error.HTTPError as error:
        body = error.read().decode("utf-8", errors="replace")[:300]
        raise ConnectionError(
            f"공공데이터 API 오류 (HTTP {error.code}): {body}"
        )

    # 인터넷 연결 끊김, 시간 초과 등 그 밖의 연결 오류
    except Exception as error:
        raise ConnectionError(
            f"공공데이터 API에 연결하지 못했습니다: {error}"
        )

    # [예외 처리] 받은 글자를 JSON(딕셔너리)으로 바꾼다.
    # 인증키 오류 등이 있으면 API가 JSON이 아닌 XML 오류 문서를 줄 수 있다.
    try:
        result = json.loads(data)
    except json.JSONDecodeError:
        raise ValueError(f"JSON이 아닌 응답을 받았습니다: {data[:200]}")

    # 정상 응답은 {"response": {"header": ..., "body": ...}} 구조이다.
    response_data = result.get("response")

    if response_data is None:
        raise ValueError(
            "API 응답에서 데이터를 찾을 수 없습니다."
        )

    # header에는 처리 결과 코드와 메시지가 들어 있다.
    header = response_data.get("header", {})

    result_code = str(
        header.get("resultCode", "")
    )

    result_message = header.get(
        "resultMsg",
        "알 수 없는 오류"
    )

    # 결과 코드가 "00"(또는 "0")이 아니면 API가 요청을 처리하지 못한 것이다.
    if result_code not in ("00", "0"):
        raise ValueError(
            f"API 오류: {result_message}"
        )

    # body의 items에 측정소별 측정값 리스트가 들어 있다.
    body = response_data.get("body", {})
    items = body.get("items", [])

    # [예외 처리] 응답은 정상이지만 데이터가 비어 있는 경우
    if not items:
        raise ValueError(
            "선택한 지역의 대기질 데이터를 찾을 수 없습니다."
        )

    return items


def get_air_quality_forecast(service_key, inform_code="PM25", search_date=None):
    """에어코리아 공식 대기질 예보를 조회한다.

    inform_code: 예보 물질 코드 ("PM10" 또는 "PM25")
    search_date: 발표 기준 날짜 (YYYY-MM-DD). 없으면 오늘 날짜를 사용한다.
    """
    from datetime import date

    # [예외 처리] 인증키가 비어 있으면 API를 호출하지 않는다.
    if not service_key:
        raise ValueError("공공데이터 API 인증키가 설정되지 않았습니다.")

    # 인증키 이중 인코딩 방지 (위 함수와 같은 처리)
    service_key = urllib.parse.unquote(service_key.strip())

    # 미세먼지 예보통보 조회 API 주소
    forecast_url = (
        "https://apis.data.go.kr/"
        "B552584/ArpltnInforInqireSvc/"
        "getMinuDustFrcstDspth"
    )

    # 조회 날짜를 따로 주지 않으면 오늘 날짜를 사용한다.
    if search_date is None:
        search_date = date.today().isoformat()

    # API에 보낼 요청 변수
    params = {
        "serviceKey": service_key,   # 인증키
        "returnType": "json",        # 응답 형식
        "numOfRows": 100,            # 한 번에 받을 예보 수
        "pageNo": 1,                 # 페이지 번호
        "searchDate": search_date,   # 예보 발표 기준 날짜
        "InformCode": inform_code,   # 예보 물질 (PM10 / PM25)
    }

    url = f"{forecast_url}?{urllib.parse.urlencode(params)}"

    request = urllib.request.Request(
        url,
        headers={
            "User-Agent": "Mozilla/5.0",
            "Accept": "application/json",
        },
        method="GET",
    )

    # [예외 처리] 실제 API 호출 (10초 안에 응답이 없으면 포기한다)
    try:
        with urllib.request.urlopen(request, timeout=10) as response:
            raw_data = response.read().decode("utf-8")

    # 서버 오류 코드 응답. "from error"는 원래 오류를 함께 기록해 원인 추적을 쉽게 한다.
    except urllib.error.HTTPError as error:
        body = error.read().decode("utf-8", errors="replace")[:300]
        raise ConnectionError(
            f"공식 예보 API 오류 (HTTP {error.code}): {body}"
        ) from error

    # 연결 실패 등 그 밖의 오류
    except Exception as error:
        raise ConnectionError(
            f"공식 예보 API에 연결하지 못했습니다: {error}"
        ) from error

    # [예외 처리] JSON 변환
    try:
        result = json.loads(raw_data)
    except json.JSONDecodeError as error:
        raise ValueError(
            f"JSON이 아닌 응답을 받았습니다: {raw_data[:200]}"
        ) from error

    # 응답 구조 확인
    response_data = result.get("response")
    if response_data is None:
        raise ValueError("API 응답에서 데이터를 찾을 수 없습니다.")

    # 결과 코드 확인 ("00"이 정상)
    header = response_data.get("header", {})
    result_code = str(header.get("resultCode", ""))

    if result_code not in ("00", "0"):
        raise ValueError(
            f"공식 예보 API 오류: "
            f"{header.get('resultMsg', '알 수 없는 오류')}"
        )

    body = response_data.get("body", {})
    items = body.get("items", [])

    # 결과가 1건이면 리스트가 아닌 딕셔너리로 오는 경우가 있어 리스트로 맞춘다.
    if isinstance(items, dict):
        items = [items]

    # [예외 처리] 아직 발표되지 않았거나 해당 날짜에 예보가 없는 경우
    if not items:
        raise ValueError(
            f"{search_date}의 예보 데이터가 없습니다. "
            "다른 발표 날짜로 다시 조회해 보세요."
        )

    return items
