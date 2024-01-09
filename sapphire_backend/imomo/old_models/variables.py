# -*- encoding: UTF-8 -*-
from sqlalchemy import Column, ForeignKey, String, Boolean, Float
from sqlalchemy.orm import relationship

from .orm import ImomoBase, CVMixin
from .units import Unit


class VariableNameCV(ImomoBase, CVMixin):
    """Table for the controlled vocabulary of the variable names.

    The attributes are as defined in the CVMixin class.
    """
    pass


class SpeciationCV(ImomoBase, CVMixin):
    """Table for the controlled vocabulary of speciation types.

    The attributes are as defined in the CVMixin class.
    """
    pass


class SampleMediumCV(ImomoBase, CVMixin):
    """Table for the controlled vocabulary of the sample medium.

    The attributes are as defined in the CVMixin class.
    """
    pass


class ValueTypeCV(ImomoBase, CVMixin):
    """Table for the controlled vocabulary of the value types.

    The attributes are as defined in the CVMixin class.
    """
    pass


class DataTypeCV(ImomoBase, CVMixin):
    """Table for the controlled vocabulary of the data type.

    The attributes are as defined in the CVMixin class.
    """
    pass


class GeneralCategoryCV(ImomoBase, CVMixin):
    """Table for the controlled vocabulary of the general data categories.

    The attributes are as defined in the CVMixin class.
    """
    pass


class Variable(ImomoBase):
    """Table for the different variables used in the system.

    This table contains the canonical list of variables available in the
    database to accompany the data values. This list is populated once
    from an authoritative source and should not require updates afterwards.

    Attributes:
        variable_code: Unique code that identifies the variable in the system.
        variable_name_id: Foreign key to the variable name.
        speciation_id: Foreign key to the speciation type, if any.
        units_id: Foreign key to the corresponding unit.
        sample_medium_id: Foreign key to the medium of the sample.
        value_type_id: Foreign key to the value type term.
        is_regular: Indicates whether the variable is regularly sampled.
        time_support: The period of sampling, if regularly sampled.
        time_units_id: Foreign key to the unit used in the time support.
        data_type_id: Foreign key to the data type in the
                      controlled vocabulary.
        general_category_id: Foreign key to the category in the controlled
                             vocabulary.
        no_data_value: Numeric value used to encode no data value in this
                       variable.
    """
    variable_code = Column(String(50), nullable=False, unique=True, index=True)
    variable_name_id = Column(ForeignKey(VariableNameCV.id), nullable=False)
    speciation_id = Column(ForeignKey(SpeciationCV.id), nullable=False)
    variable_unit_id = Column(ForeignKey(Unit.id), nullable=False)
    sample_medium_id = Column(ForeignKey(SampleMediumCV.id), nullable=False)
    value_type_id = Column(ForeignKey(ValueTypeCV.id), nullable=False)
    is_regular = Column(Boolean, default=False, nullable=False)
    time_support = Column(Float, default=0, nullable=False)
    time_unit_id = Column(ForeignKey(Unit.id), nullable=False, default=103)
    data_type_id = Column(ForeignKey(DataTypeCV.id), nullable=False)
    general_category_id = Column(ForeignKey(GeneralCategoryCV.id),
                                 nullable=False)
    no_data_value = Column(Float, default=-9999, nullable=False)

    variable_name = relationship(VariableNameCV, lazy='joined')
    variable_unit = relationship(
        Unit,
        lazy='joined',
        foreign_keys=variable_unit_id,
    )

    def to_jsonizable(self):
        return {
            'variableId': self.id,
            'variableCode': self.variable_code
        }
