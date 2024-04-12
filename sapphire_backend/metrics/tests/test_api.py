import datetime as dt
import os
from pathlib import Path
from unittest.mock import patch

import pytest
from django.core.files.uploadedfile import SimpleUploadedFile

from sapphire_backend.metrics.choices import HydrologicalMeasurementType, HydrologicalMetricName
from sapphire_backend.metrics.exceptions import FileTooBigException


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


class TestDischargeNormsAPI:
    endpoint = "/api/v1/discharge-norms"
    decadal_test_file = os.path.join(Path(__file__).parent, "data", "decadal_norm_example.xlsx")
    monthly_test_file = os.path.join(Path(__file__).parent, "data", "monthly_norm_example.xlsx")

    def _get_decadal_test_file(self):
        with open(self.decadal_test_file, "rb") as f:
            file_content = f.read()

        file = SimpleUploadedFile(
            "decadal_norm_example.xlsx",
            file_content,
            content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )

        return file

    def _get_monthly_test_file(self):
        with open(self.monthly_test_file, "rb") as f:
            file_content = f.read()

        file = SimpleUploadedFile(
            "monthly_norm_example.xlsx",
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

        response = api_client.post(f"{self.endpoint}/{manual_hydro_station.uuid}/decadal", files=files)
        assert response.status_code == 401

    def test_upload_decadal_norm_file_for_unauthorized_user(
        self, authenticated_regular_user_other_organization_api_client, manual_hydro_station
    ):
        file = self._get_decadal_test_file()

        response = authenticated_regular_user_other_organization_api_client.post(
            f"{self.endpoint}/{manual_hydro_station.uuid}/decadal", {"file": file}, format="multipart"
        )
        assert response.status_code == 403

    def test_upload_decadal_norm_file_wrong_extension(
        self, authenticated_regular_user_api_client, manual_hydro_station
    ):
        file = SimpleUploadedFile(
            "wrong_extension_file.wrongext", b"Dummy content", content_type="application/octet-stream"
        )

        response = authenticated_regular_user_api_client.post(
            f"{self.endpoint}/{manual_hydro_station.uuid}/decadal", {"file": file}, format="multipart"
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
                f"{self.endpoint}/{manual_hydro_station.uuid}/decadal", {"file": file}, format="multipart"
            )

            assert response.status_code == 400
            assert response.json() == {
                "detail": "Maximum file size is 2 MB, but uploaded file has 3 MB",
                "code": "invalid_norm_file",
            }
