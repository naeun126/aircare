import urllib.request
import urllib.parse
import json


API_URL = (
    "https://apis.data.go.kr/"
    "B552584/ArpltnInforInqireSvc/"
    "getCtprvnRltmMesureDnsty"
)


def get_air_quality_data(service_key, sido_name):
    """
    선택한 시도의 실시간 대기질 데이터를 가져온다.
    """

    if not service_key:
        raise ValueError(
            "공공데이터 API 인증키가 설정되지 않았습니다."
        )

service_key = urllib.parse.unquote(service_key)

    
    params = {
        "serviceKey": service_key,
        "returnType": "json",
        "numOfRows": 100,
        "pageNo": 1,
        "sidoName": sido_name,
        "ver": "1.0"
    }

    query_string = urllib.parse.urlencode(params)
    url = f"{API_URL}?{query_string}"

    try:
        request = urllib.request.Request(
            url,
            method="GET"
        )

        with urllib.request.urlopen(
            request,
            timeout=10
        ) as response:

            data = response.read().decode("utf-8")

    except Exception as error:
        raise ConnectionError(
            f"공공데이터 API에 연결하지 못했습니다: {error}"
        )

    try:
        result = json.loads(data)

    except json.JSONDecodeError:
        raise ValueError(
            "API에서 받은 데이터의 형식이 올바르지 않습니다."
        )

    response_data = result.get("response")

    if response_data is None:
        raise ValueError(
            "API 응답에서 데이터를 찾을 수 없습니다."
        )

    header = response_data.get("header", {})

    result_code = str(
        header.get("resultCode", "")
    )

    result_message = header.get(
        "resultMsg",
        "알 수 없는 오류"
    )

    if result_code not in ("00", "0"):
        raise ValueError(
            f"API 오류: {result_message}"
        )

    body = response_data.get("body", {})
    items = body.get("items", [])

    if not items:
        raise ValueError(
            "선택한 지역의 대기질 데이터를 찾을 수 없습니다."
        )

    return items
