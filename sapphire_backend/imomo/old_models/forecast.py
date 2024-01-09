

import datetime
# import pytz
import pickle
from dateutil.relativedelta import relativedelta

from enum import Enum as pyEnum
from sqlalchemy import (
    Float,
    Column,
    ForeignKey,
    Enum,
    String,
    JSON,
    Integer,
    Sequence,
    TEXT,
    Boolean,
)
from sqlalchemy.orm import relationship, validates
from .orm import ImomoBase, UTCDateTime

from .monitoring_site_locations import Site
from .users import User
from .data_sources import Source
from sapphire_backend.imomo import errors
from sapphire_backend.imomo.utils import timeseries


class FrequencyEnum(pyEnum):
    pentadal = 1
    decade = 2
    monthly = 3
    seasonal = 4


class ForecastMethodEnum(pyEnum):
    LinearRegression = 1
    Lasso = 2
    ExtraTreesRegressor = 3


class ForecastDataValuesType(pyEnum):
    discharge = 1
    snow_data = 2
    temperature = 3
    precipitation = 4


class ForecastModelStatus(pyEnum):
    idle = 1
    training = 2
    error = 3
    canceled = 4
    success = 5


class ForecastModelInputAssociation(ImomoBase):
    id = Column(
        Integer,
        Sequence('forecastmodelinputassociation_id_seq'),
        primary_key=True,
    )

    forecast_model_id = Column(
        Integer,
        ForeignKey('forecast_model.id'),
        primary_key=True,
    )

    site_id = Column(
        Integer,
        ForeignKey('site.id'),
        primary_key=True,
    )

    data_value_types = Column(JSON(), nullable=False)

    forecast_model = relationship(
        'ForecastModel',
        foreign_keys=forecast_model_id,
        lazy="joined"
    )

    site = relationship(
        'Site',
        foreign_keys=site_id,
        lazy="joined"
    )

    def __repr__(self):
        return '<ForecastModelInputAssociation: {forecast_model_id} -> ' \
               '{site_id} ({data_value_types})>'.format(
                    forecast_model_id=self.forecast_model_id,
                    site_id=self.site_id,
                    data_value_types=self.data_value_types,
                )


class ForecastType(ImomoBase):
    id = Column(Integer, Sequence('forecasttype_id_seq'), primary_key=True)
    created_on = Column(
        UTCDateTime,
        nullable=False,
        default=lambda: datetime.datetime.now(datetime.timezone.utc),
    )

    frequency = Column(
        Enum(
            *[freq.name for freq in list(FrequencyEnum)],
            name='forecast_frequencies'
        ),
        nullable=False,
    )

    name = Column(String(255), nullable=False, index=True)
    source_id = Column(ForeignKey(Source.id), nullable=False, index=True)

    # general forecast type
    issue_date_offset = Column(Integer)

    # seasonal forecast type
    issue_date = Column(UTCDateTime)
    target_period_start = Column(UTCDateTime)
    target_period_end = Column(UTCDateTime)

    forecast_models = relationship('ForecastModel', cascade="all,delete")
    source = relationship(Source)

    def get_forecasting_dates(self, date=None, previous=False):
        if date is None:
            date = datetime.date.today()
        else:
            date = datetime.date(date.year, date.month, date.day)

        if self.is_seasonal():

            issue_day = self.issue_date.day
            issue_month = self.issue_date.month
            issue_date = datetime.date(date.year, issue_month, issue_day)

            if issue_date > date:
                issue_date = issue_date - relativedelta(years=1)

            if previous:
                issue_date = issue_date - relativedelta(years=1)

            period_start = datetime.date(
                issue_date.year,
                self.target_period_start.month,
                self.target_period_start.day
            )

            if issue_date > period_start:
                period_start = period_start + relativedelta(years=1)

            period_end = datetime.date(
                period_start.year,
                self.target_period_end.month,
                self.target_period_end.day
            )

            if period_start > period_end:
                period_end = period_end + relativedelta(years=1)

            return period_start, period_end, issue_date
        else:
            prev_start, prev_end, prev_issue = \
                timeseries.get_previous_period_details(
                    date,
                    self.issue_date_offset,
                    self.frequency,
                )

            curr_start, curr_end, curr_issue = \
                timeseries.get_current_period_details(
                    date,
                    self.issue_date_offset,
                    self.frequency,
                )

            next_start, next_end, next_issue = \
                timeseries.get_next_period_details(
                    date,
                    self.issue_date_offset,
                    self.frequency,
                )

            if date < curr_issue:
                start, end, issue = prev_start, prev_end, prev_issue
            elif date < next_issue:
                start, end, issue = curr_start, curr_end, curr_issue
            else:
                start, end, issue = next_start, next_end, next_issue

            if previous:
                start, end, issue = timeseries.get_previous_period_details(
                    start,
                    self.issue_date_offset,
                    self.frequency,
                )

            return start, end, issue

    @validates('frequency')
    def _validate_frequency(self, key, frequency):
        self.validate_frequency(frequency)
        return frequency

    @staticmethod
    def validate_frequency(frequency):
        if frequency not in FrequencyEnum.__members__:
            raise errors.ValidationError('Invalid forecast frequency.')

    def is_general(self):
        return self.is_general_frequency(self.frequency)

    @staticmethod
    def is_general_frequency(frequency):
        return frequency in (
            FrequencyEnum.pentadal.name,
            FrequencyEnum.decade.name,
            FrequencyEnum.monthly.name,
        )

    def is_seasonal(self):
        return self.is_seasonal_frequency(self.frequency)

    @staticmethod
    def is_seasonal_frequency(frequency):
        return frequency == FrequencyEnum.seasonal.name

    def to_jsonizable(self, exclude=None):
        exclude = exclude or []
        if self.is_seasonal():
            exclude.append('issue_date_offset')
        elif self.is_general():
            exclude.append('issue_date')
            exclude.append('target_period_start')
            exclude.append('target_period_end')

        json_ = super(ForecastType, self).to_jsonizable(exclude)
        json_['created_on'] = self.created_on.isoformat()
        if self.is_seasonal():
            json_['issue_date'] = datetime.date(
                self.issue_date.year,
                self.issue_date.month,
                self.issue_date.day,
            ).isoformat()
            json_['target_period_start'] = datetime.date(
                self.target_period_start.year,
                self.target_period_start.month,
                self.target_period_start.day,
            ).isoformat()
            json_['target_period_end'] = datetime.date(
                self.target_period_end.year,
                self.target_period_end.month,
                self.target_period_end.day,
            ).isoformat()
        return json_

    def __repr__(self):
        return '<ForecastType: {id} - {freq} (source: {source_id})>'.format(
            id=self.id,
            source_id=self.source_id,
            freq=self.frequency,
        )


class ForecastModel(ImomoBase):
    id = Column(Integer, Sequence('forecastmodel_id_seq'), primary_key=True)

    created_on = Column(
        UTCDateTime,
        nullable=False,
        default=lambda: datetime.datetime.now(datetime.timezone.utc),
    )

    created_by_id = Column(ForeignKey(User.id))

    last_modified = Column(UTCDateTime)

    name = Column(String(50), nullable=False, index=True)
    site_id = Column(ForeignKey(Site.id), nullable=False, index=True)

    method = Column(
        Enum(
            *[method.name for method in list(ForecastMethodEnum)],
            name='forecast_methods'
        ),
        nullable=False,
    )
    method_parameters = Column(JSON(), nullable=False, default=dict)
    model_parameters = Column(JSON(), nullable=False, default=dict)

    forecast_type_id = Column(
        Integer,
        ForeignKey(ForecastType.id),
        nullable=False,
    )

    auto_accept = Column(Boolean, nullable=False, default=False)

    # relationships
    site = relationship(Site, lazy='joined')
    created_by = relationship(User, lazy='joined')
    data_inputs = relationship(
        ForecastModelInputAssociation,
        cascade="all,delete",
    )
    forecast_type = relationship(ForecastType, lazy='joined')
    trainings = relationship(
        'ForecastTraining',
        order_by='ForecastTraining.started',
        cascade="all,delete",
    )

    @property
    def latest_training(self):
        if self.trainings:
            latest_training = self.trainings[-1]
            if latest_training.active:
                return latest_training

    def is_general(self):
        return self.forecast_type.is_general()

    def is_seasonal(self):
        return self.forecast_type.is_seasonal()

    def deactivate_training(self, session):
        latest_training = self.latest_training
        if latest_training:
            latest_training.active = False
            session.add(latest_training)

    @property
    def status(self):
        if not self.latest_training:
            return

        return self.latest_training.status

    def to_jsonizable(self, exclude=None):
        exclude = exclude or []
        json_ = super(ForecastModel, self).to_jsonizable(exclude)
        json_['created_on'] = self.created_on.isoformat()
        if self.created_by_id is not None:
            json_['created_by'] = self.created_by.to_jsonizable()

        if self.last_modified is not None:
            json_[
                'last_modified'
            ] = self.last_modified.isoformat()

        json_['data_inputs'] = []
        for data_input in self.data_inputs:
            if data_input.site.site_code.endswith('m'):
                site_code = data_input.site.site_code[:-1]
            else:
                site_code = data_input.site.site_code

            data_input_json = {
                'data_value_types': data_input.data_value_types,
                'site_code': site_code,
                'site_name': data_input.site.site_name,
                'site_id': data_input.site.id,
                'site_type': data_input.site.site_type,
            }

            json_['data_inputs'].append(data_input_json)

        if 'forecast_type' not in exclude:
            json_['forecast_type'] = self.forecast_type.to_jsonizable()

        if 'training' not in exclude:
            if self.latest_training:
                latest_training = self.latest_training.to_jsonizable()
            else:
                latest_training = None

            json_['training'] = latest_training

        return json_

    def __repr__(self):
        if self.latest_training:
            status = self.latest_training.status
        else:
            status = None
        return '<ForecastModel: "{name}" ({id}) - "{frequency}" ' \
               '(status: "{status}", site: {site_id})>'.format(
                    id=self.id,
                    site_id=self.site_id,
                    frequency=self.forecast_type.frequency,
                    status=status,
                    name=self.name.encode('utf-8'),
                )


class ForecastTraining(ImomoBase):
    id = Column(Integer, Sequence('forecasttraining_id_seq'), primary_key=True)
    started = Column(
        UTCDateTime,
        nullable=False,
        default=lambda: datetime.datetime.now(datetime.timezone.utc),
    )
    last_modified = Column(UTCDateTime)
    finished = Column(UTCDateTime)
    active = Column(Boolean, nullable=False, default=True)
    completion = Column(Float, default=0, nullable=False)
    forecaster_object = Column(TEXT)
    evaluator_object = Column(TEXT)
    report_html_url = Column(String(255))
    report_pdf_url = Column(String(255))
    report_xlsx_url = Column(String(255))
    celery_task_id = Column(String(255))

    status = Column(
        Enum(
            *[status.name for status in list(ForecastModelStatus)],
            name='forecast_status'
        ),
        nullable=False,
    )

    status_message = Column(String(255))
    forecast_model_id = Column(Integer, ForeignKey(ForecastModel.id))

    forecast_model = relationship(ForecastModel, lazy="joined")

    results = relationship(
        'ForecastResult',
        order_by='ForecastResult.created_on',
        cascade="all,delete",
    )

    @property
    def forecaster(self):
        if self.status != 'success':
            raise errors.ValidationError(
                "Can't get forecaster from model - current "
                "model status: {status}".format(status=self.status)
            )

        return pickle.loads(self.forecaster_object)

    @forecaster.setter
    def forecaster(self, forecaster_obj):
        self.forecaster_object = pickle.dumps(forecaster_obj)

    @property
    def evaluator(self):
        if self.status != 'success':
            raise errors.ValidationError(
                "Can't get evaluator from model - current "
                "model status: {status}".format(status=self.status)
            )

        return pickle.loads(self.evaluator_object)

    @evaluator.setter
    def evaluator(self, evaluator_obj):
        self.evaluator_object = pickle.dumps(evaluator_obj)

    def to_jsonizable(self, exclude=None):
        exclude = exclude or []
        exclude.append('forecaster_object')
        exclude.append('evaluator_object')
        exclude.append('celery_task_id')
        json_ = super(ForecastTraining, self).to_jsonizable(exclude)

        if self.status_message:
            json_['status_message'] = _(self.status_message)

        json_['started'] = self.started.isoformat()
        json_['last_modified'] = self.last_modified.isoformat()
        if self.finished:
            json_['finished'] = self.finished.isoformat()

        return json_

    def __repr__(self):
        model_name = self.forecast_model.name if self.forecast_model else None
        return '<ForecastTraining: {status} (id: {id}) - model: {name}>'.format(
            status=self.status,
            id=self.id,
            name=model_name.encode('utf-8'),
        )


class ForecastResult(ImomoBase):
    id = Column(Integer, Sequence('forecastresult_id_seq'), primary_key=True)
    created_on = Column(
        UTCDateTime,
        nullable=False,
        default=lambda: datetime.datetime.now(datetime.timezone.utc),
    )
    error_message = Column(String(255))
    valid = Column(Boolean, nullable=False, default=True)

    forecasted_value = Column(Float)
    previous_value = Column(Float)
    training_data_count = Column(Integer)
    percentage = Column(Float)
    relative_error = Column(Float)
    standard_deviation = Column(Float)
    maximum = Column(Float)
    minimum = Column(Float)
    norm = Column(Float)
    issue_date = Column(UTCDateTime)
    period_start = Column(UTCDateTime)
    period_end = Column(UTCDateTime)

    manually = Column(Boolean, nullable=False, default=False)
    accepted = Column(Boolean, nullable=False, default=False)
    accepted_on = Column(UTCDateTime)

    # required for manually entered forecasted values
    forecast_type_id = Column(Integer, ForeignKey(ForecastType.id))
    site_id = Column(Integer, ForeignKey(Site.id))

    site = relationship(Site, lazy="joined")

    forecast_training_id = Column(Integer, ForeignKey(ForecastTraining.id))
    forecast_training = relationship(ForecastTraining, lazy="joined")

    def to_jsonizable(self, exclude=None):
        exclude = exclude or []
        json_ = super(ForecastResult, self).to_jsonizable(exclude)

        if self.error_message:
            json_['error_message'] = _(self.error_message)

        if self.issue_date:
            json_['issue_date'] = datetime.date(
                self.issue_date.year,
                self.issue_date.month,
                self.issue_date.day,
            ).isoformat()

        if self.created_on:
            json_['created_on'] = self.created_on.isoformat()

        if self.period_start:
            json_['period_start'] = datetime.date(
                self.period_start.year,
                self.period_start.month,
                self.period_start.day,
            ).isoformat()

        if self.period_end:
            json_['period_end'] = datetime.date(
                self.period_end.year,
                self.period_end.month,
                self.period_end.day,
            ).isoformat()

        if self.accepted_on:
            json_['accepted_on'] = self.accepted_on.isoformat()

        return json_

    def __repr__(self):
        if self.period_start:
            period_start = datetime.date(
                self.period_start.year,
                self.period_start.month,
                self.period_start.day,
            ).isoformat()
        else:
            period_start = None

        if self.period_end:
            period_end = datetime.date(
                self.period_end.year,
                self.period_end.month,
                self.period_end.day,
            ).isoformat()
        else:
            period_end = None

        return '<ForecastResult: (id: {id}) {value} [{start} - {end}]- valid:' \
               ' {valid}, accepted: {accepted}, manually: {manually}>'.format(
                    value=self.forecasted_value,
                    id=self.id,
                    accepted=self.accepted,
                    valid=self.valid,
                    manually=self.manually,
                    start=period_start,
                    end=period_end,
                )
