from sapphire_backend.estimations.schema import DischargeModelPointsPair


def least_squares_fit(points: list[DischargeModelPointsPair]) -> dict[str, float]:
    x_values = [dp.h for dp in points]
    y_values = [dp.q**0.5 for dp in points]
    mean_x = sum(x_values) / len(x_values)
    mean_y = sum(y_values) / len(y_values)

    ssxx = sum((u - mean_x) ** 2 for u in x_values)
    ssxy = sum((a - mean_x) * (b - mean_y) for a, b in zip(x_values, y_values))

    a = mean_y - (ssxy * mean_x / ssxx)
    b = ssxy / ssxx
    param_a = a / b
    param_b = 2
    param_c = b**2

    return {
        "param_a": param_a,
        "param_b": param_b,
        "param_c": param_c,
    }
