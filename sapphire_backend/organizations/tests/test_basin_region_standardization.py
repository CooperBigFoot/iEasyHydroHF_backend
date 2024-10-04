import pytest

from sapphire_backend.organizations.management.basin_region_standardizer import BasinRegionStandardizer
from sapphire_backend.organizations.models import Basin, Region


class TestBasinRegionStandardizerController:
    def test_standardizer_for_non_supported_organization(self, organization_kyrgyz):
        with pytest.raises(ValueError, match="uzbek is not supported. Currently supporting: kyrgyz"):
            _ = BasinRegionStandardizer("uzbek")

    @pytest.mark.django_db
    def test_standardizer_for_supported_organization_with_wrong_name_mapping(self):
        with pytest.raises(
            ValueError, match="Can't find organization with the name КыргызГидроМет, check the _organization_map"
        ):
            _ = BasinRegionStandardizer("kyrgyz")

    def test_standardizer_kyrgyz_region_map(self, kyrgyz_hydromet):
        brs = BasinRegionStandardizer("kyrgyz")
        assert brs.region_map == {
            "БАТКЕНСКАЯ ОБЛАСТЬ": "Баткенская",
            "Баткенская область": "Баткенская",
            "ЖАЛАЛ-АБАДСКАЯ ОБЛАСТЬ": "Жалал Абадская",
            "Жалал-Абадская область": "Жалал Абадская",
            "ИССЫК КУЛЬ": "Иссык Кульская",
            "ИССЫК-КУЛЬСКАЯ ОБЛАСТЬ": "Иссык Кульская",
            "Иссык-Кульская область": "Иссык Кульская",
            "НАРЫНСКАЯ ОБЛАСТЬ": "Нарынская",
            "Нарынская область": "Нарынская",
            "ОШСКАЯ ОБЛАСТЬ": "Ошская",
            "Ошская область": "Ошская",
            "ТАЛАССКАЯ ОБЛАСТЬ": "Таласская",
            "Таласская область": "Таласская",
            "Узген": "Ошская",
            "ЧУЙСКАЯ ОБЛАСТЬ": "Чуйская",
            "Чуйская область": "Чуйская",
        }

    def test_standardizer_kyrgyz_basin_map(self, kyrgyz_hydromet):
        brs = BasinRegionStandardizer("kyrgyz")
        assert brs.basin_map == {
            "Жыргалан": "Бассейн оз. Иссык Куль",
            "Иссык Куль": "Бассейн оз. Иссык Куль",
            "Иссык-Куль": "Бассейн оз. Иссык Куль",
            "Кара-Дарья": "Бассейн р. Сырдарьи",
            "Кара-Суу": "Бассейн р. Сырдарьи",
            "Кызыл-Суу": "Бассейн р. Амударьи",
            "Нарын": "Бассейн р. Сырдарьи",
            "ОГМС": "Бассейн р. Сырдарьи",
            "Падыша-Ата": "Бассейн р. Сырдарьи",
            "Сыр-Дарья": "Бассейн р. Сырдарьи",
            "Талас": "Бассейн р. Талас",
            "Тар": "Бассейн р. Сырдарьи",
            "Тентек-Сай": "Бассейн р. Сырдарьи",
            "ЦГМ": "Бассейн р. Сырдарьи",
            "Чаткал": "Бассейн р. Сырдарьи",
            "Чолпон-Ата": "Бассейн оз. Иссык Куль",
            "Чу": "Бассейн р. Чу",
        }

    def test_standardize_basins_for_sites(
        self, kyrgyz_hydromet, issyk_kul_basin, issyk_kul_site, talas_basin, talas_site
    ):
        assert issyk_kul_site.basin.name == issyk_kul_basin.name
        assert talas_site.basin.name == talas_basin.name
        assert Basin.objects.filter(organization=kyrgyz_hydromet).count() == 2

        brs = BasinRegionStandardizer("kyrgyz")
        brs.standardize_basins_for_sites()
        issyk_kul_site.refresh_from_db()
        talas_site.refresh_from_db()

        assert issyk_kul_site.basin.name == "Бассейн оз. Иссык Куль"
        assert talas_site.basin.name == "Бассейн р. Талас"
        assert Basin.objects.filter(organization=kyrgyz_hydromet).count() == 4  # created 2 new basins

    def test_standardize_basins_for_sites_with_unmapped_basin(self, kyrgyz_hydromet, dummy_basin, dummy_site):
        assert dummy_site.basin.name == dummy_basin.name
        assert Basin.objects.filter(organization=kyrgyz_hydromet).count() == 1

        brs = BasinRegionStandardizer("kyrgyz")
        brs.standardize_basins_for_sites()
        dummy_site.refresh_from_db()

        assert dummy_site.basin.name == dummy_basin.name
        assert Basin.objects.filter(organization=kyrgyz_hydromet).count() == 1  # no new basins created

    def test_standardize_basins_for_sites_if_no_sites(self, kyrgyz_hydromet):
        assert Basin.objects.filter(organization=kyrgyz_hydromet).count() == 0

        brs = BasinRegionStandardizer("kyrgyz")
        brs.standardize_basins_for_sites()

        assert Basin.objects.filter(organization=kyrgyz_hydromet).count() == 0

    def test_standardize_regions_for_sites(self, kyrgyz_hydromet, talas_region, talas_site, osh_region, osh_site):
        assert osh_site.region.name == osh_region.name
        assert talas_site.region.name == talas_region.name
        assert Region.objects.filter(organization=kyrgyz_hydromet).count() == 2

        brs = BasinRegionStandardizer("kyrgyz")
        brs.standardize_regions_for_sites()
        osh_site.refresh_from_db()
        talas_site.refresh_from_db()

        assert osh_site.region.name == "Ошская"
        assert talas_site.region.name == "Таласская"
        assert Region.objects.filter(organization=kyrgyz_hydromet).count() == 4  # no new basins created

    def test_standardizing_basin_doesnt_affect_region(self, kyrgyz_hydromet, talas_site, talas_basin, talas_region):
        assert talas_site.basin.name == talas_basin.name
        assert talas_site.region.name == talas_region.name
        assert Basin.objects.filter(organization=kyrgyz_hydromet).count() == 1
        assert Region.objects.filter(organization=kyrgyz_hydromet).count() == 1

        brs = BasinRegionStandardizer("kyrgyz")
        brs.standardize_basins_for_sites()

        talas_site.refresh_from_db()

        assert talas_site.basin.name == "Бассейн р. Талас"
        assert talas_site.region.name == talas_region.name
        assert Basin.objects.filter(organization=kyrgyz_hydromet).count() == 2
        assert Region.objects.filter(organization=kyrgyz_hydromet).count() == 1

    def test_standardize_regions_for_sites_with_unmapped_region(self, kyrgyz_hydromet, dummy_region, dummy_site):
        assert dummy_site.region.name == dummy_region.name
        assert Region.objects.filter(organization=kyrgyz_hydromet).count() == 1

        brs = BasinRegionStandardizer("kyrgyz")
        brs.standardize_regions_for_sites()
        dummy_site.refresh_from_db()

        assert dummy_site.region.name == dummy_region.name
        assert Region.objects.filter(organization=kyrgyz_hydromet).count() == 1  # no new regions created

    def test_standardize_basin_doesnt_create_new_region_twice(
        self, kyrgyz_hydromet, issyk_kul_site, issyk_kul_site_second, issyk_kul_basin, issyk_kul_basin_second
    ):
        assert issyk_kul_site.basin.name == issyk_kul_basin.name
        assert issyk_kul_site_second.basin.name == issyk_kul_basin_second.name
        assert Basin.objects.filter(organization=kyrgyz_hydromet).count() == 2

        brs = BasinRegionStandardizer("kyrgyz")
        brs.standardize_basins_for_sites()

        issyk_kul_site.refresh_from_db()
        issyk_kul_site_second.refresh_from_db()

        assert issyk_kul_site.basin.name == "Бассейн оз. Иссык Куль"
        assert issyk_kul_site_second.basin.name == "Бассейн оз. Иссык Куль"
        assert Basin.objects.filter(organization=kyrgyz_hydromet).count() == 3  # only 1 new basin was created

    def test_standardize_basins_for_virtual_station(self, kyrgyz_hydromet, issyk_kul_basin, issyk_kul_virtual_station):
        assert issyk_kul_virtual_station.basin.name == issyk_kul_basin.name
        assert Basin.objects.filter(organization=kyrgyz_hydromet).count() == 1

        brs = BasinRegionStandardizer("kyrgyz")
        brs.standardize_basins_for_virtual_stations()

        issyk_kul_virtual_station.refresh_from_db()

        assert issyk_kul_virtual_station.basin.name == "Бассейн оз. Иссык Куль"
        assert Basin.objects.filter(organization=kyrgyz_hydromet).count() == 2

    def test_standardize_regions_for_virtual_station(self, kyrgyz_hydromet, talas_region, talas_virtual_station):
        assert talas_virtual_station.region.name == talas_region.name
        assert Region.objects.filter(organization=kyrgyz_hydromet).count() == 1

        brs = BasinRegionStandardizer("kyrgyz")
        brs.standardize_regions_for_virtual_stations()

        talas_virtual_station.refresh_from_db()

        assert talas_virtual_station.region.name == "Таласская"
        assert Region.objects.filter(organization=kyrgyz_hydromet).count() == 2

    def test_cleanup_empty_basins_doesnt_affect_basin_with_connected_sites(
        self, kyrgyz_hydromet, talas_site, talas_basin
    ):
        assert Basin.objects.filter(organization=kyrgyz_hydromet).count() == 1
        assert talas_site.basin.name == talas_basin.name

        brs = BasinRegionStandardizer("kyrgyz")
        deleted_cnt = brs.cleanup_empty_basins()

        assert deleted_cnt == 0
        assert Basin.objects.filter(organization=kyrgyz_hydromet).count() == 1
        assert talas_site.basin.name == talas_basin.name

    def test_cleanup_empty_regions_doesnt_affect_region_with_connected_sites(
        self, kyrgyz_hydromet, talas_virtual_station, talas_region
    ):
        assert Region.objects.filter(organization=kyrgyz_hydromet).count() == 1
        assert talas_virtual_station.region.name == talas_region.name

        brs = BasinRegionStandardizer("kyrgyz")
        deleted_cnt = brs.cleanup_empty_regions()

        assert deleted_cnt == 0
        assert Region.objects.filter(organization=kyrgyz_hydromet).count() == 1
        assert talas_virtual_station.region.name == talas_region.name

    def test_cleanup_basins(
        self, kyrgyz_hydromet, issyk_kul_site, issyk_kul_site_second, issyk_kul_basin, issyk_kul_basin_second
    ):
        assert Basin.objects.filter(organization=kyrgyz_hydromet).count() == 2
        assert issyk_kul_site.basin.name == issyk_kul_basin.name
        assert issyk_kul_site_second.basin.name == issyk_kul_basin_second.name

        brs = BasinRegionStandardizer("kyrgyz")
        brs.standardize_basins_for_sites()
        deleted_cnt = brs.cleanup_empty_basins()

        issyk_kul_site.refresh_from_db()
        issyk_kul_site_second.refresh_from_db()

        assert deleted_cnt == 2
        assert Basin.objects.filter(organization=kyrgyz_hydromet).count() == 1
        assert issyk_kul_site.basin.name == "Бассейн оз. Иссык Куль"
        assert issyk_kul_site_second.basin.name == "Бассейн оз. Иссык Куль"

    def test_cleanup_regions(
        self,
        kyrgyz_hydromet,
        osh_site,
        osh_region,
        manual_hydro_station_kyrgyz,
        virtual_station_kyrgyz,
        site_kyrgyz,
        osh_virtual_station,
    ):
        assert Region.objects.filter(organization=kyrgyz_hydromet).count() == 1
        assert Region.objects.all().count() == 2
        assert osh_site.region.name == osh_region.name
        assert osh_virtual_station.region.name == osh_region.name

        brs = BasinRegionStandardizer("kyrgyz")
        brs.standardize_regions_for_sites()
        brs.standardize_regions_for_virtual_stations()
        deleted_cnt = brs.cleanup_empty_regions()

        osh_site.refresh_from_db()
        osh_virtual_station.refresh_from_db()

        assert deleted_cnt == 1
        assert Region.objects.filter(organization=kyrgyz_hydromet).count() == 1
        assert Region.objects.all().count() == 2
        assert osh_site.region.name == "Ошская"
        assert osh_virtual_station.region.name == "Ошская"
