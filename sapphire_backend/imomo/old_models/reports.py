import datetime

# import pytz
from enum import Enum as pyEnum

from sqlalchemy import (
    ARRAY,
    JSON,
    Column,
    Enum,
    ForeignKey,
    Integer,
    Sequence,
    String,
    Text,
)
from sqlalchemy.orm import relationship, validates

from sapphire_backend.imomo import lexicon
from sapphire_backend.imomo.utils import timeseries

from .data_sources import Source, UTCDateTime
from .orm import ImomoBase


class TemplateTypeEnum(pyEnum):
    daily_bulletin = 1
    decadal_bulletin = 2


class ReportingTemplate(ImomoBase):
    id = Column(
        Integer,
        Sequence("reportingtemplate_id_seq"),
        primary_key=True,
    )

    created_on = Column(
        UTCDateTime,
        nullable=False,
        default=lambda: datetime.datetime.now(datetime.UTC),
    )

    type = Column(
        Enum(*[role.name for role in list(TemplateTypeEnum)], name="reporting_template_types"),
        nullable=False,
    )

    data = Column(JSON(), nullable=False, default=dict)
    source_id = Column(ForeignKey(Source.id), nullable=False)
    template_file_url = Column(Text, nullable=False)

    language = Column(String(50), nullable=False, default="ru")

    source = relationship(Source, innerjoin=True, lazy="joined")

    def to_jsonizable(self, public_url=None, exclude=None):
        if exclude is None:
            exclude = []
        exclude.append("template_file_url")
        json_ = super().to_jsonizable(exclude)
        if public_url is not None:
            json_["template_url"] = public_url

        json_["created_on"] = self.created_on.isoformat()

        return json_

    def __repr__(self):
        return f"<ReportingTemplate: {self.type} on source {self.source_id}>"


class ReportSchedule(ImomoBase):
    id = Column(
        Integer,
        Sequence("reportschedule_id_seq"),
        primary_key=True,
    )

    type = Column(
        Enum(*[role.name for role in list(TemplateTypeEnum)], name="reporting_template_types"),
        nullable=False,
    )

    source_id = Column(ForeignKey(Source.id), nullable=False)
    data = Column(JSON(), nullable=False, default=dict)
    subscriptions = Column(ARRAY(String(255)), nullable=False, default=list)
    site_ids = Column(ARRAY(Integer()), nullable=False, default=list)

    source = relationship(Source, innerjoin=True, lazy="joined")

    @validates("subscriptions")
    def validate_subscription(self, key, subscriptions):
        return [lexicon.email(email) for email in subscriptions]

    def to_jsonizable(self, exclude=None):
        exclude = exclude or []
        exclude.append("id")
        exclude.append("data")

        json_ = super().to_jsonizable(exclude)
        if self.type == TemplateTypeEnum.decadal_bulletin.name:
            json_["day_of_decade"] = self.data["day_of_decade"]
            json_["next_issue_date"] = self.get_next_issue_date().isoformat()

        return json_

    def get_next_issue_date(self, date=None):
        if date is not None:
            date = datetime.date(date.year, date.month, date.day)
        else:
            date = datetime.date.today()

        if self.type == TemplateTypeEnum.decadal_bulletin.name:
            issue_date_offset = self.data["day_of_decade"] - 1
            day_of_period = timeseries.get_day_in_period_decade(date)
            if day_of_period <= issue_date_offset:
                start, end, issue_date = timeseries.get_current_period_details(date, issue_date_offset, "decade")
            else:
                start, end, issue_date = timeseries.get_next_period_details(date, issue_date_offset, "decade")

            return issue_date

    def get_issue_dates(self, date=None):
        if date is not None:
            date = datetime.date(date.year, date.month, date.day)
        else:
            date = datetime.date.today()

        if self.type == TemplateTypeEnum.decadal_bulletin.name:
            issue_date_offset = self.data["day_of_decade"] - 1
            start, end, issue_date = timeseries.get_current_period_details(date, issue_date_offset, "decade")
            return start, end, issue_date

    def is_issue_date(self, date=None):
        if date is not None:
            date = datetime.date(date.year, date.month, date.day)
        else:
            date = datetime.date.today()

        start, end, issue_date = self.get_issue_dates(date)

        return date == issue_date

    def get_report_date(self, date=None):
        # get report for past decade, not current
        if self.type == TemplateTypeEnum.decadal_bulletin.name:
            return timeseries.last_date_in_previous_period(date, frequency="decade")

    def __repr__(self):
        return f"<ReportSchedule: {self.type} on source {self.source_id}>"
