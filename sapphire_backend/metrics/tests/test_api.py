import datetime as dt

from sapphire_backend.metrics.choices import HydrologicalMeasurementType, HydrologicalMetricName


class TestHydroMetricsAPI:
    endpoint = "/api/v1/metrics/{}/hydro"

    def test_get_hydro_metrics_for_anonymous_user(self, api_client, organization):
        response = api_client.get(self.endpoint.format(organization.uuid))

        assert response.status_code == 401

    def test_get_hydro_metrics_for_other_organization_user(
        self, authenticated_regular_user_other_organization_api_client, organization
    ):
        response = authenticated_regular_user_other_organization_api_client.get(
            self.endpoint.format(organization.uuid)
        )

        assert response.status_code == 403

    def test_get_hydro_metrics_for_regular_user(
        self,
        authenticated_regular_user_other_organization_api_client,
        backup_organization,
        water_discharge,
        water_level_manual_other,
        water_level_automatic,
        water_level_manual_other_organization,
        water_level_manual,
    ):
        response = authenticated_regular_user_other_organization_api_client.get(
            self.endpoint.format(backup_organization.uuid)
        )

        assert response.status_code == 200
        assert len(response.json()) == 1

    def test_get_hydro_metrics_for_super_admin_from_other_organization(
        self,
        authenticated_superadmin_user_api_client,
        backup_organization,
        water_discharge,
        water_level_manual_other,
        water_level_manual_other_organization,
        water_level_manual,
        water_level_automatic,
    ):
        response = authenticated_superadmin_user_api_client.get(self.endpoint.format(backup_organization.uuid))

        assert response.status_code == 200
        assert len(response.json()) == 1

    def test_get_hydro_metrics_with_invalid_filter(self, authenticated_regular_user_api_client, organization):
        response = authenticated_regular_user_api_client.get(
            self.endpoint.format(organization.uuid), {"filter": "invalid"}
        )

        assert response.status_code == 200
        assert response.json() == []

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
            self.endpoint.format(organization.uuid),
            {
                "metric_name": HydrologicalMetricName.WATER_LEVEL_DAILY.value,
                "value_type": HydrologicalMeasurementType.MANUAL.value,
                "station__station_code": manual_hydro_station.station_code,
            },
        )

        EXPECTED_OUTPUT = [
            {
                "avg_value": water_level_manual_other.avg_value,
                "timestamp": water_level_manual_other.timestamp.strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "Z",
                "metric_name": water_level_manual_other.metric_name,
                "value_type": water_level_manual_other.value_type,
                "sensor_identifier": water_level_manual_other.sensor_identifier,
                "station_id": manual_hydro_station.id,
            },
            {
                "avg_value": water_level_manual.avg_value,
                "timestamp": water_level_manual.timestamp.strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "Z",
                "metric_name": water_level_manual.metric_name,
                "value_type": water_level_manual.value_type,
                "sensor_identifier": water_level_manual.sensor_identifier,
                "station_id": manual_hydro_station.id,
            },
        ]

        assert response.json() == EXPECTED_OUTPUT

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
            {"timestamp__gte": (dt.datetime.now(tz=dt.timezone.utc) - dt.timedelta(hours=50)).isoformat()},
        )

        assert response.json() == [
            {"metric_name": HydrologicalMetricName.WATER_DISCHARGE_DAILY, "metric_count": 1},
            {"metric_name": HydrologicalMetricName.WATER_LEVEL_DAILY, "metric_count": 2},
        ]

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
                "timestamp__gte": (dt.datetime.now(tz=dt.timezone.utc) - dt.timedelta(hours=50)).isoformat(),
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
                "timestamp__gte": (dt.datetime.utcnow() - dt.timedelta(hours=50)).isoformat(),
            },
        )

        print(response.json())

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
