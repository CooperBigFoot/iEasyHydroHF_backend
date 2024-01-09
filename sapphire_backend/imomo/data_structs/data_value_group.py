# -*- encoding: UTF-8 -*-
try:
    import xml.etree.cElementTree as ElementTree
except ImportError:
    import xml.etree.ElementTree as ElementTree

ET = ElementTree

class DataValuesGroups(object):

    def __init__(self):
        self._group_id = None
        self._values = []

    @property
    def group_id(self):
        return self._group_id

    @group_id.setter
    def group_id(self, value):
        self._group_id = value

    @property
    def values(self):
        return self._values

    @values.setter
    def values(self, value):
        self._values = value

    def to_jsonizable(self):
        return {
            'groupId': self.group_id,
            'values': [value.to_jsonizable() for value in self.values]
        }

    def to_xml(self, element):
        element.set('groupId', str(self.group_id))
        element.set('valueCount', str(len(self.values)))
        for value in self.values:
            subelement = ET.SubElement(element, value.__class__.__name__[:-1])
            value.to_xml(subelement)
