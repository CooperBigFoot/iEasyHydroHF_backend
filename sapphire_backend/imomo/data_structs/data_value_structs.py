# -*- encoding: UTF-8 -*-
from collections import namedtuple
import datetime

from imomo import ElementTree
from imomo.models import DataValue


class DischargeMeasurementPair(object):
    """Auxiliary data structure to serialize tuples of discharge and water
    level data values.

    Attributes:
        discharge: The discharge data value.
        water_level: The water level data value.
    """
    def __init__(self, discharge, water_level):
        self.discharge = discharge
        self.water_level = water_level

    @property
    def date(self):
        if self.discharge is not None:
            return self.discharge.local_date_time
        if self.water_level is not None:
            return self.water_level.local_date_time
        return None

    def to_jsonizable(self):
        """Serializes the object into a JSON-compatible dictionary.

        Returns:
            Dictionary that can be serialized into JSON.
        """
        discharge = self.discharge.to_jsonizable()
        # virtual sites has average data but doesn't have water level
        if self.water_level is not None:
            water_level = self.water_level.to_jsonizable()
        else:
            water_level = None
        return {
            'discharge': discharge,
            'water_level': water_level
        }

    def to_xml(self, element):
        sub_element_water_level = ElementTree.SubElement(element, 'WaterLevel')
        sub_element_discharge = ElementTree.SubElement(element, 'Discharge')
        self.discharge.to_xml(sub_element_discharge)
        self.water_level.to_xml(sub_element_water_level)


class DischargeTuple(DischargeMeasurementPair):
    """Auxiliary data structure to serialize tuples of discharge, water level,
    maximum depth and river cross section area values.

    See DischargeMeasurementPair for description on the discharge and water
    level attributes.

    Attributes:
        maximum_depth: The maximum depth used for the discharge measurement.
        river_free_area: The cross section of the river used for the discharge
            measurement.
    """
    def __init__(self, discharge, water_level,
                 maximum_depth=None, free_river_area=None):
        super(DischargeTuple, self).__init__(discharge, water_level)
        self.maximum_depth = maximum_depth
        self.free_river_area = free_river_area

    @property
    def date(self):
        super_date = super(DischargeTuple, self).date
        if super_date is not None:
            return super_date
        if self.free_river_area is not None:
            return self.free_river_area.local_date_time
        if self.maximum_depth is not None:
            return self.maximum_depth.local_date_time
        return None

    def to_jsonizable(self):
        """Serializes the object into a JSON-compatible dictionary.

        Returns:
            Dictionary that can be serialized into JSON.
        """
        base_dict = super(DischargeTuple, self).to_jsonizable()
        if self.maximum_depth is not None:
            base_dict['maximum_depth'] = self.maximum_depth.to_jsonizable()
        if self.free_river_area is not None:
            base_dict['free_river_area'] = self.free_river_area.to_jsonizable()
        return base_dict


class AdditionalMeasurementPair(object):
    """Auxiliary data structure to serialize tuples of air and water temperature
    and ice phenomena data values.

    Attributes:
        water_temperature: The water temperature data value.
        air_temperature: The air temperature data value.
        ice_phenomena: The ice phenomena data value
    """
    def __init__(self, water_temperature, air_temperature, ice_phenomenae):
        self.water_temperature = water_temperature
        self.air_temperature = air_temperature
        self.ice_phenomena = ice_phenomenae

    @property
    def date(self):
        if self.water_temperature is not None:
            return self.water_temperature.local_date_time
        if self.air_temperature is not None:
            return self.air_temperature.local_date_time
        if self.ice_phenomena is not None:
            return self.ice_phenomena.local_date_time
        return None

    def to_jsonizable(self):
        """Serializes the object into a JSON-compatible dictionary.

        Returns:
            Dictionary that can be serialized into JSON.
        """
        base_dict = dict()

        if self.water_temperature:
            base_dict['water_temperature'] = self.water_temperature.to_jsonizable()
        if self.air_temperature:
            base_dict['air_temperature'] = self.air_temperature.to_jsonizable()
        if self.ice_phenomena:
            base_dict['ice_phenomenae'] = self.ice_phenomena.to_jsonizable()

        return base_dict

    def to_xml(self, element):
        sub_element_water_temperature = ElementTree.SubElement(element, 'WaterTemperature')
        sub_element_air_temperature = ElementTree.SubElement(element, 'AirTemperature')
        self.water_temperature.to_xml(sub_element_water_temperature)
        self.air_temperature.to_xml(sub_element_air_temperature)


class JournalData(dict):
    """Auxiliary data structure to serialize the data for the journal display.

    This structure extends a dictionary where the keys are the site IDs,
    and the values are a dictionary with daily data and discharge data.
    Where the daily data and discharge data are lists of
    daily triplets and discharge tuples, respectively.

    Attributes:
        journal_url: The URL to retrieve the generated journal excel file.
    """
    journal_url = None

    def add_discharge_site_data(
            self,
            site_id,
            daily_data,
            discharge_data,
            decadal_data,
            site=None
    ):
        self[site_id] = {}
        self[site_id]['daily_data'] = daily_data
        self[site_id]['discharge_data'] = discharge_data
        self[site_id]['decadal_data'] = decadal_data
        self[site_id]['site'] = site

    def add_meteo_site_data(
            self,
            site,
            decadal_data,
            month_data,
    ):
        self[str(site.id)] = {
            'decadal_data': decadal_data,
            'month_data': month_data,
            'site': site
        }

    def to_jsonizable(self):
        """Serializes the object into a JSON-compatible dictionary.

        Returns:
            Dictionary that can be serialized into JSON.
        """
        json_dict = {
            # 'journal_url': self.journal_url,
            'site_data': {},
        }
        site_dict = json_dict['site_data']
        for site_id, site_data in self.iteritems():
            site_dict[site_id] = site_data
            for key, data in site_data.iteritems():
                if key == 'site':
                    site_data[key] = data.to_jsonizable()
                else:
                    new_data = []
                    for value in data:
                        if isinstance(value, dict):
                            new_data.append(value)
                        else:
                            new_data.append(value.to_jsonizable())
                    site_data[key] = new_data
        return json_dict


class DailyTriplet(object):
    """Auxiliary data structure that collects the daily measurements and
    calculated discharge.

    Attributes:
        eight_data: The water level and discharge at 08:00
        twenty_data: The water level and discharge at 20:00
        average_data: The water level and discharge in average.
    """
    def __init__(self):
        self.eight_data = None
        self.twenty_data = None
        self.average_data = None
        self.additional_data = None

    def add_eight_data(self, eight_data):
        """Add the discharge measurement pair for 08:00"""
        self.eight_data = eight_data

    def add_twenty_data(self, twenty_data):
        """Add the discharge measurement pair for 20:00"""
        self.twenty_data = twenty_data

    def add_average_data(self, average_data):
        """Add the discharge measurement pair for 12:00"""
        self.average_data = average_data

    def add_additional_data(self, additional_data):
        """Add water/air temp and ice measurements"""
        self.additional_data = additional_data

    @property
    def date(self):
        if self.eight_data is not None:
            if self.eight_data.water_level is not None:
                return self.eight_data.water_level.local_date_time
            else:
                return self.eight_data.discharge.local_date_time
        if self.twenty_data is not None:
            if self.twenty_data.water_level is not None:
                return self.twenty_data.water_level.local_date_time
            else:
                return self.twenty_data.discharge.local_date_time
        if self.average_data is not None:
            if self.average_data.water_level is not None:
                return self.average_data.water_level.local_date_time
            else:
                return self.average_data.discharge.local_date_time
        return None

    def to_jsonizable(self):
        """Serializes the object into a JSON-compatible dictionary.

        Returns:
            Dictionary that can be serialized into JSON.
        """
        base_dict = {}
        if self.eight_data:
            base_dict['eight_data'] = self.eight_data.to_jsonizable()
        if self.twenty_data:
            base_dict['twenty_data'] = self.twenty_data.to_jsonizable()
        if self.average_data:
            base_dict['average_data'] = self.average_data.to_jsonizable()
        if self.additional_data:
            base_dict['additional_data'] = self.additional_data.to_jsonizable()
        return base_dict

    def to_xml(self, element):
        if self.eight_data:
            sub_element = ElementTree.SubElement(element, 'EightData')
            self.eight_data.to_xml(sub_element)
        if self.twenty_data:
            sub_element = ElementTree.SubElement(element, 'TwentyData')
            self.twenty_data.to_xml(sub_element)
        if self.average_data:
            sub_element = ElementTree.SubElement(element, 'AverageData')
            self.average_data.to_xml(sub_element)
        if self.additional_data:
            sub_element = ElementTree.SubElement(element, 'AdditionalData')
            self.additional_data.to_xml(sub_element)


class DataValueInput(object):
    """Data structure that contains the minimum information needed to
    create a new water level/discharge pair in the system.

    Attributes:
        date_time_utc: The date and time in UTC time zone.
        utc_offset: The offset of the local time, in minutes.
        water_level: The water level value.
        discharge: The discharge value.
        """
    def __init__(self, date_time_utc, utc_offset, water_level, discharge):
        self.date_time_utc = date_time_utc
        self.utc_offset = utc_offset
        self.water_level = water_level
        self.discharge = discharge

    def to_data_values(self, water_level_variable,
                       discharge_variable, censor_code,
                       quality_control_level):
        """Creates two data values corresponding to the water level and
        discharge value stored in the instance.

        This takes care of initializing the dates and the foreign keys
        according to the given parameters.

        Args:
            water_level_variable: The variable to use for the water level
                data value.
            discharge_variable: The variable to use for the discharge
                value.
            censor_code: The censor code for both values.
            quality_control_level: The quality control level for both
                values.
        Returns:
            A list with the two data values, the first element is the water
            level and the second is the discharge.
        """
        water_level = DataValue(
            data_value=self.water_level,
            local_date_time=self.date_time_utc + datetime.timedelta(
                minutes=self.utc_offset),
            utc_offset=self.utc_offset/60.0,
            date_time_utc=self.date_time_utc,
            variable_id=water_level_variable.id,
            censor_code_id=censor_code.id,
            quality_control_level_id=quality_control_level.id)
        discharge = DataValue(
            data_value=self.discharge,
            local_date_time=self.date_time_utc + datetime.timedelta(
                minutes=self.utc_offset),
            utc_offset=self.utc_offset/60.0,
            date_time_utc=self.date_time_utc,
            variable_id=discharge_variable.id,
            censor_code_id=censor_code.id,
            quality_control_level_id=quality_control_level.id)
        return [water_level, discharge]


class DischargeInput(DataValueInput):
    """Data structure that contains the minimum information needed to
    create a new set of discharge measurements and related measurements
    in the system.

    Attributes:
        maximum_depth: The measured maximum_depth.
        free_river_area: The measured river area.
    """
    def __init__(self, date_time_utc, utc_offset, water_level, discharge,
                 maximum_depth, free_river_area):
        super(DischargeInput, self).__init__(
            date_time_utc, utc_offset, water_level, discharge)
        self.maximum_depth = maximum_depth
        self.free_river_area = free_river_area

    def to_data_values(self, water_level_variable, discharge_variable,
                       maximum_depth_variable, free_river_area_variable,
                       censor_code, quality_control_level):
        """Creates four data values corresponding to the water level,
        discharge value, maximum depth and free river area stored in
        the instance.

        This takes care of initializing the variable types with the
        provided parameters.

        See DataValueInput.to_data_values for details on some of the
        parameters.

        Args:
            maximum_depth_variable: The variable to use for the maximum
                depth data value.
            free_river_area_variable: The variable to use for the
                free river area data value.
        Returns:
            A list with the four data values, in the following order:
                * water_level
                * discharge
                * maximum_depth
                * free_river_area
        """
        water_level_discharge = super(
            DischargeInput, self).to_data_values(
            water_level_variable, discharge_variable, censor_code,
            quality_control_level)
        maximum_depth = DataValue(
            data_value=self.maximum_depth,
            local_date_time=self.date_time_utc + datetime.timedelta(
                minutes=self.utc_offset),
            utc_offset=self.utc_offset/60.0,
            date_time_utc=self.date_time_utc,
            variable_id=maximum_depth_variable.id,
            censor_code_id=censor_code.id,
            quality_control_level_id=quality_control_level.id)
        free_river_area = DataValue(
            data_value=self.free_river_area,
            local_date_time=self.date_time_utc + datetime.timedelta(
                minutes=self.utc_offset),
            utc_offset=self.utc_offset/60.0,
            date_time_utc=self.date_time_utc,
            variable_id=free_river_area_variable.id,
            censor_code_id=censor_code.id,
            quality_control_level_id=quality_control_level.id)
        water_level_discharge.extend([maximum_depth, free_river_area])
        return water_level_discharge


BulletinTuple = namedtuple(
    'BulletinTuple',
    [
        'bulletin_date',
        'morning_discharge',
        'previous_day_discharge',
        'previous_two_day_discharge',
        'discharge_decade_norm',
        'maximum_discharge',
        'previous_year_decade_discharge',
        'previous_ten_year_decade_discharge',
        'current_water_level',
        'previous_day_water_level',
        'previous_two_day_water_level'
    ])


class Bulletin(object):
    """Data structure that contains a single URL to a generated bulletin.

    Attributes:
        bulletin_url: The URL to the bulletin.
    """
    def to_jsonizable(self):
        """Serializes the object in to a JSON-compatible dictionary.

        Returns:
            Dictionary that can be serialized into JSON.
        """
        return {
            'bulletin_url': self.bulletin_url
        }
