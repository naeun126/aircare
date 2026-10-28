 """예보 지역명과 선택한 시도를 비교하기 쉽게 정리한다."""
    region = str(region).strip()

    # 예보에 시·도 이름이 길게 표시되는 경우도 고려
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


query_key = f"{search_date}_{inform_code}"
if st.session_state.get("official_forecast_query_key") != query_key:
    for key in (
        "official_forecast_items",
        "official_forecast_date",
        "official_forecast_code",
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

        # API가 반환한 예보 중 내일 날짜에 해당하는 자료만 표시한다.
        result_items = [
            item for item in merged.values()
            if date_key(item["date"]) == target_date
        ]
        result_items.sort(key=lambda item: item["date"])

        st.session_state["official_forecast_items"] = result_items
        st.session_state["official_forecast_date"] = search_date
        st.session_state["official_forecast_code"] = inform_code
        st.session_state["official_forecast_query_key"] = query_key

    except KeyError:
        st.error(
            "Streamlit Secrets에 service_key가 설정되어 있는지 확인하세요."
        )
    except (ValueError, ConnectionError) as error:
        st.error(f"예보 조회에 실패했습니다: {error}")
    except Exception as error:
        st.error(f"예상하지 못한 오류가 발생했습니다: {error}")


items = st.session_state.get("official_forecast_items", [])
saved_date = st.session_state.get("official_forecast_date")
saved_code = st.session_state.get("official_forecast_code")


if (
    items
    and saved_date == search_date
    and saved_code == inform_code
):
    st.divider()
    st.subheader(f"📋 {tomorrow:%Y년 %m월 %d일} {selected_name} 예보")

    tabs = st.tabs([item["date"] for item in items])

    for tab, item in zip(tabs, items):
        with tab:
            grades = parse_grades(item["grades"])

            # 선택한 시도에 해당하는 예보를 먼저 찾는다.
            normalized_selected = normalize_region(selected_sido)

            selected_grades = [
                (region, grade)
                for region, grade in grades
                if normalize_region(region) == normalized_selected
            ]

            st.caption(
                f"발표 시각: {clean_text(item['time'])}"
            )

            # ========================================
            # 선택 지역 예보를 최상단에 강조 표시
            # ========================================

            st.markdown("### 📍 선택 지역 예보")

            if selected_grades:
                for region, grade in selected_grades:
                    color = grade_color(grade)

                    st.markdown(
                        f"""
                        <div style="
                            background:{color}15;
                            border-left:7px solid {color};
                            border-radius:12px;
                            padding:22px;
                            margin:8px 0 20px 0;
                        ">
                            <div style="font-size:15px;color:#64748b;">
                                {region} · {selected_name}
                            </div>
                            <div style="
                                font-size:32px;
                                font-weight:700;
                                color:{color};
                                margin:8px 0;
                            ">
                                {grade}
                            </div>
                            <div style="font-size:14px;">
                                에어코리아 공식 권역별 예보
                            </div>
                        </div>
                        """,
                        unsafe_allow_html=True,
                    )
            else:
                st.warning(
                    f"선택한 지역인 '{selected_sido}'의 등급을 "
                    "예보 자료에서 찾지 못했습니다. "
                    "아래 지역별 예보를 확인해 주세요."
                )

            # ========================================
            # 나머지 지역 예보
            # ========================================

            st.markdown("### 🗺️ 다른 지역 예보")

            other_grades = [
                (region, grade)
                for region, grade in grades
                if normalize_region(region) != normalized_selected
