from collections import OrderedDict

import xlsxwriter
from imomo.models import FrequencyEnum
from imomo.utils.strings import to_unicode
from imomo.utils.xls.formatters import hydrology_cell_value_formatter


class ForecastTrainingReportDataWriter(xlsxwriter.Workbook):
    def __init__(self, filename=None, options=None):
        options = options or {}
        super().__init__(filename, options)
        self._init_column_headers_format()
        self._init_row_header_format()
        self._init_number_format()

    def _custom_number_format(self, num_format_str):
        number_format = self.add_format()
        number_format.set_num_format(num_format_str)
        number_format.set_align("right")
        return number_format

    def _init_number_format(self):
        """Initializes the format used to print the numbers in the file."""
        self._number_format = self._custom_number_format("0.0000")

    def _init_column_headers_format(self):
        """Initializes the format that is used for the column headers."""
        self._column_header_format = self.add_format()
        self._column_header_format.set_align("vcenter")
        self._column_header_format.set_align("center")
        self._column_header_format.set_text_wrap()
        self._column_header_format.set_bold()
        self._column_header_format.set_italic()

    def _init_row_header_format(self):
        """Initializes the format the is used for the row headers."""
        self._row_header_format = self.add_format()
        self._row_header_format.set_align("left")
        self._row_header_format.set_bold()

    def _get_headers(self, frequency):
        year = to_unicode(_("Year"))
        month = to_unicode(_("Month"))
        real = to_unicode(_("Real"))
        predicted = to_unicode(_("Predicted"))

        if frequency == FrequencyEnum.pentadal.name:
            return year, month, to_unicode(_("pentade").capitalize()), real, predicted
        elif frequency == FrequencyEnum.decade.name:
            return year, month, to_unicode(_("decade").capitalize()), real, predicted
        elif frequency == FrequencyEnum.decade.name:
            return year, month, real, predicted

    def _get_period_values(self, date, frequency):
        year = date.year
        month = date.month

        if frequency == FrequencyEnum.pentadal.name:
            day_to_pentade = {
                1: 1,
                6: 2,
                11: 3,
                16: 4,
                21: 5,
                26: 6,
            }
            pentade = day_to_pentade[date.day]
            return str(year), str(month), str(pentade)
        elif frequency == FrequencyEnum.decade.name:
            day_to_decade = {
                1: 1,
                11: 2,
                21: 3,
            }
            decade = day_to_decade[date.day]
            return str(year), str(month), str(decade)
        elif frequency == FrequencyEnum.monthly.name:
            return str(year), str(month)

    def write(self, real_data, forecasted_data, frequency):
        worksheet = self.add_worksheet("forecast_report")

        for column, header in enumerate(self._get_headers(frequency)):
            # Write the column headers
            worksheet.write(0, column, header, self._column_header_format)

        all_values = OrderedDict()
        for x, real_value in enumerate(real_data.values):
            real_index = real_data.index[x]
            all_values[real_index] = {"real": real_value}

        for x, forecasted_value in enumerate(forecasted_data.values):
            forecasted_index = real_data.index[x]
            if forecasted_index not in all_values:
                all_values[forecasted_index] = {}

            all_values[forecasted_index]["forecasted"] = forecasted_value

        all_values = OrderedDict(sorted(all_values.iteritems()))

        for x, (index, values) in enumerate(all_values.iteritems()):
            real_value = values.get("real")
            forecasted_value = values.get("forecasted")

            row = x + 1
            column = 0
            for column, period_value in enumerate(self._get_period_values(index, frequency)):
                worksheet.write(row, column, period_value, self._column_header_format)

            column += 1
            value, cell_format = self._get_value_and_format(real_value)
            worksheet.write(row, column, value, cell_format)

            column += 1
            value, cell_format = self._get_value_and_format(forecasted_value)
            worksheet.write(row, column, value, cell_format)

        self.close()

    def _get_value_and_format(self, value):
        num_format_str, value = hydrology_cell_value_formatter(value)
        cell_format = self._custom_number_format(num_format_str)
        return value, cell_format
