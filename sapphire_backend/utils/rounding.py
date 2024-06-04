import math
from decimal import ROUND_HALF_UP, Decimal


def custom_ceil(value: int | None) -> int | None:
    """
    Custom ceil accepts float and None, returns None if so
    """
    if value is None:
        return None
    return math.ceil(value)


def custom_round(value: float | None, ndigits: int | None = None) -> float | None:
    """
    Custom round accepts float and None, returns None if so
    """
    if value is None:
        return None
    return round(float(value), ndigits)


def hydrological_round(number: float | int):
    if number == 0:
        return Decimal("0.000")

    # Convert the number to a Decimal
    number = Decimal(number)

    # Determine the exponent to scale the number to 1 <= number < 10
    exponent = number.adjusted()

    # Calculate the scale factor
    scale_factor = Decimal("10") ** (2 - exponent)

    # Scale, round, and then rescale the number
    scaled_number = (number * scale_factor).quantize(Decimal("1"), rounding=ROUND_HALF_UP)
    rounded_number = scaled_number / scale_factor

    # Format to ensure three significant digits
    return rounded_number
