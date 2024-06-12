from django.db.models import QuerySet

from .choices import BulletinType


class BulletinTemplateQuerySet(QuerySet):
    def for_organization(self, organization):
        return self.filter(organization=organization)

    def default(self):
        return self.filter(is_default=True)

    def daily(self):
        return self.filter(type=BulletinType.DAILY)

    def decadal(self):
        return self.filter(type=BulletinType.DECADAL)
