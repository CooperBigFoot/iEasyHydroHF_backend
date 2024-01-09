from collections import namedtuple
import string

ColumnEntry = namedtuple('ColumnEntry', ['column_template', 'value', 'format'])


def create_column_entry(column_template, value, is_template_value=False, formatting=None):
    return ColumnEntry(string.Template(column_template), string.Template(value) if is_template_value else value,
                       formatting)
