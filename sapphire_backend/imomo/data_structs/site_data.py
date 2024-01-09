# -*- encoding: UTF-8 -*-


class SiteData(object):

    def __init__(self, site_id, groups):
        self._site_id = site_id
        self._groups = groups

    @property
    def site_id(self):
        return self._site_id

    @site_id.setter
    def site_id(self, value):
        self._site_id = value

    @property
    def groups(self):
        return self._groups

    @groups.setter
    def groups(self, value):
        self._groups = value

    def to_jsonizable(self):
        return {'siteId': self.site_id,
                'groups': [group.to_jsonizable() for group in self.groups]}
