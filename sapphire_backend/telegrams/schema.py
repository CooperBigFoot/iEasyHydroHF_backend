from typing import Optional, Dict

from ninja import Schema


class TelegramInputSchema(Schema):
    telegram: str


class TelegramBulkInputSchema(Schema):
    telegrams: list[str]


class TelegramWithDateInputSchema(Schema):
    raw: str
    override_date: Optional[str] = None


class TelegramBulkWithDatesInputSchema(Schema):
    telegrams: list[TelegramWithDateInputSchema]


class TelegramSectionZeroSchema(Schema):
    date: str
    station_code: str
    station_name: str


class TelegramSectionOneSchema(Schema):
    morning_water_level: int
    water_level_trend: int
    water_level_20h_period: int
    water_temperature: Optional[int] = None
    air_temperature: Optional[int] = None
    ice_phenomena: list[dict[str, int]]


class TelegramSectionThreeSchema(Schema):
    mean_water_level: list[int]


class TelegramSectionSixSingleSchema(Schema):
    water_level: int
    discharge: int
    cross_section_area: float = None
    maximum_depth: int = None
    date: str


class TelegramOutputSchema(Schema):
    section_zero: TelegramSectionZeroSchema
    section_one: TelegramSectionOneSchema
    section_three: TelegramSectionThreeSchema = None
    section_six: list[TelegramSectionSixSingleSchema] = None


class BulkParseSuccessTelegramSchema(Schema):
    index: int
    telegram: str
    parsed_data: TelegramOutputSchema


class BulkParseErrorTelegramSchema(Schema):
    index: int
    telegram: str
    error: str


class BulkParseOutputSchema(Schema):
    parsed: list[BulkParseSuccessTelegramSchema]
    errors: list[BulkParseErrorTelegramSchema]


class ReportedDischargeSchema(Schema):
    water_level: float
    discharge: float
    cross_section_area: float
    maximum_depth: float
    date: str


class DischargeOverviewSchema(Schema):
    index: int
    station_code: str
    station_name: str
    telegram_day_date: str
    telegram_day_morning_water_level: float
    telegram_day_water_level_trend: float
    trend_ok: bool
    previous_day_date: str
    previous_day_morning_water_level: Optional[float] = None
    previous_day_evening_water_level: float
    previous_day_water_level_average: Optional[float] = None
    reported_discharge: list


class DailyOverviewOutputSchema(Schema):
    discharge: list[DischargeOverviewSchema]
    meteo: list[dict]  # list[MeteoTelegramOverviewSchema]
    discharge_codes: list[tuple]
    meteo_codes: list[tuple]


class TimeData(Schema):
    water_level_new: Optional[int] = None
    water_level_old: Optional[int] = None
    discharge_new: Optional[float] = None
    discharge_old: Optional[float] = None


class DataProcessingDayTimes(Schema):
    morning: TimeData
    evening: TimeData
    average: TimeData


class DataProcessingDate(Schema):
    dates: Dict[str, DataProcessingDayTimes]


class DataProcessingOverviewOutputSchema(Schema):
    codes: Dict[str, DataProcessingDate]
