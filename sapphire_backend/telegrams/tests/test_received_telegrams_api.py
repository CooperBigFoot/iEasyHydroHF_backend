from datetime import date, datetime, timedelta
from unittest.mock import patch

import pytest

from sapphire_backend.telegrams.models import TelegramReceived
from sapphire_backend.telegrams.tests.factories import TelegramReceivedFactory
from sapphire_backend.utils.datetime_helper import SmartDatetime


class TestListTelegramsReceivedAPI:
    @pytest.mark.parametrize(
        "client, expected_status_code",
        [
            ("unauthenticated_api_client", 401),
            ("regular_user_uzbek_api_client", 403),
            ("organization_admin_uzbek_api_client", 403),
            ("regular_user_kyrgyz_api_client", 200),
            ("organization_admin_kyrgyz_api_client", 200),
            ("superadmin_kyrgyz_api_client", 200),
            ("superadmin_uzbek_api_client", 200),
        ],
    )
    def test_list_telegram_received_status_code(
        self,
        client,
        manual_hydro_station_kyrgyz,
        expected_status_code,
        organization_kyrgyz,
        request,
    ):
        endpoint = f"/api/v1/telegrams/{organization_kyrgyz.uuid}/received/list"

        client = request.getfixturevalue(client)

        response = client.get(endpoint)
        assert response.status_code == expected_status_code

    @pytest.mark.parametrize(
        "client",
        [
            "regular_user_kyrgyz_api_client",
            "organization_admin_kyrgyz_api_client",
            "superadmin_kyrgyz_api_client",
            "superadmin_uzbek_api_client",
        ],
    )
    def test_list_telegram_received_filter_date(
        self,
        client,
        organization_kyrgyz,
        filestate_zks,
        request,
    ):
        target_smart_dt = SmartDatetime(datetime(2020, 1, 1, 10, 3, 0), station=organization_kyrgyz, tz_included=False)
        # date 2020-01-01
        for sec in range(10):
            with patch("django.utils.timezone.now", return_value=target_smart_dt.tz + timedelta(seconds=sec)):
                TelegramReceivedFactory(filestate=filestate_zks, organization=organization_kyrgyz)

        # date 2020-01-02
        for sec in range(8):
            with patch("django.utils.timezone.now", return_value=target_smart_dt.tz + timedelta(days=1, seconds=sec)):
                TelegramReceivedFactory(filestate=filestate_zks, organization=organization_kyrgyz)

        endpoint = f"/api/v1/telegrams/{organization_kyrgyz.uuid}/received/list"

        client = request.getfixturevalue(client)

        response = client.get(endpoint, {"created_date": date(2020, 1, 1)})
        res = response.json()
        queryset_expected = (
            TelegramReceived.objects.filter(
                created_date__gte=target_smart_dt.day_beginning_tz,
                created_date__lt=target_smart_dt.day_beginning_tz + timedelta(days=1),
                organization=organization_kyrgyz,
            )
            .order_by("-created_date")
            .values()
        )
        for telegram_response, telegram_expected in zip(res, queryset_expected):
            assert datetime.fromisoformat(telegram_response["created_date"]) == telegram_expected["created_date"]
            assert telegram_response["telegram"] == telegram_expected["telegram"]
            assert telegram_response["id"] == telegram_expected["id"]

    @pytest.mark.parametrize(
        "client, expected_status_code",
        [
            ("unauthenticated_api_client", 401),
            ("regular_user_uzbek_api_client", 403),
            ("organization_admin_uzbek_api_client", 403),
            ("regular_user_kyrgyz_api_client", 200),
            ("organization_admin_kyrgyz_api_client", 200),
            ("superadmin_kyrgyz_api_client", 200),
            ("superadmin_uzbek_api_client", 200),
        ],
    )
    def test_telegram_received_acknowledge_status_code(
        self,
        client,
        organization_kyrgyz,
        filestate_zks,
        request,
        expected_status_code,
    ):
        target_smart_dt = SmartDatetime(datetime(2020, 1, 1, 10, 3, 0), station=organization_kyrgyz, tz_included=False)
        # date 2020-01-01
        for sec in range(10):
            with patch("django.utils.timezone.now", return_value=target_smart_dt.tz + timedelta(seconds=sec)):
                TelegramReceivedFactory(
                    id=sec + 1, filestate=filestate_zks, acknowledged=False, organization=organization_kyrgyz
                )

        endpoint = f"/api/v1/telegrams/{organization_kyrgyz.uuid}/received/ack"

        client = request.getfixturevalue(client)

        response = client.post(
            endpoint,
            data={"ids": [2, 5]},
            content_type="application/json",
        )

        assert response.status_code == expected_status_code

    @pytest.mark.parametrize(
        "client",
        [
            "regular_user_kyrgyz_api_client",
            "organization_admin_kyrgyz_api_client",
            "superadmin_kyrgyz_api_client",
            "superadmin_uzbek_api_client",
        ],
    )
    def test_telegram_received_acknowledge(
        self,
        client,
        organization_kyrgyz,
        filestate_zks,
        request,
    ):
        target_smart_dt = SmartDatetime(datetime(2020, 1, 1, 10, 3, 0), station=organization_kyrgyz, tz_included=False)
        # date 2020-01-01
        for sec in range(10):
            with patch("django.utils.timezone.now", return_value=target_smart_dt.tz + timedelta(seconds=sec)):
                TelegramReceivedFactory(
                    id=sec + 1, filestate=filestate_zks, acknowledged=False, organization=organization_kyrgyz
                )

        endpoint = f"/api/v1/telegrams/{organization_kyrgyz.uuid}/received/ack"

        client = request.getfixturevalue(client)

        # Before ack
        assert (
            TelegramReceived.objects.filter(id=2, acknowledged=False, organization=organization_kyrgyz).exists()
            is True
        )
        assert (
            TelegramReceived.objects.filter(id=5, acknowledged=False, organization=organization_kyrgyz).exists()
            is True
        )

        client.post(
            endpoint,
            data={"ids": [2, 5]},
            content_type="application/json",
        )

        # After ack
        assert (
            TelegramReceived.objects.filter(id=2, acknowledged=True, organization=organization_kyrgyz).exists() is True
        )
        assert (
            TelegramReceived.objects.filter(id=5, acknowledged=True, organization=organization_kyrgyz).exists() is True
        )

    @pytest.mark.parametrize(
        "client",
        [
            "regular_user_kyrgyz_api_client",
            "organization_admin_kyrgyz_api_client",
            "superadmin_kyrgyz_api_client",
            "superadmin_uzbek_api_client",
        ],
    )
    def test_telegram_received_acknowledge_non_existing(
        self,
        client,
        organization_kyrgyz,
        filestate_zks,
        request,
    ):
        endpoint = f"/api/v1/telegrams/{organization_kyrgyz.uuid}/received/ack"

        client = request.getfixturevalue(client)

        # Before ack
        assert (
            TelegramReceived.objects.filter(id=100, acknowledged=False, organization=organization_kyrgyz).exists()
            is False
        )

        response = client.post(endpoint, data={"ids": [100]}, content_type="application/json")

        # After ack
        res = response.json()
        assert res == {"detail": "Object does not exist", "code": "not_found"}
