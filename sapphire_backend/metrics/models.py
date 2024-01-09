from django.db import connection, models
from django.utils.translation import gettext_lazy as _


class HydrologicalMetric(models.Model):
    class MeasurementType(models.TextChoices):
        MANUAL = "M", _("Manual")
        AUTOMATIC = "A", _("Automatic")
        CALCULATED = "C", _("Calculated")
        IMPORTED = "I", _("Imported")
        UNKNOWN = "U", _("Unknown")

    class MetricName(models.TextChoices):
        WATER_LEVEL_DAILY_MEASUREMENT = "WLDM", _("Water level daily measurement")  # '0001'
        WATER_LEVEL_DAILY_AVERAGE_MEASUREMENT = "WLADM", _("Water level daily average measurement")  # '0002'
        WATER_LEVEL_DAILY_AVERAGE_ESTIMATION = "WLDAE", _("Water level daily average estimation")  # '0003'

        WATER_DISCHARGE_DAILY_ESTIMATION = "WDDE", _("Water discharge daily estimation")  # '0005'
        WATER_DISCHARGE_DAILY_AVERAGE_ESTIMATION = "WDDAE", _("Water discharge daily average estimation")  # '0010'
        WATER_DISCHARGE_FIVEDAY_AVERAGE = "WDFA", _("Water discharge fiveday average")  # '0015'
        WATER_DISCHARGE_DECADE_AVERAGE = "WDDCA", _("Water discharge decade average")  # '0008'

        WATER_TEMPERATURE_OBSERVATION = "WTO", _("Water temperature observation")  # '0013'
        AIR_TEMPERATURE_OBSERVATION = "ATO", _("Air temperature observation")  # '0014'
        ICE_PHENOMENA_OBSERVATION = "IPO", _("Ice phenomena observation")  # '0011'

        WATER_DISCHARGE_DAILY_MEASUREMENT = "WDDM", _("Water discharge daily measurement")  # '0004'
        WATER_LEVEL_DECADAL_MEASUREMENT = "WLDCM", _("Water level decadal measurement")  # '0012'
        RIVER_CROSS_SECTION_AREA_MEASUREMENT = "RCSAM", _("River cross section area measurement")  # '0006'
        MAXIMUM_DEPTH_MEASUREMENT = "MDM"
        _("Maximum depth measurement")  # '0007'

        WATER_DISCHARGE_DECADE_AVERAGE_HISTORICAL = "WDDCAH", _("Water discharge decade average historical")  # '0020'

        # WATER_DISCHARGE_MAXIMUM_RECOMMENDATION = "WDMR", _(
        #    "Water discharge maximum recommendation")  # '0009' # TODO more of a HydrologicalStation model field

    class MetricUnit(models.TextChoices):
        WATER_LEVEL = "cm", _("centimeter")  # '0001'
        WATER_DISCHARGE = "m^3/s", _("cubic meters per second")  # '0005'
        TEMPERATURE = "degC", _("degree celsius")  # '0013'
        ICE_PHENOMENA_OBSERVATION = "dimensionless", _("dimensionless")  # '0011'
        AREA = "m^2", _("square meter")  # '0006'

    timestamp = models.DateTimeField(primary_key=True, verbose_name=_("Timestamp"))
    min_value = models.DecimalField(
        verbose_name=_("Minimum value"), max_digits=15, decimal_places=5, null=True, blank=True
    )
    avg_value = models.DecimalField(verbose_name=_("Average value"), max_digits=15, decimal_places=5)
    max_value = models.DecimalField(
        verbose_name=_("Maximum value"), max_digits=15, decimal_places=5, null=True, blank=True
    )
    unit = models.CharField(verbose_name=_("Unit"), choices=MetricUnit, blank=True, max_length=20)
    value_type = models.CharField(
        verbose_name=_("Value type"),
        choices=MeasurementType,
        default=MeasurementType.UNKNOWN,
        max_length=2,
        blank=False,
    )
    metric_name = models.CharField(
        verbose_name=_("Metric name"),
        choices=MetricName,
        max_length=20,
        blank=False,
    )
    station = models.ForeignKey("stations.HydrologicalStation", verbose_name=_("Station"), on_delete=models.PROTECT)

    sensor_identifier = models.CharField(verbose_name=_("Sensor identifier"), blank=True, max_length=50)
    sensor_type = models.CharField(verbose_name=_("Sensor type"), blank=True, max_length=50)

    class Meta:
        verbose_name = _("Hydrological metric")
        verbose_name_plural = _("Hydrological metrics")
        ordering = ["-timestamp"]

    def __str__(self):
        return f"{self.metric_name}, {self.station.name} on {self.timestamp}"

    def save(self) -> None:
        min_value = self.min_value
        max_value = self.max_value
        avg_value = self.avg_value

        if self.min_value is None:
            min_value = "NULL"
        max_value = self.max_value
        if self.max_value is None:
            max_value = "NULL"
        if self.avg_value is None:
            avg_value = "NULL"
        sql_query = """
        INSERT INTO metrics_hydrologicalmetric
        (timestamp, station_id, metric_name, min_value, avg_value, max_value,
        unit, value_type, sensor_identifier, sensor_type)
        VALUES ('{timestamp}'::timestamp, {station_id}, '{metric_name}', {min_value},
        {avg_value}, {max_value}, '{unit}', '{value_type}', '{sensor_identifier}', '{sensor_type}');
        """.format(
            timestamp=self.timestamp,
            station_id=self.station_id,
            metric_name=self.metric_name,
            min_value=min_value,
            avg_value=avg_value,
            max_value=max_value,
            unit=self.unit,
            value_type=self.value_type,
            sensor_identifier=self.sensor_identifier,
            sensor_type=self.sensor_type,
        )

        with connection.cursor() as cursor:
            try:
                cursor.execute(sql_query)
            except:
                raise Exception("Hydro metric problem")


class MeteorologicalMetric(models.Model):
    class MeasurementType(models.TextChoices):
        IMPORTED = "I", _("Imported")
        UNKNOWN = "U", _("Unknown")

    class MetricName(models.TextChoices):
        AIR_TEMPERATURE_DECADE_AVERAGE = "ATDCA", _("Air temperature decade average")  # 0016
        AIR_TEMPERATURE_MONTH_AVERAGE = "ATMA", _("Air temperature month average")  # 0017
        PRECIPITATION_DECADE_AVERAGE = "PDCA", _("Precipitation decade average")  # 0018
        PRECIPITATION_MONTH_AVERAGE = "PMA", _("Precipitation month average")  # 0019

    class MetricUnit(models.TextChoices):
        TEMPERATURE = "degC", _("degree celsius")  # 0016
        PRECIPITATION = "mm/day", _("millimeters per day")  # 0018

    timestamp = models.DateTimeField(primary_key=True, verbose_name=_("Timestamp"))
    value = models.DecimalField(verbose_name=_("Value"), max_digits=10, decimal_places=5)
    value_type = models.CharField(
        verbose_name=_("Value type"),
        choices=MeasurementType,
        default=MeasurementType.UNKNOWN,
        max_length=2,
        blank=False,
    )
    metric_name = models.CharField(
        verbose_name=_("Metric name"),
        choices=MetricName,
        max_length=20,
        blank=False,
    )
    unit = models.CharField(verbose_name=_("Unit"), choices=MetricUnit, max_length=20, blank=True)
    station = models.ForeignKey("stations.MeteorologicalStation", verbose_name=_("Station"), on_delete=models.PROTECT)

    class Meta:
        verbose_name = _("Meteorological metric")
        verbose_name_plural = _("Meteorological metrics")
        ordering = ["-timestamp"]

    def __str__(self):
        return f"{self.metric_name}, {self.station.name} on {self.timestamp}"

    def save(self) -> None:
        sql_query = """
        INSERT INTO metrics_meteorologicalmetric (timestamp, station_id, metric_name, value, value_type, unit )
        VALUES ('{timestamp}'::timestamp, {station_id}, '{metric_name}', {value}, '{value_type}', '{unit}');
        """.format(
            timestamp=self.timestamp,
            station_id=self.station_id,
            metric_name=self.metric_name,
            value=self.value,
            value_type=self.value_type,
            unit=self.unit,
        )

        with connection.cursor() as cursor:
            cursor.execute(sql_query)
