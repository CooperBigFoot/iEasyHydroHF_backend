import datetime as dt
import os
import uuid
from decimal import Decimal
from pathlib import Path
from unittest.mock import patch

import pytest
from django.core.files.uploadedfile import SimpleUploadedFile

from sapphire_backend.estimations.models import EstimationsWaterDischargeDailyAverage
from sapphire_backend.metrics.choices import HydrologicalMeasurementType, HydrologicalMetricName, NormType
from sapphire_backend.metrics.exceptions import FileTooBigException
from sapphire_backend.metrics.models import HydrologicalNorm
from sapphire_backend.utils.rounding import custom_round


class TestHydroMetricsAPI:
    endpoint = "/api/v1/metrics/{}/hydro"
    start_date = dt.date(2020, 2, 1)
    end_date = dt.date(2020, 2, 15)

    @pytest.mark.parametrize(
        "client_fixture, expected_status_code",
        [
            ("api_client", 401),  # anonymous user
            ("authenticated_regular_user_other_organization_api_client", 403),  # other org user
            ("authenticated_regular_user_api_client", 200),  # regular user
            ("authenticated_superadmin_user_api_client", 200),  # superadmin
        ],
    )
    def test_get_hydro_metrics_permissions(
        self,
        client_fixture,
        expected_status_code,
        organization,
        request,
    ):
        client = request.getfixturevalue(client_fixture)
        response = client.get(
            f"{self.endpoint.format(organization.uuid)}/measurements/individual",
            {
                "timestamp_local__gte": "2020-01-01T00:00:00Z",
                "timestamp_local__lte": "2020-01-15T00:00:00Z",
            },
        )
        assert response.status_code == expected_status_code

    def test_get_hydro_metrics_with_invalid_filter(
        self, authenticated_regular_user_api_client, water_level_manual, organization
    ):
        response = authenticated_regular_user_api_client.get(
            f"{self.endpoint.format(organization.uuid)}/measurements/individual",  # Add /measurements/individual
            {
                "filter": "invalid",
                "timestamp_local__gte": water_level_manual.timestamp_local - dt.timedelta(minutes=1),
                "timestamp_local__lt": water_level_manual.timestamp_local + dt.timedelta(minutes=1),
            },
        )

        assert response.status_code == 200
        response_json = response.json()
        assert len(response_json["results"]) == 1
        assert response_json["count"] == 1
        assert response_json["next"] is None
        assert response_json["previous"] is None

    def test_get_hydro_metrics_with_filters(
        self,
        authenticated_regular_user_api_client,
        organization,
        manual_hydro_station,
        water_discharge,
        water_level_manual,
        water_level_automatic,
        water_level_manual_other,
        water_level_manual_other_organization,
    ):
        response = authenticated_regular_user_api_client.get(
            f"{self.endpoint.format(organization.uuid)}/measurements/individual",  # Add /measurements/individual
            {
                "timestamp_local__gte": water_level_manual.timestamp_local - dt.timedelta(minutes=1),
                "timestamp_local__lt": water_level_manual.timestamp_local + dt.timedelta(minutes=1),
                "metric_name__in": HydrologicalMetricName.WATER_LEVEL_DAILY,
                "value_type__in": HydrologicalMeasurementType.MANUAL,
                "station__station_code": manual_hydro_station.station_code,
            },
        )

        EXPECTED_OUTPUT = [
            {
                "avg_value": water_level_manual.avg_value,
                "timestamp_local": water_level_manual.timestamp.strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "Z",
                "metric_name": water_level_manual.metric_name,
                "value_type": water_level_manual.value_type,
                "sensor_identifier": water_level_manual.sensor_identifier,
                "station_id": manual_hydro_station.id,
                "value_code": None,
                "station_code": manual_hydro_station.station_code,
                "station_uuid": str(manual_hydro_station.uuid),
            },
        ]

        response_json = response.json()
        assert response_json["results"] == EXPECTED_OUTPUT
        assert response_json["count"] == 1
        assert response_json["next"] is None
        assert response_json["previous"] is None

    @pytest.mark.django_db(transaction=True)
    @pytest.mark.parametrize("water_level_metrics_daily_generator", [(start_date, end_date)], indirect=True)
    @pytest.mark.parametrize(
        "view_type, display_type, metric_names, expected_status, expected_keys",
        [
            # Daily view tests
            (
                "daily",
                "individual",
                ["WLDA"],
                200,
                ["timestamp_local", "avg_value", "metric_name"],
            ),
            (
                "daily",
                "grouped",
                ["WLDA"],
                200,
                ["timestamp_local", "WLDA"],
            ),
            # Measurements view tests
            (
                "measurements",
                "individual",
                ["WLD"],
                200,
                ["timestamp_local", "avg_value", "metric_name"],
            ),
            (
                "measurements",
                "grouped",
                ["WLD"],
                200,
                ["timestamp_local", "WLD"],
            ),
            # Error cases
            (
                "daily",
                "individual",
                [],  # Missing required metric_names
                422,
                None,
            ),
        ],
    )
    def test_get_hydro_metrics_view_types(
        self,
        regular_user_kyrgyz_api_client,
        organization_kyrgyz,
        manual_hydro_station_kyrgyz,
        water_level_metrics_daily_generator,
        view_type,
        display_type,
        metric_names,
        expected_status,
        expected_keys,
    ):
        response = regular_user_kyrgyz_api_client.get(
            f"{self.endpoint.format(organization_kyrgyz.uuid)}/{view_type}/{display_type}",
            {
                "station_id": manual_hydro_station_kyrgyz.id,
                "timestamp_local__gte": f"{self.start_date.isoformat()}T00:00:00Z",
                "timestamp_local__lte": f"{self.end_date.isoformat()}T23:59:59Z",
                "metric_name__in": metric_names,
                "order_param": "timestamp_local",
                "order_direction": "ASC",
            },
        )

        assert response.status_code == expected_status

        if expected_status == 200:
            data = response.json()
            results = data["results"]  # Always paginated for table views
            if len(results) > 0:
                for key in expected_keys:
                    assert key in results[0]

    @pytest.mark.django_db(transaction=True)
    @pytest.mark.parametrize("water_level_metrics_daily_generator", [(start_date, end_date)], indirect=True)
    @pytest.mark.parametrize(
        "view_type, metric_names, expected_status, expected_keys",
        [
            (
                "daily",
                ["WLDA"],
                200,
                ["x", "y"],  # Chart format uses x/y keys
            ),
            (
                "measurements",
                ["WLD"],
                200,
                ["x", "y"],
            ),
        ],
    )
    def test_get_hydro_metrics_chart(
        self,
        regular_user_kyrgyz_api_client,
        organization_kyrgyz,
        manual_hydro_station_kyrgyz,
        water_level_metrics_daily_generator,
        view_type,
        metric_names,
        expected_status,
        expected_keys,
    ):
        response = regular_user_kyrgyz_api_client.get(
            f"{self.endpoint.format(organization_kyrgyz.uuid)}/{view_type}/chart",
            {
                "station_id": manual_hydro_station_kyrgyz.id,
                "timestamp_local__gte": f"{self.start_date.isoformat()}T00:00:00Z",
                "timestamp_local__lte": f"{self.end_date.isoformat()}T23:59:59Z",
                "metric_name__in": metric_names,
            },
        )

        assert response.status_code == expected_status

        if expected_status == 200:
            data = response.json()  # Direct response, no pagination
            if len(data) > 0:
                for key in expected_keys:
                    assert key in data[0]

    @pytest.mark.django_db(transaction=True)
    @pytest.mark.parametrize(
        "view_type, start_date, end_date, expected_status",
        [
            # Raw measurements - 30 days limit
            (
                "measurements",
                dt.datetime(2020, 1, 1, tzinfo=dt.timezone.utc),
                dt.datetime(2020, 1, 30, tzinfo=dt.timezone.utc),  # 29 days - should pass
                200,
            ),
            (
                "measurements",
                dt.datetime(2020, 1, 1, tzinfo=dt.timezone.utc),
                dt.datetime(2020, 2, 1, tzinfo=dt.timezone.utc),  # 31 days - should fail
                422,
            ),
            # Daily data - 365 days limit
            (
                "daily",
                dt.datetime(2020, 1, 1, tzinfo=dt.timezone.utc),
                dt.datetime(2020, 12, 31, tzinfo=dt.timezone.utc),  # 364 days - should pass
                200,
            ),
            (
                "daily",
                dt.datetime(2020, 1, 1, tzinfo=dt.timezone.utc),
                dt.datetime(2021, 1, 2, tzinfo=dt.timezone.utc),  # 366 days - should fail
                422,
            ),
        ],
    )
    def test_get_hydro_metrics_date_range_validation(
        self,
        regular_user_kyrgyz_api_client,
        organization_kyrgyz,
        manual_hydro_station_kyrgyz,
        view_type,
        start_date,
        end_date,
        expected_status,
    ):
        """Test date range validation for different view types"""
        response = regular_user_kyrgyz_api_client.get(
            f"{self.endpoint.format(organization_kyrgyz.uuid)}/{view_type}/individual",
            {
                "station_id": manual_hydro_station_kyrgyz.id,
                "timestamp_local__gte": start_date.isoformat(),
                "timestamp_local__lte": end_date.isoformat(),
                "metric_name__in": ["WLDA"] if view_type == "daily" else ["WLD"],
                "order_param": "timestamp_local",
                "order_direction": "ASC",
                "station": manual_hydro_station_kyrgyz.id,
            },
        )

        assert response.status_code == expected_status

    @pytest.mark.django_db(transaction=True)
    @pytest.mark.parametrize("water_level_metrics_daily_generator", [(start_date, end_date)], indirect=True)
    def test_get_detailed_daily_hydro_metrics(
        self,
        organization_kyrgyz,
        manual_hydro_station_kyrgyz,
        regular_user_kyrgyz_api_client,
        water_level_metrics_daily_generator,
    ):
        """Test getting detailed daily hydro metrics with all fields."""
        response = regular_user_kyrgyz_api_client.get(
            f"{self.endpoint.format(organization_kyrgyz.uuid)}/detailed-daily",
            {
                "station": manual_hydro_station_kyrgyz.id,
                "timestamp_local__gte": "2020-02-01T00:00:00Z",
                "timestamp_local__lt": "2020-02-15T00:00:00Z",
                "metric_name__in": ["WLD", "ATDA", "WTDA"],  # Water Level Daily + Air/Water Temperature
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert len(data) > 0

        # Check first entry has all required fields
        first_entry = data[0]
        expected_fields = {
            "id",
            "date",
            "daily_average_water_level",
            "manual_daily_average_water_level",
            "morning_water_level",
            "morning_water_level_timestamp",
            "evening_water_level",
            "evening_water_level_timestamp",
            "min_water_level",
            "min_water_level_timestamp",
            "max_water_level",
            "max_water_level_timestamp",
            "daily_average_air_temperature",
            "daily_average_water_temperature",
        }
        assert set(first_entry.keys()) == expected_fields

    @pytest.mark.parametrize(
        "client_fixture, expected_status_code",
        [
            ("api_client", 401),  # anonymous user
            ("authenticated_regular_user_other_organization_api_client", 403),  # other org user
            ("authenticated_regular_user_api_client", 200),  # regular user
            ("authenticated_superadmin_user_api_client", 200),  # superadmin
        ],
    )
    def test_get_detailed_daily_hydro_metrics_permissions(
        self,
        client_fixture,
        expected_status_code,
        organization,
        manual_hydro_station,
        request,
    ):
        """Test permissions for detailed daily hydro metrics endpoint."""
        client = request.getfixturevalue(client_fixture)
        response = client.get(
            f"{self.endpoint.format(organization.uuid)}/detailed-daily",
            {
                "station": manual_hydro_station.id,
                "timestamp_local__gte": "2020-02-01T00:00:00Z",
                "timestamp_local__lt": "2020-02-15T00:00:00Z",
                "metric_name__in": ["WLD"],
            },
        )
        assert response.status_code == expected_status_code

    def test_get_detailed_daily_hydro_metrics_missing_params(
        self,
        authenticated_regular_user_api_client,
        organization,
        manual_hydro_station,
    ):
        """Test validation of required query parameters."""
        # Missing station
        response = authenticated_regular_user_api_client.get(
            f"{self.endpoint.format(organization.uuid)}/detailed-daily",
            {
                "timestamp_local__gte": "2020-02-01T00:00:00Z",
                "timestamp_local__lt": "2020-02-15T00:00:00Z",
                "metric_name__in": ["WLD"],
            },
        )
        assert response.status_code == 422
        assert response.json()["detail"] == "Some data is invalid or missing"

        # Missing WLD metric
        response = authenticated_regular_user_api_client.get(
            f"{self.endpoint.format(organization.uuid)}/detailed-daily",
            {
                "station": manual_hydro_station.id,
                "timestamp_local__gte": "2020-02-01T00:00:00Z",
                "timestamp_local__lt": "2020-02-15T00:00:00Z",
                "metric_name__in": ["ATDA"],  # Only air temperature, no water level
            },
        )
        assert response.status_code == 422
        assert response.json()["detail"] == "Some data is invalid or missing"

        # Missing date range
        response = authenticated_regular_user_api_client.get(
            f"{self.endpoint.format(organization.uuid)}/detailed-daily",
            {
                "station": manual_hydro_station.id,
                "metric_name__in": ["WLD"],
            },
        )
        assert response.status_code == 422

    @pytest.mark.django_db(transaction=True)
    @pytest.mark.parametrize("water_level_metrics_daily_generator", [(start_date, end_date)], indirect=True)
    def test_get_detailed_daily_hydro_metrics_data_validation(
        self,
        organization_kyrgyz,
        manual_hydro_station_kyrgyz,
        regular_user_kyrgyz_api_client,
        water_level_metrics_daily_generator,
    ):
        """Test data validation and processing."""
        # Test with invalid date range (too long)
        response = regular_user_kyrgyz_api_client.get(
            f"{self.endpoint.format(organization_kyrgyz.uuid)}/detailed-daily",
            {
                "station": manual_hydro_station_kyrgyz.id,
                "timestamp_local__gte": "2019-01-01T00:00:00Z",
                "timestamp_local__lt": "2021-01-01T00:00:00Z",  # More than 365 days
                "metric_name__in": ["WLD"],
            },
        )
        assert response.status_code == 422
        assert "Some data is invalid or missing" in response.json()["detail"]

        # Test with invalid metric names
        response = regular_user_kyrgyz_api_client.get(
            f"{self.endpoint.format(organization_kyrgyz.uuid)}/detailed-daily",
            {
                "station": manual_hydro_station_kyrgyz.id,
                "timestamp_local__gte": "2020-02-01T00:00:00Z",
                "timestamp_local__lt": "2020-02-15T00:00:00Z",
                "metric_name__in": ["INVALID"],
            },
        )
        assert response.status_code == 422

    def test_get_hydro_metric_count(
        self,
        authenticated_regular_user_api_client,
        organization,
        water_discharge,
        water_level_manual_other,
        water_level_manual_other_organization,
        water_level_manual,
        water_level_automatic,
    ):
        response = authenticated_regular_user_api_client.get(
            f"{self.endpoint.format(organization.uuid)}/metric-count",
            {"timestamp_local__gte": (dt.datetime.now(tz=dt.timezone.utc) - dt.timedelta(hours=50)).isoformat()},
        )

        assert sorted(response.json(), key=lambda d: d["metric_name"]) == sorted(
            [
                {"metric_name": HydrologicalMetricName.WATER_LEVEL_DAILY, "metric_count": 2},
                {"metric_name": HydrologicalMetricName.WATER_DISCHARGE_DAILY, "metric_count": 1},
            ],
            key=lambda d: d["metric_name"],
        )

    def test_get_hydro_metric_count_total_only(
        self,
        authenticated_regular_user_api_client,
        organization,
        water_discharge,
        water_level_manual_other,
        water_level_manual_other_organization,
        water_level_manual,
        water_level_automatic,
    ):
        response = authenticated_regular_user_api_client.get(
            f"{self.endpoint.format(organization.uuid)}/metric-count",
            {
                "timestamp_local__gte": (dt.datetime.now(tz=dt.timezone.utc) - dt.timedelta(hours=50)).isoformat(),
                "total_only": True,
            },
        )

        assert response.json() == {"total": 3}

    def test_get_hydro_metric_time_bucket_for_invalid_interval(
        self, authenticated_regular_user_api_client, organization
    ):
        response = authenticated_regular_user_api_client.get(
            f"{self.endpoint.format(organization.uuid)}/time-bucket", {"interval": "invalid", "agg_func": "COUNT"}
        )

        assert response.status_code == 400

    def test_get_hydro_metric_time_bucket_for_invalid_aggregation_function(
        self, authenticated_regular_user_api_client, organization
    ):
        response = authenticated_regular_user_api_client.get(
            f"{self.endpoint.format(organization.uuid)}/time-bucket", {"interval": "1 day", "agg_func": "invalid"}
        )

        assert response.status_code == 422

    def test_get_hydro_metrics_time_bucket(
        self,
        authenticated_regular_user_api_client,
        organization,
        water_discharge,
        water_level_manual_other,
        water_level_manual,
        water_level_automatic,
    ):
        response = authenticated_regular_user_api_client.get(
            f"{self.endpoint.format(organization.uuid)}/time-bucket",
            {
                "interval": "1 day",
                "agg_func": "COUNT",
                "timestamp_local__gte": (dt.datetime.utcnow() - dt.timedelta(hours=50)).isoformat(),
            },
        )

        EXPECTED_RESPONSE = [
            {
                "bucket": dt.datetime(
                    water_discharge.timestamp.year,
                    water_discharge.timestamp.month,
                    water_discharge.timestamp.day,
                    tzinfo=dt.timezone.utc,
                ).strftime("%Y-%m-%dT%H:%M:%S")
                + "Z",
                "value": 1,
            },
            {
                "bucket": dt.datetime(
                    water_level_manual_other.timestamp.year,
                    water_level_manual_other.timestamp.month,
                    water_level_manual_other.timestamp.day,
                    tzinfo=dt.timezone.utc,
                ).strftime("%Y-%m-%dT%H:%M:%S")
                + "Z",
                "value": 1,
            },
            {
                "bucket": dt.datetime(
                    water_level_automatic.timestamp.year,
                    water_level_automatic.timestamp.month,
                    water_level_automatic.timestamp.day,
                    tzinfo=dt.timezone.utc,
                ).strftime("%Y-%m-%dT%H:%M:%S")
                + "Z",
                "value": 1,
            },
        ]

        assert response.json() == EXPECTED_RESPONSE

    @pytest.mark.django_db(transaction=True)
    @pytest.mark.parametrize("water_level_metrics_daily_generator", [(start_date, end_date)], indirect=True)
    def test_get_discharge_daily_average(
        self,
        organization_kyrgyz,
        manual_hydro_station_kyrgyz,
        regular_user_kyrgyz_api_client,
        water_level_metrics_daily_generator,
        discharge_model_manual_hydro_station_kyrgyz,
    ):
        response = regular_user_kyrgyz_api_client.get(
            f"{self.endpoint.format(organization_kyrgyz.uuid)}/daily/individual",
            {
                "station_id": manual_hydro_station_kyrgyz.id,
                "timestamp_local__gte": "2020-02-01T12:00:00Z",
                "timestamp_local__lte": "2020-02-29T23:59:59.999Z",
                "metric_name__in": ["WDDA"],  # Water Discharge Daily Average
                "order_direction": "ASC",
            },
        )

        assert response.status_code == 200
        wdda_res_returned = response.json()["results"]  # Note: now wrapped in pagination

        wdda_queryset = EstimationsWaterDischargeDailyAverage.objects.filter(
            station_id=manual_hydro_station_kyrgyz.id,
            timestamp_local__date__range=(self.start_date, self.end_date),
        ).order_by("timestamp_local")

        wdda_res_expected = wdda_queryset.values("timestamp_local", "avg_value")

        assert len(wdda_res_returned) == len(wdda_res_expected)
        for entry_returned, entry_expected in zip(wdda_res_returned, wdda_res_expected):
            assert entry_returned["timestamp_local"] == entry_expected["timestamp_local"].isoformat()
            assert custom_round(entry_returned["avg_value"], 6) == custom_round(entry_expected["avg_value"], 6)


class TestDischargeNormsAPI:
    endpoint = "/api/v1/hydrological-norms"
    decadal_test_file = os.path.join(Path(__file__).parent, "data", "decadal_hydro_norm_example.xlsx")
    monthly_test_file = os.path.join(Path(__file__).parent, "data", "monthly_hydro_norm_example.xlsx")
    pentadal_test_file = os.path.join(Path(__file__).parent, "data", "pentadal_hydro_norm_example.xlsx")

    def _get_decadal_test_file(self):
        with open(self.decadal_test_file, "rb") as f:
            file_content = f.read()

        file = SimpleUploadedFile(
            self.decadal_test_file,
            file_content,
            content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )

        return file

    def _get_monthly_test_file(self):
        with open(self.monthly_test_file, "rb") as f:
            file_content = f.read()

        file = SimpleUploadedFile(
            self.monthly_test_file,
            file_content,
            content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )

        return file

    def _get_pentadal_test_file(self):
        with open(self.pentadal_test_file, "rb") as f:
            file_content = f.read()

        file = SimpleUploadedFile(
            self.pentadal_test_file,
            file_content,
            content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )

        return file

    @pytest.mark.django_db
    def test_download_template_file_for_unauthenticated_user(self, api_client):
        response = api_client.get(f"{self.endpoint}/download-template?norm_type=d")

        assert response.status_code == 401

    @pytest.mark.django_db
    def test_download_decadal_norm_template_file(self, authenticated_regular_user_api_client):
        response = authenticated_regular_user_api_client.get(f"{self.endpoint}/download-template?norm_type=d")

        assert response.status_code == 200
        assert response["Content-Disposition"] == 'attachment; filename="discharge_norm_decadal_template.xlsx"'

    @pytest.mark.django_db
    def test_download_monthly_norm_template_file(self, authenticated_regular_user_api_client):
        response = authenticated_regular_user_api_client.get(f"{self.endpoint}/download-template?norm_type=m")

        assert response.status_code == 200
        assert response["Content-Disposition"] == 'attachment; filename="discharge_norm_monthly_template.xlsx"'

    @pytest.mark.django_db
    def test_download_pentadal_norm_template_file(self, authenticated_regular_user_api_client):
        response = authenticated_regular_user_api_client.get(f"{self.endpoint}/download-template?norm_type=p")

        assert response.status_code == 200
        assert response["Content-Disposition"] == 'attachment; filename="discharge_norm_pentadal_template.xlsx"'

    @pytest.mark.django_db
    def test_download_missing_norm_template_file(self, authenticated_regular_user_api_client):
        with patch("os.path.exists", return_value=False):
            response = authenticated_regular_user_api_client.get(f"{self.endpoint}/download-template?norm_type=m")
            assert response.status_code == 404
            assert response.json() == {"detail": "Could not retrieve the file", "code": "file_not_found"}

    def test_upload_decadal_norm_file_for_unauthenticated_user(self, api_client, manual_hydro_station):
        file_content = b"Some file content"
        files = {
            "file": (
                "filename.xlsx",
                file_content,
                "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            )
        }

        response = api_client.post(f"{self.endpoint}/{manual_hydro_station.uuid}?norm_type=d", files=files)
        assert response.status_code == 401

    def test_upload_decadal_norm_file_for_unauthorized_user(
        self, authenticated_regular_user_other_organization_api_client, manual_hydro_station
    ):
        file = self._get_decadal_test_file()

        response = authenticated_regular_user_other_organization_api_client.post(
            f"{self.endpoint}/{manual_hydro_station.uuid}?norm_type=d", {"file": file}, format="multipart"
        )
        assert response.status_code == 403

    def test_upload_decadal_norm_file_wrong_extension(
        self, authenticated_regular_user_api_client, manual_hydro_station
    ):
        file = SimpleUploadedFile(
            "wrong_extension_file.wrongext", b"Dummy content", content_type="application/octet-stream"
        )

        response = authenticated_regular_user_api_client.post(
            f"{self.endpoint}/{manual_hydro_station.uuid}?norm_type=d", {"file": file}, format="multipart"
        )
        assert response.status_code == 400
        assert response.json() == {"detail": "Invalid file extension: .wrongext", "code": "invalid_norm_file"}

    def test_upload_large_file(self, authenticated_regular_user_api_client, manual_hydro_station):
        file = self._get_decadal_test_file()
        with patch(
            "sapphire_backend.metrics.utils.parser.DecadalDischargeNormFileParser._validate_file_size"
        ) as mock_validate:

            def side_effect():
                raise FileTooBigException(3, 2)

            mock_validate.side_effect = side_effect
            response = authenticated_regular_user_api_client.post(
                f"{self.endpoint}/{manual_hydro_station.uuid}?norm_type=d", {"file": file}, format="multipart"
            )

            assert response.status_code == 400
            assert response.json() == {
                "detail": "Maximum file size is 2 MB, but uploaded file has 3 MB",
                "code": "invalid_norm_file",
            }

    def test_decadal_norm_wrong_sheet_name(self, authenticated_regular_user_api_client, manual_hydro_station):
        file = self._get_decadal_test_file()

        with patch(
            "sapphire_backend.metrics.utils.parser.DecadalDischargeNormFileParser._get_sheet_names",
            return_value=["test"],
        ):
            response = authenticated_regular_user_api_client.post(
                f"{self.endpoint}/{manual_hydro_station.uuid}?norm_type=d", {"file": file}, format="multipart"
            )

            assert response.status_code == 400
            assert response.json() == {
                "detail": "Missing required sheets: 'test', found: 'discharge'",
                "code": "invalid_norm_file",
            }

    def test_incomplete_decadal_norm_upload(self, authenticated_regular_user_api_client, manual_hydro_station):
        file = self._get_monthly_test_file()
        response = authenticated_regular_user_api_client.post(
            f"{self.endpoint}/{manual_hydro_station.uuid}?norm_type=d", {"file": file}, format="multipart"
        )

        assert response.status_code == 400
        assert response.json() == {
            "detail": "Invalid number of columns, need to have 36 values.",
            "code": "invalid_norm_file",
        }

    def test_upload_decadal_norm(self, authenticated_regular_user_api_client, manual_hydro_station):
        assert HydrologicalNorm.objects.for_station(manual_hydro_station).decadal().count() == 0

        file = self._get_decadal_test_file()
        response = authenticated_regular_user_api_client.post(
            f"{self.endpoint}/{manual_hydro_station.uuid}?norm_type=d", {"file": file}, format="multipart"
        )

        assert response.status_code == 201
        assert HydrologicalNorm.objects.for_station(manual_hydro_station).decadal().count() == 36

    def test_upload_monthly_norm(self, authenticated_regular_user_api_client, manual_hydro_station):
        assert HydrologicalNorm.objects.for_station(manual_hydro_station).monthly().count() == 0

        file = self._get_monthly_test_file()
        response = authenticated_regular_user_api_client.post(
            f"{self.endpoint}/{manual_hydro_station.uuid}?norm_type=m", {"file": file}, format="multipart"
        )

        assert response.status_code == 201
        assert HydrologicalNorm.objects.for_station(manual_hydro_station).monthly().count() == 12

    def test_upload_pentadal_norm(self, authenticated_regular_user_api_client, manual_hydro_station):
        assert HydrologicalNorm.objects.for_station(manual_hydro_station).pentadal().count() == 0

        file = self._get_pentadal_test_file()
        response = authenticated_regular_user_api_client.post(
            f"{self.endpoint}/{manual_hydro_station.uuid}?norm_type=p", {"file": file}, format="multipart"
        )

        assert response.status_code == 201
        assert HydrologicalNorm.objects.for_station(manual_hydro_station).pentadal().count() == 72

    def test_upload_monthly_norm_api_response(self, authenticated_regular_user_api_client, manual_hydro_station):
        file = self._get_monthly_test_file()
        response = authenticated_regular_user_api_client.post(
            f"{self.endpoint}/{manual_hydro_station.uuid}?norm_type=m", {"file": file}, format="multipart"
        )

        current_year = dt.datetime.now().year
        assert response.json() == [
            {"timestamp_local": f"{current_year}-01-01T12:00:00Z", "ordinal_number": 1, "value": "1.0"},
            {"timestamp_local": f"{current_year}-02-01T12:00:00Z", "ordinal_number": 2, "value": "2.0"},
            {"timestamp_local": f"{current_year}-03-01T12:00:00Z", "ordinal_number": 3, "value": "3.0"},
            {"timestamp_local": f"{current_year}-04-01T12:00:00Z", "ordinal_number": 4, "value": "4.0"},
            {"timestamp_local": f"{current_year}-05-01T12:00:00Z", "ordinal_number": 5, "value": "5.0"},
            {"timestamp_local": f"{current_year}-06-01T12:00:00Z", "ordinal_number": 6, "value": "6.0"},
            {"timestamp_local": f"{current_year}-07-01T12:00:00Z", "ordinal_number": 7, "value": "7.0"},
            {"timestamp_local": f"{current_year}-08-01T12:00:00Z", "ordinal_number": 8, "value": "8.0"},
            {"timestamp_local": f"{current_year}-09-01T12:00:00Z", "ordinal_number": 9, "value": "9.0"},
            {"timestamp_local": f"{current_year}-10-01T12:00:00Z", "ordinal_number": 10, "value": "10.0"},
            {"timestamp_local": f"{current_year}-11-01T12:00:00Z", "ordinal_number": 11, "value": "11.0"},
            {"timestamp_local": f"{current_year}-12-01T12:00:00Z", "ordinal_number": 12, "value": "12.0"},
        ]

    def test_upload_decadal_norm_partial_api_response(
        self, authenticated_regular_user_api_client, manual_hydro_station
    ):
        file = self._get_decadal_test_file()
        response = authenticated_regular_user_api_client.post(
            f"{self.endpoint}/{manual_hydro_station.uuid}?norm_type=d", {"file": file}, format="multipart"
        )

        current_year = dt.datetime.now().year
        assert response.json()[:12] == [
            {"timestamp_local": f"{current_year}-01-05T12:00:00Z", "ordinal_number": 1, "value": "1.0"},
            {"timestamp_local": f"{current_year}-01-15T12:00:00Z", "ordinal_number": 2, "value": "2.0"},
            {"timestamp_local": f"{current_year}-01-25T12:00:00Z", "ordinal_number": 3, "value": "3.0"},
            {"timestamp_local": f"{current_year}-02-05T12:00:00Z", "ordinal_number": 4, "value": "4.0"},
            {"timestamp_local": f"{current_year}-02-15T12:00:00Z", "ordinal_number": 5, "value": "5.0"},
            {"timestamp_local": f"{current_year}-02-25T12:00:00Z", "ordinal_number": 6, "value": "6.0"},
            {"timestamp_local": f"{current_year}-03-05T12:00:00Z", "ordinal_number": 7, "value": "7.0"},
            {"timestamp_local": f"{current_year}-03-15T12:00:00Z", "ordinal_number": 8, "value": "8.0"},
            {"timestamp_local": f"{current_year}-03-25T12:00:00Z", "ordinal_number": 9, "value": "9.0"},
            {"timestamp_local": f"{current_year}-04-05T12:00:00Z", "ordinal_number": 10, "value": "10.0"},
            {"timestamp_local": f"{current_year}-04-15T12:00:00Z", "ordinal_number": 11, "value": "11.0"},
            {"timestamp_local": f"{current_year}-04-25T12:00:00Z", "ordinal_number": 12, "value": "12.0"},
        ]

    def test_upload_pentadal_norm_partial_api_response(
        self, authenticated_regular_user_api_client, manual_hydro_station
    ):
        file = self._get_pentadal_test_file()
        response = authenticated_regular_user_api_client.post(
            f"{self.endpoint}/{manual_hydro_station.uuid}?norm_type=p", {"file": file}, format="multipart"
        )

        current_year = dt.datetime.now().year
        assert response.json()[:12] == [
            {"timestamp_local": f"{current_year}-01-03T12:00:00Z", "ordinal_number": 1, "value": "1.0"},
            {"timestamp_local": f"{current_year}-01-08T12:00:00Z", "ordinal_number": 2, "value": "2.0"},
            {"timestamp_local": f"{current_year}-01-13T12:00:00Z", "ordinal_number": 3, "value": "3.0"},
            {"timestamp_local": f"{current_year}-01-18T12:00:00Z", "ordinal_number": 4, "value": "4.0"},
            {"timestamp_local": f"{current_year}-01-23T12:00:00Z", "ordinal_number": 5, "value": "5.0"},
            {"timestamp_local": f"{current_year}-01-28T12:00:00Z", "ordinal_number": 6, "value": "6.0"},
            {"timestamp_local": f"{current_year}-02-03T12:00:00Z", "ordinal_number": 7, "value": "7.0"},
            {"timestamp_local": f"{current_year}-02-08T12:00:00Z", "ordinal_number": 8, "value": "8.0"},
            {"timestamp_local": f"{current_year}-02-13T12:00:00Z", "ordinal_number": 9, "value": "9.0"},
            {"timestamp_local": f"{current_year}-02-18T12:00:00Z", "ordinal_number": 10, "value": "1.0"},
            {"timestamp_local": f"{current_year}-02-23T12:00:00Z", "ordinal_number": 11, "value": "2.0"},
            {"timestamp_local": f"{current_year}-02-28T12:00:00Z", "ordinal_number": 12, "value": "3.0"},
        ]

    def test_upload_norm_overwrites_existing_records(
        self, authenticated_regular_user_api_client, manual_hydro_station
    ):
        for i in range(1, 13):
            _ = HydrologicalNorm.objects.create(
                station=manual_hydro_station, norm_type=NormType.MONTHLY, value=i + 10, ordinal_number=i
            )

        norms = HydrologicalNorm.objects.for_station(manual_hydro_station).monthly()

        assert norms.count() == 12
        assert list(norms.values_list("value", flat=True)) == [
            Decimal("11.00000"),
            Decimal("12.00000"),
            Decimal("13.00000"),
            Decimal("14.00000"),
            Decimal("15.00000"),
            Decimal("16.00000"),
            Decimal("17.00000"),
            Decimal("18.00000"),
            Decimal("19.00000"),
            Decimal("20.00000"),
            Decimal("21.00000"),
            Decimal("22.00000"),
        ]

        file = self._get_monthly_test_file()
        _ = authenticated_regular_user_api_client.post(
            f"{self.endpoint}/{manual_hydro_station.uuid}?norm_type=m", {"file": file}, format="multipart"
        )

        assert norms.count() == 12
        assert list(norms.values_list("value", flat=True)) == [
            Decimal("1.00000"),
            Decimal("2.00000"),
            Decimal("3.00000"),
            Decimal("4.00000"),
            Decimal("5.00000"),
            Decimal("6.00000"),
            Decimal("7.00000"),
            Decimal("8.00000"),
            Decimal("9.00000"),
            Decimal("10.00000"),
            Decimal("11.00000"),
            Decimal("12.00000"),
        ]

    def test_get_norm_for_anonymous_user(self, api_client, manual_hydro_station):
        response = api_client.get(f"{self.endpoint}/{manual_hydro_station.uuid}?norm_type=m")
        assert response.status_code == 401

    def test_get_norm_for_station_in_different_organization(
        self, authenticated_regular_user_other_organization_api_client, manual_hydro_station
    ):
        response = authenticated_regular_user_other_organization_api_client.get(
            f"{self.endpoint}/{manual_hydro_station.uuid}?norm_type=m"
        )
        assert response.status_code == 403

    def test_get_norm_for_non_existent_station(self, authenticated_regular_user_api_client):
        response = authenticated_regular_user_api_client.get(f"{self.endpoint}/{uuid.uuid4()}?norm_type=m")
        assert response.status_code == 403  # not ideal, permission class can't find the station so the check fails

    def test_get_norm_for_station_with_no_data(self, authenticated_regular_user_api_client, manual_hydro_station):
        response = authenticated_regular_user_api_client.get(
            f"{self.endpoint}/{manual_hydro_station.uuid}?norm_type=m"
        )
        assert response.status_code == 200
        assert response.json() == []

    def test_get_decadal_norm(
        self,
        authenticated_regular_user_api_client,
        manual_hydro_station,
        decadal_discharge_norm_first,
        decadal_discharge_norm_second,
        monthly_discharge_norm_first,
        monthly_discharge_norm_second,
        pentadal_discharge_norm_first,
        pentadal_discharge_norm_second,
    ):
        current_year = dt.datetime.now().year
        response = authenticated_regular_user_api_client.get(
            f"{self.endpoint}/{manual_hydro_station.uuid}?norm_type=d"
        )
        assert response.json() == [
            {"timestamp_local": f"{current_year}-01-05T12:00:00Z", "ordinal_number": 1, "value": "1.00000"},
            {"timestamp_local": f"{current_year}-01-15T12:00:00Z", "ordinal_number": 2, "value": "2.00000"},
        ]

    def test_get_monthly_norm(
        self,
        authenticated_regular_user_api_client,
        manual_hydro_station,
        decadal_discharge_norm_first,
        decadal_discharge_norm_second,
        monthly_discharge_norm_first,
        monthly_discharge_norm_second,
        pentadal_discharge_norm_first,
        pentadal_discharge_norm_second,
    ):
        current_year = dt.datetime.now(dt.timezone.utc).year
        response = authenticated_regular_user_api_client.get(
            f"{self.endpoint}/{manual_hydro_station.uuid}?norm_type=m"
        )
        assert response.json() == [
            {"timestamp_local": f"{current_year}-01-01T12:00:00Z", "ordinal_number": 1, "value": "1.00000"},
            {"timestamp_local": f"{current_year}-02-01T12:00:00Z", "ordinal_number": 2, "value": "2.00000"},
        ]

    def test_get_pentadal_norm(
        self,
        authenticated_regular_user_api_client,
        manual_hydro_station,
        decadal_discharge_norm_first,
        decadal_discharge_norm_second,
        monthly_discharge_norm_first,
        monthly_discharge_norm_second,
        pentadal_discharge_norm_first,
        pentadal_discharge_norm_second,
    ):
        current_year = dt.datetime.now().year
        response = authenticated_regular_user_api_client.get(
            f"{self.endpoint}/{manual_hydro_station.uuid}?norm_type=p"
        )
        assert response.json() == [
            {"timestamp_local": f"{current_year}-01-03T12:00:00Z", "ordinal_number": 1, "value": "1.00000"},
            {"timestamp_local": f"{current_year}-01-08T12:00:00Z", "ordinal_number": 2, "value": "2.00000"},
        ]
