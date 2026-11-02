

def date_key(value):
    """예보 날짜를 YYYY-MM-DD 형식으로 변환한다."""

    value = str(value).strip()

    match = re.search(
        r"(\d{4})년\s*(\d{1,2})월\s*(\d{1,2})일",
        value,
    )

    if match:
        year, month, day = match.groups()

        return (
            f"{year}-{int(month):02d}-{int(day):02d}"
        )

    match = re.search(
        r"(\d{4})-(\d{1,2})-(\d{1,2})",
        value,
    )

    if match:
        year, month, day = match.groups()

        return (
            f"{year}-{int(month):02d}-{int(day):02d}"
        )

    return ""


def parse_grades(grade_list):
    """지역별 예보 문자열을 지역과 등급으로 분리한다."""

    results = []

    for text in grade_list:
        if not text:
            continue

        text = str(text)

        text = (
            text.replace("<br>", ",")
            .replace("<br/>", ",")
            .replace("<br />", ",")
        )

        for part in re.split(r"[,;\n]", text):

            if ":" not in part:
                continue

            region, grade = part.split(":", 1)

            region = region.strip()
            grade = grade.strip()

            if region and grade:
                results.append((region, grade))

    return results


def grade_color(grade):
    """예보 등급에 따른 색상을 반환한다."""

    grade = str(grade).strip()

    if "매우나쁨" in grade or "매우 나쁨" in grade:
        return "#D93636"

    elif "나쁨" in grade:
        return "#E87524"

    elif "보통" in grade:
        return "#E5B900"

    elif "좋음" in grade:
        return "#2E9D50"

    return "#64748B"


def normalize_region(region):
    """예보 지역명과 선택한 시도명을 비교하기 쉽게 정리한다."""

    region = str(region).strip()

    aliases = {
        "충청북도": "충북",
        "충청남도": "충남",
        "전라북도": "전북",
        "전라남도": "전남",
        "경상북도": "경북",
        "경상남도": "경남",
        "강원특별자치도": "강원",
        "제주특별자치도": "제주",
        "경기도": "경기",
        "서울특별시": "서울",
        "부산광역시": "부산",
        "대구광역시": "대구",
        "인천광역시": "인천",
        "광주광역시": "광주",
        "대전광역시": "대전",
        "울산광역시": "울산",
        "세종특별자치시": "세종",
    }

    return aliases.get(region, region)


# ========================================
# 5. 공식 예보 API 조회
# ========================================

query_key = f"{search_date}_{inform_code}"

if st.session_state.get("official_forecast_query_key") != query_key:

    for key in (
        "official_forecast_items",
        "official_forecast_date",
        "official_forecast_code",
        "official_forecast_query_key",
    ):
        st.session_state.pop(key, None)

    try:
        service_key = st.secrets["service_key"]

        with st.spinner("공식 예보를 조회하고 있습니다..."):

            items = get_air_quality_forecast(
                service_key=service_key,
                inform_code=inform_code,
                search_date=search_date,
            )

        # 예보 대상 날짜별로 내용 통합
        merged = {}

        for item in items:

            forecast_date = clean_text(
                item.get("informData"),
                "날짜 정보 없음",
            )

            if forecast_date not in merged:

                merged[forecast_date] = {
                    "date": forecast_date,
                    "time": item.get("dataTime"),
                    "grades": [],
                    "overall": [],
                    "cause": [],
                    "action": [],
                }

            row = merged[forecast_date]

            for field, target in [
                ("informGrade", "grades"),
                ("informOverall", "overall"),
                ("informCause", "cause"),
                ("actionKnack", "action"),
            ]:

                value = item.get(field)

                if value and str(value).strip() not in ("", "None"):

                    text = str(value).strip()

                    if text not in row[target]:
                        row[target].append(text)

            if item.get("dataTime"):
                row["time"] = item["dataTime"]

        # 내일 날짜에 해당하는 예보만 선택
        result_items = [
            item
            for item in merged.values()
            if date_key(item["date"]) == target_date
        ]

        result_items.sort(
