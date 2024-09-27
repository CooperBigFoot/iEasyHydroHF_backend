# import pytest
#
# from sapphire_backend.ingestion.utils.parser import ZKSParser
# from sapphire_backend.telegrams.models import TelegramReceived
# from sapphire_backend.telegrams.parser import KN15TelegramParser
#
# TELEGRAMS_EXPECTED = ["15000 14081 10122 20000 30122 00000=",
#                       "15001 14081 10262 20000 30258 41521 00000=",
#                       "15002 14082 10212 20000 30211 48417 00000 96607 10211 21716 31460 51313=",
#                       "15003 NIL=",
#                       "15004 14082 10325 20012 30320 0000/ 92213 10326 20000 30326 00002 92212 10326 20000 30325 00000=",
#                       "15005 14082 10185 20011 30185 00011 92212 10184 20022 30186 00000="
#                       ]
#
#
# class TestXMLParser:
#     @pytest.mark.django_db
#     def test_parse_xml_file_metrics_count(self, filestate_xml_20240131_downloaded,
#                                        organization_kyrgyz):
#         assert TelegramReceived.objects.all().count() == 0
#         parser = ZKSParser(file_path=filestate_zks_14_07_downloaded.local_path,
#                            filestate=filestate_zks_14_07_downloaded, organization=organization_kyrgyz)
#
#         parser.run()
#         queryset = TelegramReceived.objects.filter(organization=organization_kyrgyz,
#                                                    filestate=filestate_zks_14_07_downloaded).order_by("id")
#
#         assert queryset.count() == 6
#
#     @pytest.mark.django_db
#     def test_parse_file_telegram_valid(self, filestate_zks_14_07_downloaded,
#                                        hydro_stations_zks_kyrgyz,
#                                        organization_kyrgyz):
#
#         zks_parser = ZKSParser(file_path=filestate_zks_14_07_downloaded.local_path,
#                                filestate=filestate_zks_14_07_downloaded, organization=organization_kyrgyz)
#
#         zks_parser.run()
#         queryset = TelegramReceived.objects.filter(organization=organization_kyrgyz,
#                                                    filestate=filestate_zks_14_07_downloaded,
#                                                    ).order_by("id")
#
#         for tg_received, tg_expected in zip(queryset, TELEGRAMS_EXPECTED):
#             assert tg_received.telegram == tg_expected
#             try:
#                 decoded_expected = KN15TelegramParser(
#                     tg_expected, organization_uuid=organization_kyrgyz.uuid, store_parsed_telegram=False
#                 ).parse()
#                 assert tg_received.valid is True
#                 assert tg_received.decoded_values == decoded_expected
#                 assert tg_received.station_code == decoded_expected["section_zero"]["station_code"]
#                 assert tg_received.errors == ""
#             except Exception as e:
#                 assert tg_received.valid is False
#                 assert tg_received.decoded_values == ""
#                 assert tg_received.station_code == ""
#                 assert tg_received.errors == repr(e)
