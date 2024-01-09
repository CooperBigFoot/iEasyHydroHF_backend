# -*- encoding: UTF-8 -*-
from sqlalchemy import Column, String

from .orm import ImomoBase


class Unit(ImomoBase):
    """Table for the units used in the system.

    This table contains the canonical list of available units for the data
    values.

    Attributes:
        unit_name: Descriptive name, e.g. meter.
        unit_type: Category, e.g. length.
        unit_abbv: Abbreviation, e.g. m.
    """
    unit_name = Column(String(255), nullable=False)
    unit_type = Column(String(255), nullable=False)
    unit_abbv = Column(String(255), nullable=False)

    def __repr__(self):
        return '<Unit {}: {} ({})>'.format(
            self.id,
            self.unit_name.encode('utf-8'),
            self.unit_abbv.encode('utf-8'),
        )
