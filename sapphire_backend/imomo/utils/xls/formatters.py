
import math
from decimal import Decimal


def hydrology_formatter(value):
    if value is None or value == '' or math.isnan(value):
        return ''

    return float('{value:.3g}'.format(value=value))


def hydrology_cell_value_formatter(value):
    if value is None or value == '' or math.isnan(value):
        return '', ''

    formatted_value_str = '{value:.3g}'.format(value=value)
    decimal_tuple = Decimal(formatted_value_str).as_tuple()
    smallest_valuable_exponent = decimal_tuple.exponent - 3 + len(decimal_tuple.digits)
    if smallest_valuable_exponent < 0:
        cell_format = '0.' + abs(smallest_valuable_exponent) * '0'

    else:
        cell_format = '0'

    return cell_format, float(formatted_value_str)



def signed_hydrology_formatter(value):
    if value is None or value == '' or math.isnan(value):
        return ''

    if value != 0:
        return '{value:+}'.format(value=int(value))
    else:
        return '{value}'.format(value=int(value))
