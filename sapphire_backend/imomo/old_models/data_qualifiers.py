from enum import Enum as pyEnum

from sqlalchemy import Column, String, Text

from .orm import ImomoBase


class StandardQualityControlLevels(pyEnum):
    raw_data = "0"
    quality_controlled_data = "1"
    derived_products = "2"
    interpreted_products = "3"
    knowledge_products = "4"


class QualityControlLevel(ImomoBase):
    """Table for the quality control levels of the data.

    This table is used to record the level of quality control
    processing that a data value has been subjected to.

    Attributes:
        quality_control_level_code: Unique string identifier for the
                                    quality control level (50 char limit).
        definition: Short definition of the quality control level
                    (255 char limit).
        explanation: Textual explanation of the quality control level.
    """

    quality_control_level_code = Column(String(50), nullable=False, unique=True, index=True)
    definition = Column(String(255), nullable=False)
    explanation = Column(Text, nullable=False)


class Qualifier(ImomoBase):
    """Table for qualifier comments for the data.

    This table is used to record any additional qualifiers or comments on the
    data values.

    Attributes:
        qualifier_code: Optional short code that identifies the qualifier
                        (50 char limit).
        qualifier_description: Textual description of the qualifier comment.
    """

    qualifier_code = Column(String(50))
    qualifier_description = Column(Text, nullable=False)
