from django.db import models


class StationQuerySet(models.QuerySet):
    def active(self):
        return self.filter(is_deleted=False)

    def for_organization(self, organization_uuid: str):
        return self.filter(site__organization__uuid=organization_uuid)

    def for_site(self, site_uuid: str):
        return self.filter(site__uuid=site_uuid)


class HydroStationQuerySet(StationQuerySet):
    def manual(self):
        return self.filter(station_type="M")

    def automatic(self):
        return self.filter(station_type="A")


class MeteoStationQuerySet(StationQuerySet):
    pass


class VirtualStationQuerySet(models.QuerySet):
    def active(self):
        return self.filter(is_deleted=False)

    def for_organization(self, organization_uuid: str):
        return self.filter(organization__uuid=organization_uuid)
