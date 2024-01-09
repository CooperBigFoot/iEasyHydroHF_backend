# -*- encoding: UTF-8 -*-
import math

import xlsxwriter

from imomo.utils.strings import to_unicode
from imomo.utils.timeseries import get_year_decade_from_data
from imomo.utils.xls.formatters import hydrology_cell_value_formatter


class HistoricDataWriter(xlsxwriter.Workbook):

    def __init__(self, filename=None, options={}):
        """Initializes the formats and such, passes the filename and options
        to the super constructor.
        """
        super(HistoricDataWriter, self).__init__(filename, options)
        self._init_column_headers_format()
        self._init_row_header_format()
        self._init_number_format()

    def _custom_number_format(self, num_format_str):
        number_format = self.add_format()
        number_format.set_num_format(num_format_str)
        number_format.set_align('right')
        return number_format

    def _init_number_format(self):
        """Initializes the format used to print the numbers in the file."""
        self._number_format = self._custom_number_format('0.0000')

    def _init_column_headers_format(self):
        """Initializes the format that is used for the column headers."""
        self._column_header_format = self.add_format()
        self._column_header_format.set_align('vcenter')
        self._column_header_format.set_align('center')
        self._column_header_format.set_text_wrap()
        self._column_header_format.set_bold()
        self._column_header_format.set_italic()

    def _init_row_header_format(self):
        """Initializes the format the is used for the row headers."""
        self._row_header_format = self.add_format()
        self._row_header_format.set_align('left')
        self._row_header_format.set_bold()

    def write(self, site_historic_data):
        for data_type, historic_data in site_historic_data.iteritems():
            sheet_name = data_type

            if data_type == 'discharge':
                hydrology_format = True
            else:
                hydrology_format = False

            worksheet = self.add_worksheet(sheet_name)

            # Write the column headers
            worksheet.write(
                0, 0, to_unicode(_('Year')), self._column_header_format
            )

            for month in xrange(12):
                for month_decade in range(3):
                    year_decade = month * 3 + month_decade + 1
                    cell_column = year_decade
                    worksheet.write(
                        0,
                        cell_column,
                        to_unicode(_('{decade_in_year} dec.')).format(decade_in_year=year_decade),
                        self._column_header_format
                    )

            # Write the rows
            all_years_with_data = historic_data.keys()
            if all_years_with_data:
                min_year = min(all_years_with_data)
                max_year = max(all_years_with_data)
                for index, year in enumerate(range(min_year, max_year + 1)):
                    year_data = historic_data.get(year, [])
                    self._write_row(
                        worksheet, index + 1, year_data, str(year), hydrology_format)

        self.close()

    def _write_row(
            self,
            worksheet,
            row_index,
            row_data,
            row_header,
            hydrology_format=False
    ):
        worksheet.write(
            row_index, 0, row_header, self._row_header_format
        )

        for data_value in row_data:
            if data_value is None or math.isnan(data_value.data_value):
                continue
            column_index = get_year_decade_from_data(data_value.local_date_time)
            value = data_value.data_value
            if hydrology_format:
                num_format_str, value = hydrology_cell_value_formatter(value)
                cell_format = self._custom_number_format(num_format_str)
            else:
                cell_format, value = self._number_format, value

            worksheet.write(row_index, column_index, value, cell_format)
