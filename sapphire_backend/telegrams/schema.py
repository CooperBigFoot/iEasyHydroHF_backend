from datetime import datetime
from typing import Any

from ninja import FilterSchema, Schema

from sapphire_backend.utils.daily_precipitation_mapper import DailyPrecipitationCodeMapper
from sapphire_backend.utils.ice_phenomena_mapper import IcePhenomenaCodeMapper


class TelegramWithDateInputSchema(Schema):
    raw: str
    override_date: str | None = None


class TelegramBulkWithDatesInputSchema(Schema):
    telegrams: list[TelegramWithDateInputSchema]


class TelegramSectionZeroSchema(Schema):
    date: str
    station_code: str
    station_name: str


class IcePhenomenaSchema(Schema):
    code: int
    intensity: int | None
    description: str

    @staticmethod
    def resolve_description(obj):
        return IcePhenomenaCodeMapper(obj["code"]).get_description()


class DailyPrecipitationSchema(Schema):
    precipitation: int | float
    duration_code: int
    description: str

    @staticmethod
    def resolve_description(obj):
        return DailyPrecipitationCodeMapper(obj["duration_code"]).get_description()


class TelegramSectionOneSchema(Schema):
    date: str
    morning_water_level: int
    water_level_trend: int
    water_level_20h_period: int
    water_temperature: float | None = None
    air_temperature: int | None = None
    ice_phenomena: list[IcePhenomenaSchema] | None = None
    daily_precipitation: DailyPrecipitationSchema | None = None


class TelegramSectionThreeSchema(Schema):
    mean_water_level: list[int]


class TelegramSectionSixSingleSchema(Schema):
    water_level: int
    discharge: float
    cross_section_area: float = None
    maximum_depth: float | None = None
    date: str


class TelegramSectionEightSchema(Schema):
    decade: int
    timestamp: str
    precipitation: int | None
    temperature: float | None


class NewOldMetrics(Schema):
    water_level_new: int | None = None
    water_level_old: int | None = None
    discharge_new: float | None = None
    discharge_old: float | None = None


class DataProcessingDayTimes(Schema):
    morning: NewOldMetrics
    evening: NewOldMetrics
    average: NewOldMetrics


class SingleDateWithDataProcessingDayTimes(Schema):
    date: str
    metrics: DataProcessingDayTimes


class DailyOverviewSingleSchema(Schema):
    station_code: str
    station_name: str
    telegram_day_date: str
    previous_day_date: str
    section_one: TelegramSectionOneSchema
    section_two: list[TelegramSectionOneSchema]
    section_six: list[TelegramSectionSixSingleSchema]
    section_eight: TelegramSectionEightSchema | None
    calc_trend_ok: bool
    calc_previous_day_water_level_average: int | None = None
    db_previous_day_morning_water_level: int | None = None


class SaveDataOverviewSingleSchema(Schema):
    station_code: str
    station_name: str
    telegram_day_date: str
    wl_q_triplets: list[SingleDateWithDataProcessingDayTimes]
    section_one_two: list[TelegramSectionOneSchema]
    section_six: list[TelegramSectionSixSingleSchema]
    section_eight: TelegramSectionEightSchema | None
    type: str


class ReportedDischargePointsOutputSchema(Schema):
    date: str
    h: int
    q: float
    f: float | None


class TelegramOverviewErrorOutputSchema(Schema):
    index: int
    telegram: str
    error: str


class TelegramOverviewOutputSchema(Schema):
    daily_overview: list[DailyOverviewSingleSchema]
    data_processing_overview: dict[str, list[tuple[str, DataProcessingDayTimes]]]
    reported_discharge_points: dict[str, list[ReportedDischargePointsOutputSchema]]
    save_data_overview: list[SaveDataOverviewSingleSchema]
    discharge_codes: list[tuple[str, str]]
    meteo_codes: list[tuple[str, str]]
    errors: list[TelegramOverviewErrorOutputSchema]


class TelegramReceivedOutputSchema(Schema):
    id: int
    telegram: str
    valid: bool
    created_date: datetime
    station_code: str | None = None
    decoded_values: Any | None = None
    acknowledged: bool


class TelegramReceivedFilterSchema(FilterSchema):
    created_date: str = None
    only_pending: bool = True
    only_invalid: bool | None = False
    station_codes: str | None = None
    basin_uuid: str | None = None


class InputAckSchema(Schema):
    ids: list[int]
