import xlsxwriter
from imomo.utils.strings import to_unicode
from imomo.utils.xls.formatters import hydrology_cell_value_formatter


class BulkDataWriter(xlsxwriter.Workbook):
    _value_format = {"text_wrap": True, "align": "center"}

    float_number = {"num_format": "0.00", "align": "center"}
    int_number = {"num_format": "0"}
    date_format = {"num_format": "dd.mm.yyyy. hh:MM:ss", "align": "center"}
    header_format = {"align": "center", "valign": "vcenter", "bold": True, "text_wrap": True}
    _ = lambda k: k
    variables = {
        # gauge_height_daily_measurement = '0001'
        "0001": {"label": _("Water Level daily")},
        # gauge_height_average_daily_measurement = '0002'
        "0002": {"label": _("Water Level daily average")},
        # gauge_height_average_daily_estimation = '0003'
        "0003": {"label": _("Water Level daily estimation")},
        # discharge_daily_measurement = '0004'
        "0004": {"label": _("Discharge measurement"), "hydrology_format": True},
        # discharge_daily_estimation = '0005'
        "0005": {"label": _("Discharge daily"), "hydrology_format": True},
        # river_cross_section_area_measurement = '0006'
        "0006": {"label": _("Free river area")},
        # maximum_depth_measurement = '0007'
        "0007": {"label": _("Maximum depth")},
        # discharge_decade_average = '0008'
        "0008": {"label": _("Decade discharge"), "hydrology_format": True},
        # discharge_maximum_recommendation = '0009'
        "0009": {"label": _("Dangerous discharge"), "hydrology_format": True},
        # discharge_daily_average_estimation = '0010'
        "0010": {"label": _("Discharge daily average"), "hydrology_format": True},
        # ice_phenomena_observation = '0011'
        "0011": {"label": _("Ice phenomena")},
        # gauge_height_decadal_measurement = '0012'
        "0012": {"label": _("Water level measurement")},
        # water_temperature_observation = '0013'
        "0013": {"label": _("Water temperature")},
        # air_temperature_observation = '0014'
        "0014": {"label": _("Air temperature")},
        # discharge_fiveday_average = '0015'
        "0015": {"label": _("Fiveday Discharge"), "hydrology_format": True},
        # temperature_decade_average = '0016'
        "0016": {"label": _("Decade temperature")},
        # temperature_month_average = '0017'
        "0017": {"label": _("Monthly temperature")},
        # precipitation_decade_average = '0018'
        "0018": {"label": _("Decade precipitation")},
        # precipitation_month_average = '0019'
        "0019": {"label": _("Monthly precipitation")},
        # discharge_decade_average_historical = '0020'
        "0020": {"label": _("Discharge historical decade average")},
    }

    def __init__(self, filename=None, options=None):
        if options is None:
            options = {}
        super().__init__(filename, options)
        self._init_column_headers_format()
        self._init_row_header_format()
        self._init_number_format()

    def _init_number_format(self):
        """Initializes the format used to print the numbers in the file."""
        self._number_format = self.add_format()
        self._number_format.set_num_format("0.0000")
        self._number_format.set_align("center")

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

    def _add_headers(self, worksheet, row):
        worksheet.set_row(row, 35)
        for column, col_data in enumerate(self.headers):
            text = col_data["header"]
            worksheet.write(row, column, text, self._column_header_format)

    def write(self, data_values):
        for site, site_data in data_values.iteritems():
            sheet_label = site.site_code_repr
            if site.is_meteo_site:
                sheet_label += to_unicode(_(" (meteo)"))
            worksheet = self.add_worksheet(sheet_label)
            worksheet.set_column(0, 0, width=20)
            worksheet.set_row(0, height=50)

            worksheet.freeze_panes(0, 0)
            worksheet.freeze_panes(1, 0)
            worksheet.freeze_panes(2, 0)

            column = 1

            data = site_data["data"]
            variables = []
            for var in site_data["variables"]:
                var_data = self.variables[var.variable_code]
                var_data["variable"] = var
                variables.append(var_data)

            variable_data = sorted(variables, key=lambda x: x.get("sort", x.get("variable").variable_code))
            sorted_variable_ids = [var_["variable"].id for var_ in variable_data]
            sorted_formatters = [var_.get("hydrology_format") for var_ in variable_data]

            for index, var in enumerate(variable_data):
                worksheet.set_column(column + index, column + index, width=15)
                worksheet.write(
                    0, column + index, to_unicode(_(var.get("label"))), self.add_format(self.header_format)
                )

                worksheet.write(
                    1,
                    column + index,
                    to_unicode(_(var.get("variable").unit_abbv)),
                    self.add_format(self.header_format),
                )

            worksheet.write(1, 0, to_unicode(_("Date / Unit")), self.add_format(self.header_format))

            row = 2

            for local_date_time, date_date_values in sorted(data.iteritems()):
                worksheet.write(
                    row,
                    0,
                    local_date_time,
                    self.add_format(self.date_format),
                )

                for dv in date_date_values:
                    index = sorted_variable_ids.index(dv.variable_id)
                    hydrology_format = sorted_formatters[index]
                    if hydrology_format:
                        num_format, value = hydrology_cell_value_formatter(dv.data_value)
                        cell_format = {"num_format": num_format, "align": "center"}
                    else:
                        value = dv.data_value
                        cell_format = self.float_number

                    worksheet.write(
                        row,
                        index + 1,
                        value,
                        self.add_format(cell_format),
                    )

                row += 1

        self.close()
