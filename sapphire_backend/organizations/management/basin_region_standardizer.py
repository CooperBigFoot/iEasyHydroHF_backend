from tqdm import tqdm

from sapphire_backend.organizations.models import Basin, Organization, Region
from sapphire_backend.stations.models import Site


class BasinRegionStandardizer:
    def __init__(self, organization: str):
        self.organization = self._get_organization(organization)
        self.region_map = self._organization_map[organization]["region_mapping"]
        self.basin_map = self._organization_map[organization]["basin_mapping"]

    @property
    def _organization_map(self):
        return {
            "kyrgyz": {
                "name": "КыргызГидроМет",
                "region_mapping": {
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
                },
                "basin_mapping": {
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
                },
            }
        }

    def _get_organization(self, organization: str):
        if organization not in self._organization_map:
            raise ValueError(f"{organization} is not supported. Currently supporting: {self._organization_map.keys()}")

        try:
            return Organization.objects.get(name=self._organization_map[organization]["name"])
        except Organization.DoesNotExist:
            raise ValueError(
                f"Can't find organization with the name {self._organization_map[organization]['name']},"
                f" check the _organization_map"
            )

    def standardize_regions(self):
        sites = Site.objects.filter(organization=self.organization).select_related("region")
        for site in tqdm(sites, desc="Standardizing site regions", total=sites.count()):
            old_region = site.region
            if old_region.name not in self.region_map:
                pass
            new_region = Region.objects.get_or_create(
                name=self.region_map[old_region.name],
                defaults={"secondary_name": "", "organization": self.organization, "bulletin_order": 0},
            )
            site.region = new_region
            site.save()

    def standardize_basins(self):
        sites = Site.objects.filter(organization=self.organization).select_related("basin")
        for site in tqdm(sites, desc="Standardizing site basins", total=sites.count()):
            old_basin = site.basin
            if old_basin.name not in self.region_map:
                pass
            new_basin = Basin.objects.get_or_create(
                name=self.region_map[old_basin.name],
                defaults={"secondary_name": "", "organization": self.organization, "bulletin_order": 0},
            )
            site.basin = new_basin
            site.save()
