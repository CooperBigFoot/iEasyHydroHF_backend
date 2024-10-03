import pytest

from sapphire_backend.organizations.management.basin_region_standardizer import BasinRegionStandardizer
from sapphire_backend.organizations.models import Basin


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

    def test_standardize_basins_for_sites(self, kyrgyz_hydromet, chu_basin, chu_site, talas_basin, talas_site):
        assert chu_site.basin.name == chu_basin.name
        assert talas_site.basin.name == talas_basin.name
        assert Basin.objects.filter(organization=kyrgyz_hydromet).count() == 2

        brs = BasinRegionStandardizer("kyrgyz")
        brs.standardize_basins_for_sites()
        chu_site.refresh_from_db()
        talas_site.refresh_from_db()

        assert chu_site.basin.name == "Бассейн р. Чу"
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
