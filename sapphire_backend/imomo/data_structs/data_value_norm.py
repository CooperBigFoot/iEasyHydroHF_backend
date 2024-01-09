# -*- encoding: UTF-8 -*-


class DataValueNorm(object):
    """Data structure for the data_value norm data for a single site.

    Attributes:
        norm_url (str): The URL to the excel file with the norm data.
        norm_data (list of float): A list with 36 floating point values, one
            for each decade in a year. This is the data_value average or norm
            for the site.
        site_id (int):
        start_year (int):
        end_year (int):
    """
    def __init__(self, norm_url, norm_data, site_id, start_year, end_year):
        self.norm_url = norm_url
        self.norm_data = norm_data
        self.site_id = site_id
        self.start_year = start_year
        self.end_year = end_year

    def to_jsonizable(self):
        """Serializes the object in to a JSON-compatible dictionary.

        Returns:
            Dictionary that can be serialized into JSON.
        """
        return {
            'norm_url': self.norm_url,
            'norm_data': self.norm_data,
            'site_id': self.site_id,
            'start_year': self.start_year,
            'end_year': self.end_year
        }
