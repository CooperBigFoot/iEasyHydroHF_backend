import pytest

from sapphire_backend.estimations.schema import DischargeModelPointsPair
from sapphire_backend.estimations.utils import least_squares_fit
from sapphire_backend.utils.exceptions import InsufficientDataVariationException
from sapphire_backend.utils.rounding import custom_round


class TestFuncLeastSquaresFitAPI:
    def test_least_squares_fit_func_three_points(self):
        expected = {
            "param_a": 27.602188704658484,
            "param_b": 2,
            "param_c": 0.0006222912360003366,
        }

        points_raw = [{"q": 10, "h": 100}, {"q": 20, "h": 150}, {"q": 32, "h": 200}]

        input_points = [DischargeModelPointsPair(**kwargs) for kwargs in points_raw]
        calculated = least_squares_fit(input_points)

        assert custom_round(calculated["param_a"], 10) == custom_round(expected["param_a"], 10)
        assert custom_round(calculated["param_b"], 10) == custom_round(expected["param_b"], 10)
        assert custom_round(calculated["param_c"], 10) == custom_round(expected["param_c"], 10)

    def test_least_squares_fit_func_four_points(self):
        points_raw = [{"q": 4.97, "h": 133}, {"q": 8.47, "h": 144}, {"q": 16, "h": 163}, {"q": 27.51, "h": 184}]

        expected = {
            "param_a": -94.91529202311185,
            "param_b": 2,
            "param_c": 0.0034658921581445954,
        }

        input_points = [DischargeModelPointsPair(**kwargs) for kwargs in points_raw]
        calculated = least_squares_fit(input_points)

        assert custom_round(calculated["param_a"], 10) == custom_round(expected["param_a"], 10)
        assert custom_round(calculated["param_b"], 10) == custom_round(expected["param_b"], 10)
        assert custom_round(calculated["param_c"], 10) == custom_round(expected["param_c"], 10)

    def test_least_squares_fit_func_five_points(self):
        points_raw = [
            {"q": 2.43, "h": 110},
            {"q": 4.97, "h": 133},
            {"q": 8.47, "h": 144},
            {"q": 16, "h": 163},
            {"q": 27.51, "h": 184},
        ]
        expected = {
            "param_a": -84.46577833258002,
            "param_b": 2,
            "param_c": 0.002616828746452033,
        }

        input_points = [DischargeModelPointsPair(**kwargs) for kwargs in points_raw]
        calculated = least_squares_fit(input_points)

        assert custom_round(calculated["param_a"], 10) == custom_round(expected["param_a"], 10)
        assert custom_round(calculated["param_b"], 10) == custom_round(expected["param_b"], 10)
        assert custom_round(calculated["param_c"], 10) == custom_round(expected["param_c"], 10)

    def test_least_squares_fit_func_three_points_with_same_water_level(self):
        points_raw = [{"q": 10, "h": 20}, {"q": 10, "h": 21}, {"q": 10, "h": 19}]

        input_points = [DischargeModelPointsPair(**kwargs) for kwargs in points_raw]

        with pytest.raises(InsufficientDataVariationException) as exc_info:
            least_squares_fit(input_points)

        assert (
            str(exc_info.value.message)
            == "Insufficient variation in water levels for reliable discharge calculation. Measurements need to be taken at different water levels."
        )
