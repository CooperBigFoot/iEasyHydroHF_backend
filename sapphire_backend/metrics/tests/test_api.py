import datetime as dt
import os
import uuid
from decimal import Decimal
from pathlib import Path
from unittest.mock import patch

import pytest
from django.core.files.uploadedfile import SimpleUploadedFile

from sapphire_backend.metrics.choices import HydrologicalMeasurementType, HydrologicalMetricName, NormType
from sapphire_backend.metrics.exceptions import FileTooBigException
from sapphire_backend.metrics.models import HydrologicalNorm


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
                "metric_name__in": HydrologicalMetricName.WATER_LEVEL_DAILY,
                "value_type__in": HydrologicalMeasurementType.MANUAL,
                "station__station_code": manual_hydro_station.station_code,
            },
        )

        EXPECTED_OUTPUT = [
            {
                "avg_value": water_level_manual_other.avg_value,
                "timestamp_local": water_level_manual_other.timestamp.strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "Z",
                "metric_name": water_level_manual_other.metric_name,
                "value_type": water_level_manual_other.value_type,
                "sensor_identifier": water_level_manual_other.sensor_identifier,
                "station_id": manual_hydro_station.id,
                "value_code": None,
            },
            {
                "avg_value": water_level_manual.avg_value,
                "timestamp_local": water_level_manual.timestamp.strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "Z",
                "metric_name": water_level_manual.metric_name,
                "value_type": water_level_manual.value_type,
                "sensor_identifier": water_level_manual.sensor_identifier,
                "station_id": manual_hydro_station.id,
                "value_code": None,
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


class TestDischargeNormsAPI:
    endpoint = "/api/v1/hydrological-norms"
    decadal_test_file = os.path.join(Path(__file__).parent, "data", "decadal_hydro_norm_example.xlsx")
    monthly_test_file = os.path.join(Path(__file__).parent, "data", "monthly_hydro_norm_example.xlsx")

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

    def test_upload_monthly_norm_api_response(self, authenticated_regular_user_api_client, manual_hydro_station):
        file = self._get_monthly_test_file()
        response = authenticated_regular_user_api_client.post(
            f"{self.endpoint}/{manual_hydro_station.uuid}?norm_type=m", {"file": file}, format="multipart"
        )

        assert response.json() == [
            {"timestamp_local": "2024-01-01T12:00:00Z", "ordinal_number": 1, "value": "1.0"},
            {"timestamp_local": "2024-02-01T12:00:00Z", "ordinal_number": 2, "value": "2.0"},
            {"timestamp_local": "2024-03-01T12:00:00Z", "ordinal_number": 3, "value": "3.0"},
            {"timestamp_local": "2024-04-01T12:00:00Z", "ordinal_number": 4, "value": "4.0"},
            {"timestamp_local": "2024-05-01T12:00:00Z", "ordinal_number": 5, "value": "5.0"},
            {"timestamp_local": "2024-06-01T12:00:00Z", "ordinal_number": 6, "value": "6.0"},
            {"timestamp_local": "2024-07-01T12:00:00Z", "ordinal_number": 7, "value": "7.0"},
            {"timestamp_local": "2024-08-01T12:00:00Z", "ordinal_number": 8, "value": "8.0"},
            {"timestamp_local": "2024-09-01T12:00:00Z", "ordinal_number": 9, "value": "9.0"},
            {"timestamp_local": "2024-10-01T12:00:00Z", "ordinal_number": 10, "value": "10.0"},
            {"timestamp_local": "2024-11-01T12:00:00Z", "ordinal_number": 11, "value": "11.0"},
            {"timestamp_local": "2024-12-01T12:00:00Z", "ordinal_number": 12, "value": "12.0"},
        ]

    def test_upload_decadal_norm_partial_api_response(
        self, authenticated_regular_user_api_client, manual_hydro_station
    ):
        file = self._get_decadal_test_file()
        response = authenticated_regular_user_api_client.post(
            f"{self.endpoint}/{manual_hydro_station.uuid}?norm_type=d", {"file": file}, format="multipart"
        )

        assert response.json()[:12] == [
            {"timestamp_local": "2024-01-05T12:00:00Z", "ordinal_number": 1, "value": "1.0"},
            {"timestamp_local": "2024-01-15T12:00:00Z", "ordinal_number": 2, "value": "2.0"},
            {"timestamp_local": "2024-01-25T12:00:00Z", "ordinal_number": 3, "value": "3.0"},
            {"timestamp_local": "2024-02-05T12:00:00Z", "ordinal_number": 4, "value": "4.0"},
            {"timestamp_local": "2024-02-15T12:00:00Z", "ordinal_number": 5, "value": "5.0"},
            {"timestamp_local": "2024-02-25T12:00:00Z", "ordinal_number": 6, "value": "6.0"},
            {"timestamp_local": "2024-03-05T12:00:00Z", "ordinal_number": 7, "value": "7.0"},
            {"timestamp_local": "2024-03-15T12:00:00Z", "ordinal_number": 8, "value": "8.0"},
            {"timestamp_local": "2024-03-25T12:00:00Z", "ordinal_number": 9, "value": "9.0"},
            {"timestamp_local": "2024-04-05T12:00:00Z", "ordinal_number": 10, "value": "10.0"},
            {"timestamp_local": "2024-04-15T12:00:00Z", "ordinal_number": 11, "value": "11.0"},
            {"timestamp_local": "2024-04-25T12:00:00Z", "ordinal_number": 12, "value": "12.0"},
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
    ):
        response = authenticated_regular_user_api_client.get(
            f"{self.endpoint}/{manual_hydro_station.uuid}?norm_type=d"
        )
        assert response.json() == [
            {"timestamp_local": "2024-01-05T12:00:00Z", "ordinal_number": 1, "value": "1.00000"},
            {"timestamp_local": "2024-01-15T12:00:00Z", "ordinal_number": 2, "value": "2.00000"},
        ]

    def test_get_monthly_norm(
        self,
        authenticated_regular_user_api_client,
        manual_hydro_station,
        decadal_discharge_norm_first,
        decadal_discharge_norm_second,
        monthly_discharge_norm_first,
        monthly_discharge_norm_second,
    ):
        response = authenticated_regular_user_api_client.get(
            f"{self.endpoint}/{manual_hydro_station.uuid}?norm_type=m"
        )
        assert response.json() == [
            {"timestamp_local": "2024-01-01T12:00:00Z", "ordinal_number": 1, "value": "1.00000"},
            {"timestamp_local": "2024-02-01T12:00:00Z", "ordinal_number": 2, "value": "2.00000"},
        ]
