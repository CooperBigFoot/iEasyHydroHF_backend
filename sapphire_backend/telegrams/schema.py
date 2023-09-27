from ninja import Schema


class TelegramInputSchema(Schema):
    telegram: str


class TelegramBulkInputSchema(Schema):
    telegrams: list[str]


class TelegramSectionZeroSchema(Schema):
    date: str
    station_code: str


class TelegramSectionOneSchema(Schema):
    morning_water_level: int
    water_level_trend: int
    water_level_20h_period: int
    water_temperature: int = None
    air_temperature: int = None
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
