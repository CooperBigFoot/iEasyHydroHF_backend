import math
from decimal import ROUND_HALF_UP, Decimal


def custom_ceil(value: int | None) -> int | None:
    """
    Custom ceil accepts float and None, returns None if so
    """
    if value is None:
        return None
    return math.ceil(value)


def custom_round(value: float | Decimal | None, ndigits: int | None = None) -> float | None:
    """
    Custom round accepts float, Decimal and None, returns float or None.
    """
    if value is None:
        return None
    if ndigits is not None:
        if ndigits > 10:
            raise ValueError("No need to round to more than 10 digits.")
    return round(float(value), ndigits)


def hydrological_round(number: Decimal | float | int):
    if number == 0:
        return Decimal("0.000")
    elif number < 1.0:
        # return (number * 3).quantize(Decimal("1"), rounding=ROUND_HALF_UP)    # Convert the number to a Decimal
        rounding_format = "1." + "0" * 3  # Create the format string e.g., '1.000' for 3 places
        return number.quantize(Decimal(rounding_format), rounding=ROUND_HALF_UP)
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
