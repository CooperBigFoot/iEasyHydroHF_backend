def custom_average(values: list[int | float | None]) -> float | None:
    """
    Calculate the average of the elements in the list, ignoring None values.

    :param values: List of numbers (int or float), possibly containing None.
    :return: The average of the non-None numbers, or None if there are no such numbers.
    """
    # Filter out None values
    filtered_values = [value for value in values if value is not None]

    # Check if there are any valid numbers to calculate the average
    if len(filtered_values) == 0:
        return None

    # Calculate the average
    return sum(filtered_values) / len(filtered_values)

