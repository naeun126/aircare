"""대기질 등급 판정 기준과 색상을 한곳에서 관리한다."""

GRADE_LEVELS = ["좋음", "보통", "나쁨", "매우 나쁨"]

GRADE_COLORS = {
    "좋음": "#2E9D50",
    "보통": "#E5B900",
    "나쁨": "#E87524",
    "매우 나쁨": "#D93636",
}

# 좋음 / 보통 / 나쁨의 상한값이며, 이를 넘으면 매우 나쁨
GRADE_LIMITS = {
    "PM10": (30, 80, 150),
    "PM2.5": (15, 35, 75),
    "오존(O₃)": (0.030, 0.090, 0.150),
}


def get_grade(value, limits):
    """측정값을 등급 문자열로 바꾼다. 값이 없거나 음수면 None을 반환한다."""
    try:
        number = float(value)
    except (ValueError, TypeError):
        return None

    if number < 0:
        return None

    for level, limit in zip(GRADE_LEVELS, limits):
        if number <= limit:
            return level

    return GRADE_LEVELS[-1]
