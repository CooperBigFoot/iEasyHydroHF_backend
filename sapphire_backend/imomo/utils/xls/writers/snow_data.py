# -*- encoding: UTF-8 -*-

from dateutil import parser
from datetime import timedelta, date

import xlsxwriter


class SnowDataWriter(xlsxwriter.Workbook):

    def __init__(self, filename=None, options=None):
        if options is None:
            options = {}
        super(SnowDataWriter, self).__init__(filename, options)
        self._init_column_headers_format()
        self._init_row_header_format()
        self._init_number_format()

    def _init_number_format(self):
        """Initializes the format used to print the numbers in the file."""
        self._number_format = self.add_format()
        self._number_format.set_num_format('0.0000')
        self._number_format.set_align('right')

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

    @staticmethod
    def date_range(start_date, end_date):
        for n in range(int((end_date - start_date).days)):
            yield start_date + timedelta(n)

    def write(self, site_snow_data):
        worksheet = self.add_worksheet('snow_data')
        worksheet.set_column(0, 0, 20)

        all_keys = []
        for result in site_snow_data['resources']:
            all_keys += result['snow_data'].keys()

        if all_keys:
            min_date = min(all_keys)
            max_date = max(all_keys)
            start_date = parser.parse(min_date).date()
            end_date = parser.parse(max_date).date()

        worksheet.write(
            0,
            0,
            'Min elevation',
            self._column_header_format
        )

        worksheet.write(
            1,
            0,
            'Max elevation',
            self._column_header_format
        )

        row = 2
        for index, values in enumerate(site_snow_data['resources']):
            worksheet.write(
                0,
                index + 1,
                values['min_elev'],
                self._column_header_format
            )

            worksheet.write(
                1,
                index + 1,
                values['max_elev'],
                self._column_header_format
            )

        if all_keys:
            for single_date in self.date_range(start_date, end_date):
                date_key = single_date.strftime("%Y-%m-%d")
                worksheet.write(
                    row,
                    0,
                    date_key,
                    self._column_header_format
                )
                for index, values in enumerate(site_snow_data['resources']):
                    worksheet.write(
                        row,
                        index + 1,
                        values['snow_data'].get(date_key, ''),
                        self._number_format
                    )

                row += 1

        self.close()
