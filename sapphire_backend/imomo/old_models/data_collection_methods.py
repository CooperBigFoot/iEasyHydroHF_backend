# -*- encoding: UTF-8 -*-
from enum import Enum as pyEnum
from sqlalchemy import Column, Text, String, ForeignKey

from .orm import ImomoBase, CVMixin


class StandardMethods(pyEnum):
    gauge_measurement = 1
    water_flow_measurement = 2
    water_level_averaging = 3
    decade_discharge_averaging = 4
    maximum_discharge_recommendation = 5


class Method(ImomoBase):
    """Table for data collection methods.

    This table is used to identify the methods used to make or collection
    a physical observation.

    Attributes:
        method_description: Textual description of the method.
        method_link: URL to more information on the method (500 char limit).
    """
    method_description = Column(Text, nullable=False)
    method_link = Column(String(500))


class SampleTypeCV(ImomoBase, CVMixin):
    """Table for the controlled vocabulary of the standard sample types.

    The attributes are as defined in the CVMixin class.
    """
    pass


class LabMethod(ImomoBase):
    """Table for the laboratory methods.

    This table is used to identify laboratory methods that result in samples
    recorded in the data values table.

    Attributes:
        lab_name: The laboratory's name (255 char limit).
        lab_organization: Name (255 char limit) of the
                          organization associated with the laboratory.
        lab_method_name: The method's name (255 char limit) .
        lab_method_description: Text describing the method.
        lab_method_link: URL to more information on the method
                         (500 char limit).
    """
    lab_name = Column(String(255), nullable=False, default='Unknown')
    lab_organization = Column(String(255), nullable=False, default='Unknown')
    lab_method_name = Column(String(255), nullable=False, default='Unknown')
    lab_method_description = Column(Text, nullable=False, default='Unknown')
    lab_method_link = Column(String(500))


class Sample(ImomoBase):
    """Table for laboratory samples.

    This table is used to identify data values that are the result of the
    analysis of a physical sample in the laboratory, where the method used
    is recorded in the LabMethods table.

    Attributes:
        sample_type_id: Foreign key to the term in the sample type controlled
                     vocabulary.
        lab_sample_code: Unique tracking code that identifies the sample in
                         the laboratory (50 char limit).
        lab_method_id: Foreign key to the associated laboratory method.
    """
    sample_type_id = Column(ForeignKey(SampleTypeCV.id), nullable=False)
    lab_sample_code = Column(String(50), nullable=False, unique=True)
    lab_method_id = Column(ForeignKey(LabMethod.id),
                           nullable=False, default=0)
