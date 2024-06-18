from datetime import date

import pytest

from sapphire_backend.estimations.models import EstimationsWaterDischargeDailyAverage
from sapphire_backend.utils.rounding import custom_round


class TestEstimationsApi:
    start_date = date(2020, 2, 1)
    end_date = date(2020, 2, 29)

    @pytest.mark.django_db(transaction=True)
    @pytest.mark.parametrize("water_level_metrics_daily_generator", [(start_date, end_date)], indirect=True)
    def test_get_discharge_daily_average(
        self,
        organization,
        manual_hydro_station_kyrgyz,
        authenticated_regular_user_kyrgyz_api_client,
        water_level_metrics_daily_generator,
        discharge_model_manual_hydro_station_kyrgyz,
    ):
        endpoint = f"/api/v1/estimations/{str(organization.uuid)}/discharge-daily-average"

        response = authenticated_regular_user_kyrgyz_api_client.get(
            endpoint,
            {
                "station_id": manual_hydro_station_kyrgyz.id,
                "timestamp_local__gte": "2020-02-01T12:00:00Z",
                "timestamp_local__lte": "2020-02-29T23:59:59.999Z",
                "order_direction": "ASC",
            },
            content_type="application/json",
        )

        wdda_res_returned = response.json()

        wdda_queryset = EstimationsWaterDischargeDailyAverage.objects.filter(
            station_id=manual_hydro_station_kyrgyz.id,
            timestamp_local__date__range=(self.start_date, self.end_date),
        ).order_by("timestamp_local")

        wdda_res_expected = wdda_queryset.values("timestamp_local", "avg_value")

        assert len(wdda_res_returned) == len(wdda_res_expected)
        for entry_returned, entry_expected in zip(wdda_res_returned, wdda_res_expected):
            assert entry_returned["timestamp_local"] == entry_expected["timestamp_local"].isoformat()
            assert custom_round(entry_returned["avg_value"], 6) == custom_round(entry_expected["avg_value"], 6)
