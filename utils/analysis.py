def get_valid_values(data, column):
    values = []

    for record in data:
        value = record.get(column)

        if value is None:
            continue

        try:
            number = float(value)

            if number >= 0:
                values.append(number)

        except (ValueError, TypeError):
            continue

    return values


def calculate_average(data, column):
    values = get_valid_values(data, column)

    if not values:
        return None

    return sum(values) / len(values)


def calculate_max(data, column):
    values = get_valid_values(data, column)

    if not values:
        return None

    return max(values)


def calculate_min(data, column):
    values = get_valid_values(data, column)

    if not values:
        return None

    return min(values)


def calculate_change(data, column):
    values = get_valid_values(data, column)

    if len(values) < 2:
        return None

    return values[-1] - values[0]


def calculate_trend(data, column):
    change = calculate_change(data, column)

    if change is None:
        return "데이터 부족"

    if change > 0:
        return "증가"

    if change < 0:
        return "감소"

    return "변화 없음"
