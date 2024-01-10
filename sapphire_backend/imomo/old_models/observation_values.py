import calendar
import math
from enum import Enum as pyEnum

from sqlalchemy import Column, DateTime, Float, ForeignKey, String, UniqueConstraint
from sqlalchemy.orm import relationship

from sapphire_backend.imomo.data_structs.standard_data import Variables

from .data_collection_methods import Method, Sample
from .data_qualifiers import Qualifier, QualityControlLevel
from .data_sources import Source
from .monitoring_site_locations import Site
from .offsets import OffsetType
from .orm import CVMixin, ImomoBase, session_required
from .variables import Variable


class StandardCensorCodes(pyEnum):
    not_censored = "nc"
    greater_than = "gt"
    non_detect = "nd"
    present_but_not_quantified = "pnq"
    less_than = "lt"

    @classmethod
    def default_censor_code_term(cls):
        return cls.not_censored


class CensorCodeCV(ImomoBase, CVMixin):
    """Table for the controlled vocabulary of the censor codes.

    The attributes are as defined in the CVMixin class.
    """

    pass


class DerivedFrom(ImomoBase):
    """Table for the identifiers of relationships between derived data values.

    This table differs from the ODM schema in order to support a value
    being derived from multiple values at the same time and ensuring
    transactional integrity at the schema level, rather than at the application
    level.
    """

    pass


class DataValue(ImomoBase):
    """Table for recording all the data values.

    This is the main table for recording data in the system, it is the main
    table for all transactions and data reading. The records are differentiated
    based on the dimension tables in the schema.

    Attributes:
        data_value: The numeric value.
        value_accuracy: The accuracy of the recorded value.
        local_date_time: The local date time.
        utc_offset: The offset value of the date time with respect to the
                    UTC date time, in hours.
        date_time_utc: The UTC date time.
        site_id: The site where the data value was collected.
        variable_id: The variable identifying the data value.
        offset_value: Numerical offset value for the data value.
        offset_type_id: Foreign key to the type of offset, if any.
        censor_code_id: Foreign key to the censoring code controlled
                        vocabulary.
        qualifier_id: Foreign key to an additional qualifier comment.
        method_id: Foreign key to the method used for data collection.
        source_id: Foreign key to the data source that owns it.
        sample_id: Foreign key to the associated laboratory sample, if any.
        derived_from_id: Foreign key to the data value from which the current
                         value was derived, if any.
        quality_control_level_id: Foreign key to a quality qualifier.
        site: ORM relationship to the site instance.
        method: ORM relationship to the method instance.
        variable: ORM relationship to the variable instance.
        source: ORM relationship to the source instance.
        derived_from: ORM relationship to the originating data value, if any.
        quality_control_level: ORM relationship to the quality control
                               qualifier.
    """

    __table_args__ = (
        UniqueConstraint(
            "local_date_time",
            "site_id",
            "variable_id",
            "source_id",
            "quality_control_level_id",
            name="repeated_data_integrity_check",
        ),
    )

    data_value = Column(Float, nullable=False)
    value_accuracy = Column(Float)
    local_date_time = Column(DateTime, nullable=False)
    utc_offset = Column(Float, nullable=False)
    date_time_utc = Column(DateTime, nullable=False)
    ice_phenomena_string = Column(String, nullable=True)
    site_id = Column(ForeignKey(Site.id), nullable=False, index=True)
    variable_id = Column(ForeignKey(Variable.id), nullable=False, index=True)
    offset_value = Column(Float)
    offset_type_id = Column(ForeignKey(OffsetType.id))
    censor_code_id = Column(ForeignKey(CensorCodeCV.id), nullable=False)
    qualifier_id = Column(ForeignKey(Qualifier.id))
    method_id = Column(ForeignKey(Method.id), nullable=False, default=0)
    source_id = Column(ForeignKey(Source.id), nullable=False)
    sample_id = Column(ForeignKey(Sample.id))
    derived_from_id = Column(ForeignKey(DerivedFrom.id))
    quality_control_level_id = Column(ForeignKey(QualityControlLevel.id), nullable=False)

    site = relationship(Site)
    method = relationship(Method)
    variable = relationship(Variable)
    source = relationship(Source)
    derived_from = relationship(DerivedFrom)
    quality_control_level = relationship(QualityControlLevel)
    group_assoc = relationship("Group", cascade="all,delete")

    def __repr__(self):
        if self.variable:
            variable_type = Variables(self.variable.variable_code).name
            unit = self.variable.variable_unit.unit_abbv
        else:
            variable_type = ""
            unit = ""

        return (
            f'<DataValue: {self.data_value} {unit} @ "{self.date_time_utc}" '
            f"(variable: {variable_type}, site_id: {self.site_id})>"
        )

    def to_jsonizable(self):
        if self.ice_phenomena_string is not None:
            return self.jsonize_ice_phenomenae()
        else:
            json_ = super().to_jsonizable(["ice_phenomena_string"])

            if math.isnan(self.data_value):
                json_["data_value"] = None

            return json_

    def jsonize_ice_phenomenae(self):
        ice_phenomenae = []
        for data_value in self.ice_phenomena_data_values:
            ice_phenomena_data_value_json = super().to_jsonizable(["ice_phenomena_string"])
            ice_phenomena_data_value_json["data_value"] = data_value
            ice_phenomenae.append(ice_phenomena_data_value_json)

        return ice_phenomenae

    @property
    def ice_phenomena_data_values(self):
        ice_phenomena_strings = self.ice_phenomena_string.split("|")
        ice_phenomena_data_values = []
        for ice_phenomena_string in ice_phenomena_strings:
            code, intensity = ice_phenomena_string.split(":")
            intensity = float(intensity)

            data_value = int(code)
            if not math.isnan(intensity):
                data_value += intensity / 100.0

            if math.isnan(data_value):
                data_value = None

            ice_phenomena_data_values.append(data_value)
        return ice_phenomena_data_values

    @session_required
    def set_default_quality_control_level_id(self, session):
        """Sets the quality_control_level_id attribute to the default value.

        The value assigned refers to the quality control level for raw data.

        Args:
            session: The session object to use to query the database.
        """
        self.quality_control_level_id = (
            session.query(QualityControlLevel.id)
            .filter(QualityControlLevel.quality_control_level_code == "0")
            .scalar()
        )

    @session_required
    def set_default_censor_code_id(self, session):
        """ "Sets the censor_code_id attribute to the default value.

        The value assigned refers to the censor code for not censored data.

        Args:
            session: The session object to use to query the database.
        """
        self.censor_code_id = session.query(CensorCodeCV.id).filter(CensorCodeCV.term == "nc").scalar()

    def to_xml(self, element):
        element.set("dataValue", str(self.data_value))
        element.set("dateTimeUtc", str(calendar.timegm(self.date_time_utc.timetuple())))
        element.set("localDateTime", str(calendar.timegm(self.local_date_time.timetuple())))
        element.set("utcOffset", str(self.utc_offset))


class DerivedFromGroup(ImomoBase):
    """Table for the specific values from which another value was derived.

    This table creates a many-to-many relationship between the DerivedFrom
    and DataValues table.

    Attributes:
        derived_from_id: Foreign key to the derived from record.
        value_id: Foreign key to the originating data value.
        derived_from: ORM relationship to the derived from instance.
        value: ORM relationship to the originating data value instance.
    """

    __table_args__ = (UniqueConstraint("derived_from_id", "value_id"),)

    derived_from_id = Column(ForeignKey(DerivedFrom.id))
    value_id = Column(ForeignKey(DataValue.id))
    derived_from = relationship(DerivedFrom)
    value = relationship(DataValue)
