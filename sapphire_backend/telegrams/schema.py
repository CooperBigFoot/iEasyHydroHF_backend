from ninja import Schema


class TelegramWithDateInputSchema(Schema):
    raw: str
    override_date: str | None = None


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
    water_temperature: float | None = None
    air_temperature: int | None = None
    ice_phenomena: list[dict[str, int]]


class TelegramSectionThreeSchema(Schema):
    mean_water_level: list[int]


class TelegramSectionSixSingleSchema(Schema):
    water_level: int
    discharge: float
    cross_section_area: float = None
    maximum_depth: float | None = None
    date: str


class NewOldMetrics(Schema):
    water_level_new: int | None = None
    water_level_old: int | None = None
    discharge_new: float | None = None
    discharge_old: float | None = None


class DataProcessingDayTimes(Schema):
    morning: NewOldMetrics
    evening: NewOldMetrics
    average: NewOldMetrics


class DailyOverviewSingleSchema(Schema):
    station_code: str
    station_name: str
    telegram_day_date: str
    previous_day_date: str
    section_one: TelegramSectionOneSchema
    section_six: list[TelegramSectionSixSingleSchema]
    section_eight: None  # TODO when meteo parsing is implemented
    calc_trend_ok: bool
    calc_previous_day_water_level_average: int | None = None
    db_previous_day_morning_water_level: int | None = None


class SaveDataOverviewSingleSchema(Schema):
    station_code: str
    station_name: str
    telegram_day_date: str
    previous_day_date: str
    previous_day_data: DataProcessingDayTimes
    telegram_day_data: DataProcessingDayTimes
    section_six: list[TelegramSectionSixSingleSchema]
    section_eight: None  # TODO when meteo parsing is implemented
    type: str


class TelegramOverviewOutputSchema(Schema):
    daily_overview: list[DailyOverviewSingleSchema]
    data_processing_overview: dict[str, list[tuple[str, DataProcessingDayTimes]]]
    save_data_overview: list[SaveDataOverviewSingleSchema]
    discharge_codes: list[tuple[str, str]]
    meteo_codes: list[tuple[str, str]]
    errors: list[str]
