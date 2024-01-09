# Data structures for the operational journal.


class DataPair:
    """
    Attributes:
        water_level
        discharge
    """

    def __init__(self, water_level, discharge):
        self.water_level = water_level
        self.discharge = discharge

    @property
    def water_level(self):
        return self._water_level

    @water_level.setter
    def water_level(self, value):
        self._water_level = value

    @property
    def discharge(self):
        return self._discharge

    @discharge.setter
    def discharge(self, value):
        assert value > 0, "Negative discharge values are invalid."
        self._discharge = value

    def to_jsonizable(self):
        return {"water_level": self.water_level, "discharge": self.discharge}


class DecadeAverageTuple:
    """
    Attributes:
        decade_in_month
        average_data
    """

    def __init__(self, decade_in_month, average_data):
        self.decade_in_month = decade_in_month
        self.average_data = average_data

    @property
    def decade_in_month(self):
        return self._decade_in_month

    @decade_in_month.setter
    def decade_in_month(self, value):
        self._decade_in_month = value

    @property
    def average_data(self):
        return self._average_data

    @average_data.setter
    def average_data(self, value):
        assert isinstance(value, DataPair)
        self._average_data = value

    def to_jsonizable(self):
        return {"decade_in_month": self.decade_in_month, "average_data": self.average_data.to_jsonizable()}
