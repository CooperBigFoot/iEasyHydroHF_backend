# -*- encoding: UTF-8 -*-

import datetime
from enum import Enum as pyEnum

from sqlalchemy import Column, String, Text, ForeignKey, Boolean, or_, Enum
from sqlalchemy.orm import validates

from .orm import ImomoBase, CVMixin, UTCDateTime
from sapphire_backend.imomo.utils import validators
from sapphire_backend.imomo.utils.strings import to_str


class TopicCategoryCV(ImomoBase, CVMixin):
    """Table for the controlled vocabulary of the topic categories.

    The attributes are as defined in the CVMixin class.
    """
    pass


class ISOMetadata(ImomoBase):
    """Table for additional metadata to ensure compliance with ISO standards.

    This table holds additional fields that ensure that the information about
    a source is complete with respect to ISO standards.

    Attributes:
        topic_category_id: Foreign key to the topic category controlled
                           vocabulary.
        title: Title for the data from a specific. source.
        abstract: Abstract for the data from a specific source.
        profile_version: Name of the metadata profile used by the source.
        metadata_link: URL link to any additional metadata information.
    """
    topic_category_id = Column(ForeignKey(TopicCategoryCV.id),
                               nullable=False)
    title = Column(String(255), nullable=False, default='Unknown')
    abstract = Column(Text, nullable=False, default='Unknown')
    profile_version = Column(String(255), nullable=False, default='Unknown')
    metadata_link = Column(String(500))


class YearTypeEnum(pyEnum):
    calendar_year = 'calendar_year'
    hydro_year = 'hydro_year'


class Source(ImomoBase):
    """Table for the data sources.

    This table holds the complete specification of all the data sources
    that originated the available data values in the database. This table also
    indicates ownership of the data values.

    These data sources represent real organizations, e.g. Kyrgyzstan
    Hydromet. The term source should be used to refer to organizations inside
    the code.

    Attributes:
        organization: Name of the organization represented by the source
                      (255 char limit).
        source_description: Textual description.
        source_link: URL to further information about the source.
        contact_name: Name of a contact person.
        phone: Contact phone number.
        address: Physical address.
        city: City where the source is located.
        country: Country where the source is located.
        zip_code: Zip code.
        citation: Optional citation text.
        metadata_id: Foreign key to the additional ISO metadata.
    """
    organization = Column(String(255), nullable=False)
    source_description = Column(Text, nullable=True)
    source_link = Column(String(500))
    contact_name = Column(String(255), nullable=False, default='Unknown')
    phone = Column(String(255), nullable=False, default='Unknown')
    email = Column(String(255), nullable=False, default='Unknown')
    citation = Column(Text, nullable=False, default='Unknown')
    iso_metadata_id = Column(ForeignKey(ISOMetadata.id),
                             nullable=False, default=0)
    timezone = Column(String(50))
    language = Column(String(50), nullable=True)

    # full address
    country = Column(String(255), nullable=False)
    city = Column(String(255), nullable=False)
    zip_code = Column(String(255), nullable=False)
    address = Column(String(255), nullable=False)

    # payment
    expires_at = Column(UTCDateTime)

    deleted = Column(Boolean, default=False)

    # setup process finished
    setup_finished = Column(Boolean, default=False)

    # hydro year selection
    year_type = Column(
        Enum(*[type_.name for type_ in YearTypeEnum], name='year_type_enum'),
        nullable=False,
        default=YearTypeEnum.hydro_year.name,
    )

    @classmethod
    def not_deleted(cls):
        return or_(Source.deleted == False, Source.deleted == None)

    @validates('timezone')
    def validate_timezone(self, key, timezone):
        if timezone is not None:
            return validators.timezone_validator(timezone, key)

    @property
    def expires_in_days(self):
        if self.expires_at is not None:
            today = datetime.date.today()
            date_delta = self.expires_at.date() - today
            return date_delta.days

    @property
    def active(self):
        if self.expires_at is None:
            return False
        else:
            return self.expires_in_days >= 0

    def to_jsonizable(self, exclude=None):
        rtn_json = super(Source, self).to_jsonizable(exclude=exclude)

        rtn_json['active'] = self.active

        if rtn_json['expires_at'] is not None:
            rtn_json['expires_at'] = rtn_json['expires_at'].isoformat()

        return rtn_json

    def __repr__(self):
        return '<Source: {name} (id: {id})>'.format(
            name=to_str(self.organization), id=self.id
        )
