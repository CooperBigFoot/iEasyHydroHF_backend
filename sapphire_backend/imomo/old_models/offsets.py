from sqlalchemy import Column, ForeignKey, Text

from .orm import ImomoBase
from .units import Unit


class OffsetType(ImomoBase):
    """Table for offset types used in some data values.

    The offset types represent the appropriate datum used as a reference
    for a data value, e.g. "depth below or above ground".

    Attributes:
        offset_units_id: Foreign key to the corresponding unit.
        offset_description: Text description of the offset.
    """

    offset_units_id = Column(ForeignKey(Unit.id), nullable=False)
    offset_description = Column(Text, nullable=False)
