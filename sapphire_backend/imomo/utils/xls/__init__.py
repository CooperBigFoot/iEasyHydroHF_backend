from openpyxl.workbook import Worksheet

from insert_row import insert_rows

# Monkey patches the insert_rows function to openpyxl.workbook.Worksheet
Worksheet.insert_rows = insert_rows
