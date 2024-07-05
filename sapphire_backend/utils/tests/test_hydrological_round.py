from decimal import Decimal

import pytest

from sapphire_backend.utils.db_helper import execute_sql_hydrological_round
from sapphire_backend.utils.rounding import hydrological_round


class TestHydrologicalRound:
    input_output_expected = [
        (Decimal("0.0"), Decimal("0.0")),
        (Decimal("0.00005567"), Decimal("0")),
        (Decimal("0.555"), Decimal("0.555")),
        (Decimal("0.5555"), Decimal("0.556")),
        (Decimal("0.5555555"), Decimal("0.556")),
        (Decimal("0.2368"), Decimal("0.237")),
        (Decimal("2"), Decimal("2")),
        (Decimal("2.565"), Decimal("2.57")),
        (Decimal("25"), Decimal("25")),
        (Decimal("24.67"), Decimal("24.7")),
        (Decimal("124.7"), Decimal("125")),
        (Decimal("124.67"), Decimal("125")),
        (Decimal("1246"), Decimal("1250")),
        (Decimal("1245.7"), Decimal("1250")),
        (Decimal("1245.67"), Decimal("1250")),
    ]

    def test_python_hydrological_round(self, manual_hydro_station_kyrgyz):
        for input_value, output_expected in self.input_output_expected:
            python_func_output = hydrological_round(input_value)
            assert python_func_output == output_expected

    def test_sql_hydrological_round(self, manual_hydro_station_kyrgyz):
        for input_value, expected_output in self.input_output_expected:
            sql_output = execute_sql_hydrological_round(input_value)
            assert sql_output == expected_output

    @pytest.mark.django_db
    def test_compare_hydrological_round_range_low(self):
        start = Decimal("0.00001")
        end = Decimal("1")
        increment = Decimal("0.00003")

        current_value = start
        while current_value <= end:
            python_result = hydrological_round(current_value)
            sql_result = execute_sql_hydrological_round(current_value)

            assert (
                python_result == sql_result
            ), f"Failed for input {current_value}: Python result {python_result} != SQL result {sql_result}"

            current_value += increment

    @pytest.mark.django_db
    def test_compare_hydrological_round_range_middle(self):
        start = Decimal("1")
        end = Decimal("5")
        increment = Decimal("0.0003")

        current_value = start
        while current_value <= end:
            python_result = hydrological_round(current_value)
            sql_result = execute_sql_hydrological_round(current_value)

            assert (
                python_result == sql_result
            ), f"Failed for input {current_value}: Python result {python_result} != SQL result {sql_result}"

            current_value += increment

    @pytest.mark.django_db
    def test_compare_hydrological_round_range_high(self):
        start = Decimal("5")
        end = Decimal("2000")
        increment = Decimal("2.3")

        current_value = start
        while current_value <= end:
            python_result = hydrological_round(current_value)
            sql_result = execute_sql_hydrological_round(current_value)

            assert (
                python_result == sql_result
            ), f"Failed for input {current_value}: Python result {python_result} != SQL result {sql_result}"

            current_value += increment
