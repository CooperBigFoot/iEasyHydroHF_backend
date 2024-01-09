# -*- encoding: UTF-8 -*-


class ForecastData(object):
    """
    Attributes:
        year (int)
        decade (int)
        site_id (int)
        predicted_value (float)
        previous_values (list of imomo.models.DataValue)
    """

    def __init__(self, year, decade, site_id, predicted_value,
                 previous_values):
        self.year = year
        self.decade = decade
        self.site_id = site_id
        self.predicted_value = predicted_value
        self.previous_values = previous_values

    def to_jsonizable(self):
        return {'year': self.year,
                'decade': self.decade,
                'site_id': self.site_id,
                'predicted_value': self.predicted_value,
                'previous_values': [value.to_jsonizable()
                                    for value in self.previous_values]
                }
