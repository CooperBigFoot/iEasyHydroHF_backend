#!/usr/bin/python
"""This module implements a parser for Excel files with decadal
discharge data.

It expects certain formatting from the excel file and will
reject anything that is not properly formatted.
"""
import logging

import xlrd

from sapphire_backend.imomo import errors

logger = logging.getLogger("hydromet.XLSReader")


class XLSReader:
    def __init__(self, file_path):
        self.workbook = self.open_workbook(file_path)

    @staticmethod
    def open_workbook(file_path):
        try:
            return xlrd.open_workbook(file_path)
        except OSError:
            raise errors.XLSReaderError("File not found.")
        except xlrd.XLRDError:
            raise errors.XLSReaderError("Unsupported format, or corrupt file.")

    def get_sheet_by_index(self, index, raise_exception):
        try:
            return self.workbook.sheet_by_index(index)
        except (IndexError, TypeError):
            if raise_exception:
                raise errors.XLSReaderError(f"Sheet with index {index} not found.")

    def get_sheet_by_name(self, sheet_name, raise_exception):
        try:
            return self.workbook.sheet_by_name(sheet_name)
        except xlrd.XLRDError:
            if raise_exception:
                raise errors.XLSReaderError(f"Sheet with name {sheet_name} not found.")

    @staticmethod
    def parse_decade_data(sheet):
        # Check that we have all 12 months worth of data
        #  37 = 1 + 12 * 3
        if sheet.ncols != 37:
            raise errors.XLSReaderError("Invalid number of columns.")

        decadal_data = dict()

        for row in xrange(1, sheet.nrows):
            year = int(sheet.cell_value(rowx=row, colx=0))
            # Check that it looks like a sound year
            if year < 1900 or year > 2100:
                raise errors.XLSReaderError(f"Invalid year {year}")

            decadal_data[year] = []
            for column in xrange(1, sheet.ncols):
                val = sheet.cell_value(rowx=row, colx=column)
                try:
                    val = float(val)
                except ValueError:
                    val = float("nan")  # NaN for not numbers
                decadal_data[year].append(val)
        return decadal_data

    def load_decade_data(self, sheet_indices=None, sheet_names=None, raise_exception=True):
        decadal_data = {}

        if sheet_indices:
            for sheet_index in sheet_indices:
                sheet = self.get_sheet_by_index(
                    sheet_index,
                    raise_exception,
                )
                decadal_data[sheet_index] = self.parse_decade_data(sheet) if sheet else {}

        else:
            # if neither sheet_indices or sheet_names arguments are passed
            #  read all available sheets
            sheet_names = sheet_names or self.workbook.sheet_names()
            for sheet_name in sheet_names:
                sheet = self.get_sheet_by_name(
                    sheet_name,
                    raise_exception,
                )
                decadal_data[sheet_name] = self.parse_decade_data(sheet) if sheet else {}

        return decadal_data


if __name__ == "__main__":
    reader = XLSReader("/home/diegob/Dropbox/modeling/Chu/AlaArcha.xls")
    # print reader.load_decade_data()
