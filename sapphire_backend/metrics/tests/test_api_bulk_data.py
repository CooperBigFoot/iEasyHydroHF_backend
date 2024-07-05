# from io import BytesIO
#
# import pytest
# from openpyxl.reader.excel import load_workbook
#
# from sapphire_backend.estimations.tests.conftest import virtual_station
#
#
# class TestBulkDataAPI:
#     endpoint = "/api/v1/bulk-data/{organization_uuid}/download"
#
#     @pytest.mark.parametrize(
#         "client, expected_status_code",
#         [
#             ("unauthenticated_api_client", 401),
#             ("regular_user_uzbek_api_client", 403),
#             ("organization_admin_uzbek_api_client", 403),
#             ("regular_user_kyrgyz_api_client", 200),
#             ("organization_admin_kyrgyz_api_client", 200),
#             ("superadmin_kyrgyz_api_client", 200),
#             ("superadmin_uzbek_api_client", 200),
#         ],
#     )
#     def test_bulk_data_download_permissions_status_codes(
#         self,
#         client,
#         organization_kyrgyz,
#         manual_hydro_station_kyrgyz,
#         manual_meteo_station_kyrgyz,
#         virtual_station,
#         expected_status_code,
#         request,
#     ):
#         client = request.getfixturevalue(client)
#         payload = {
#             "hydro_station_manual_uuids": [manual_hydro_station_kyrgyz.uuid],
#             "hydro_station_auto_uuids": [],
#             "meteo_station_uuids": [manual_meteo_station_kyrgyz.uuid],
#             "virtual_station_uuids": [virtual_station.uuid],
#         }
#
#         response = client.post(
#             self.endpoint.format(organization_uuid=organization_kyrgyz.uuid),
#             data=payload,
#             content_type="application/json",
#         )
#
#         assert response.status_code == expected_status_code
#
#     @pytest.mark.parametrize(
#         "client",
#         [
#             "regular_user_kyrgyz_api_client",
#             "organization_admin_kyrgyz_api_client",
#             "superadmin_kyrgyz_api_client",
#             "superadmin_uzbek_api_client",
#         ],
#     )
#     def test_download_check_sheets(
#         self, client, organization_kyrgyz,
#         manual_hydro_station_kyrgyz,
#         manual_meteo_station_kyrgyz,
#         virtual_station,
#         request
#     ):
#         client = request.getfixturevalue(client)
#         payload = {
#             "hydro_station_manual_uuids": [manual_hydro_station_kyrgyz.uuid],
#             "hydro_station_auto_uuids": [],
#             "meteo_station_uuids": [manual_meteo_station_kyrgyz.uuid],
#             "virtual_station_uuids": [virtual_station.uuid],
#         }
#
#         response = client.post(
#             self.endpoint.format(organization_uuid=organization_kyrgyz.uuid),
#             data=payload,
#             content_type="application/json",
#         )
#
#         workbook = load_workbook(filename=BytesIO(b''.join(response.streaming_content)))
#
#         assert len(workbook.sheetnames) == 3
#
#         sheets_expected = {manual_hydro_station_kyrgyz.station_code + " (manual)", manual_meteo_station_kyrgyz.station_code  + " (meteo)",
#                            virtual_station.station_code  + " (virtual)"}
#         sheets_actual = {workbook.sheetnames}
#         assert sheets_actual == sheets_expected
#
#     # @pytest.mark.parametrize(
#     #     "client",
#     #     [
#     #         "regular_user_kyrgyz_api_client",
#     #         "organization_admin_kyrgyz_api_client",
#     #         "superadmin_kyrgyz_api_client",
#     #         "superadmin_uzbek_api_client",
#     #     ],
#     # )
#     # def test_generate_bulk_data_small(
#     #     self, client, organization_kyrgyz,
#     #     manual_hydro_station_kyrgyz,
#     #     manual_second_hydro_station_kyrgyz,
#     #     manual_meteo_station_kyrgyz,
#     #     manual_second_meteo_station_kyrgyz,
#     #     virtual_station,
#     #     request
#     # ):
#     #     client = request.getfixturevalue(client)
#     #     payload = {
#     #         "hydro_station_uuids": [manual_hydro_station_kyrgyz.uuid,manual_second_hydro_station_kyrgyz.uuid],
#     #         "meteo_station_uuids": [manual_meteo_station_kyrgyz.uuid, manual_second_meteo_station_kyrgyz.uuid],
#     #         "virtual_station_uuids": [virtual_station.uuid],
#     #     }
#     #
#     #     response = client.post(
#     #         self.endpoint.format(organization_uuid=organization_kyrgyz.uuid),
#     #         data=payload,
#     #         content_type="application/json",
#     #     )
#     #
#     #     workbook = load_workbook(filename=BytesIO(b''.join(response.streaming_content)))
#     #
#     #
