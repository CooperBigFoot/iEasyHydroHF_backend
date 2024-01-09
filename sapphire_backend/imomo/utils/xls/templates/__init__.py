import StringIO
import pkgutil


def load_template(country_code):
    """
    :param country_code: str
    """
    return StringIO.StringIO(pkgutil.get_data('imomo.utils.xls.templates', country_code + '_template.xlsx'))
