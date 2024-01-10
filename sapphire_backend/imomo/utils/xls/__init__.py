from insert_row import insert_rows
from openpyxl.workbook import Worksheet

# Monkey patches the insert_rows function to openpyxl.workbook.Worksheet
Worksheet.insert_rows = insert_rows
