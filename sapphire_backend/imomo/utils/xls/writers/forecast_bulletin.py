# -*- encoding: UTF-8 -*-

import xlsxwriter
from imomo.utils.xls.formatters import hydrology_cell_value_formatter


class ForecastBulletinWriter(xlsxwriter.Workbook):

    _value_format = {
        'text_wrap': True,
        'align': 'center'
    }

    float_number = {'num_format': '0.00'}
    int_number = {'num_format': '0'}
    date_format = {'num_format': 'dd.mm.yyyy.'}

    headers = (
        {'header': u'Site Name', 'value_key': 'site_name', 'format': {}, 'width': 30},
        {'header': u'Site Code', 'value_key': 'site_code', 'format': {}},
        {'header': u'Model Name', 'value_key': 'model_name', 'format': {}, 'width': 30},
        {'header': u'Issue Date', 'value_key': 'issue_date', 'format': date_format, 'date': True, 'width': 15},
        {'header': u'Period start', 'value_key': 'period_start', 'format': date_format, 'date': True, 'width': 15},
        {'header': u'Period end', 'value_key': 'period_end', 'format': date_format, 'date': True, 'width': 15},
        {'header': u'Forecasted Value', 'value_key': 'forecast_value', 'format': {}, 'hydrology_format': True},
        {'header': u'Previous Value', 'value_key': 'previous_value', 'format': {}, 'hydrology_format': True},
        {'header': u'Number of training data', 'value_key': 'n_of_data', 'format': int_number},
        {'header': u'P%', 'value_key': 'percentage', 'format': float_number, 'width': 6},
        {'header': u'S/s', 'value_key': 'rel_error', 'format': float_number, 'width': 6},
        # {'header': u'±d', 'value_key': 'std_dev', 'format': float_number, 'width': 6},
        {'header': u'Max', 'value_key': 'max', 'format': {}, 'width': 6, 'hydrology_format': True},
        {'header': u'Norm', 'value_key': 'norm', 'format': {}, 'width': 6, 'hydrology_format': True},
        {'header': u'Min', 'value_key': 'min', 'format': {}, 'width': 6, 'hydrology_format': True},
    )

    def __init__(self, filename=None, options=None):
        if options is None:
            options = {}
        super(ForecastBulletinWriter, self).__init__(filename, options)
        self._init_column_headers_format()
        self._init_row_header_format()
        self._init_number_format()

    def _init_number_format(self):
        """Initializes the format used to print the numbers in the file."""
        self._number_format = self.add_format()
        self._number_format.set_num_format('0.0000')
        self._number_format.set_align('center')

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

    def _add_headers(self, worksheet, row):
        worksheet.set_row(row, 35)
        for column, col_data in enumerate(self.headers):
            text = col_data['header']
            worksheet.write(row, column, text, self._column_header_format)

    def write(self, forecast_data):
        worksheet = self.add_worksheet('forecast_bulletin')
        row = 0

        for index, col_info in enumerate(self.headers):
            worksheet.set_column(
                index,
                index,
                width=col_info.get('width', 10),
            )

        def key_fn(kv):
            if kv.frequency == 'pentadal':
                sort_prefix = '0'
            elif kv.frequency == 'decade':
                sort_prefix = '1'
            elif kv.frequency == 'monthly':
                sort_prefix = '2'
            else:
                sort_prefix = '3'

            # sort by frequency and by name
            return sort_prefix + kv.name

        sorted_keys = sorted(forecast_data.keys(), key=key_fn)

        for forecast_type in sorted_keys:
            forecast_type_data = forecast_data[forecast_type]
            forecast_type_header = False

            for site, site_results in forecast_type_data.iteritems():
                forecast_type_header_set = False
                if site_results and not forecast_type_header:
                    forecast_type_header = u'{name} ({frequency})'.format(
                        name=forecast_type.name,
                        frequency=forecast_type.frequency,
                    )

                    worksheet.merge_range(
                        row, 0,
                        row, len(self.headers) - 1,
                        forecast_type_header,
                        self._column_header_format
                    )
                    worksheet.set_row(row, 25)
                    row += 1

                    self._add_headers(worksheet, row)
                    row += 1

                    forecast_type_header_set = True
                    forecast_type_header = True

                for result in site_results:
                    model_name = result.forecast_training.forecast_model.name \
                        if result.forecast_training else '--'

                    values = {
                        'site_name': site.site_name,
                        'site_code': site.site_code,
                        'model_name': model_name,
                        'issue_date': result.issue_date,
                        'period_start': result.period_start,
                        'period_end': result.period_end,
                        'forecast_value': result.forecasted_value,
                        'previous_value': result.previous_value,
                        'n_of_data': result.training_data_count,
                        'percentage': result.percentage,
                        'rel_error': result.relative_error,
                        # 'std_dev': result.standard_deviation,
                        'max': result.maximum,
                        'norm': result.norm,
                        'min': result.minimum,
                    }

                    assert len(values) == len(self.headers)

                    column = 0
                    for index, cell_info in enumerate(self.headers):
                        value = values[cell_info['value_key']]
                        if cell_info.get('hydrology_format'):
                            num_format, value = hydrology_cell_value_formatter(value)
                            cell_info['format']['num_format'] = num_format

                        cell_info['format'].update(self._value_format)
                        if value is None:
                            column += 1
                            continue

                        try:
                            if cell_info.get('date'):
                                import pytz
                                if value.tzinfo is not None:
                                    value = value.replace(tzinfo=None)
                                worksheet.write_datetime(
                                    row,
                                    column,
                                    value,
                                    self.add_format(cell_info['format']),
                                )
                            else:
                                worksheet.write(
                                    row,
                                    column,
                                    value,
                                    self.add_format(cell_info['format']),
                                )
                        except TypeError:
                            pass
                        column += 1

                    row += 1

                if forecast_type_header_set:
                    row += 3

        self.close()

