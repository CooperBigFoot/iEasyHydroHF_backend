from django.db.models import QuerySet

from .choices import BulletinTagType, BulletinType


class BulletinTemplateQuerySet(QuerySet):
    def for_organization(self, organization):
        return self.filter(organization=organization)

    def for_tag(self, tag):
        return self.filter(tags=tag)

    def default(self):
        return self.filter(is_default=True)

    def daily(self):
        return self.filter(type=BulletinType.DAILY)

    def decadal(self):
        return self.filter(type=BulletinType.DECADAL)


class BulletinTemplateTagQuerySet(QuerySet):
    def for_template(self, template):
        return self.filter(bulletins=template)

    def default(self):
        return self.filter(is_default=True)

    def general(self):
        return self.filter(type=BulletinTagType.GENERAL)

    def data(self):
        return self.filter(type=BulletinTagType.DATA)

    def header(self):
        return self.filter(type=BulletinTagType.HEADER)
