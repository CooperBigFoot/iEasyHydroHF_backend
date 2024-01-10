from sqlalchemy import Column, Float, ForeignKey, Text, UniqueConstraint

from .orm import ImomoBase
from .variables import Variable


class Category(ImomoBase):
    """Table for description of categorical data.

    The way to store categorical data values in this schema is to create a
    category entry for the associated variable with an unique real value
    that is tied to the description of the category. This data value is the
    one entered in the corresponding field of the DataValues table.

    Attributes:
        variable_id: Foreign key to the variable associated to this category.
        data_value: Real number value that uniquely identifies the category
                    for the associated variable.
        category_description: Textual description of the category.
    """

    variable_id = Column(ForeignKey(Variable.id))
    data_value = Column(Float)
    category_description = Column(Text, nullable=False)

    __table_args__ = (UniqueConstraint(variable_id, data_value),)
