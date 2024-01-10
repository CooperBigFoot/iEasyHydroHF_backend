import datetime

# import pytz
from sqlalchemy import DateTime, String, TypeDecorator, func, type_coerce


class PasswordType(TypeDecorator):
    """Password class for transparent encryption and verification.

    Based on the SQLAlchemy recipe:
    https://bitbucket.org/zzzeek/sqlalchemy/wiki/UsageRecipes/DatabaseCrypt
    It is stored as a String of 60 characters in the database.
    """

    impl = String(60)

    def bind_expression(self, bindvalue):
        """Encrypt the cleartext password before storing them in the database.

        This uses the default encryption as defined by the PWD_CONTEXT global.
        """
        return func.crypt(bindvalue, func.gen_salt("bf"))

    class comparator_factory(String.comparator_factory):
        def __eq__(self, other):
            """Compare the local password column to an incoming cleartext
            password.
            """
            local_pw = type_coerce(self.expr, String)
            return local_pw == func.crypt(other, local_pw)


class UTCDateTime(TypeDecorator):
    """Custom type that stores a DateTime object without time zone information
    in the database but ensuring that it is always in UTC.

    Adapted from http://stackoverflow.com/questions/2528189/.

    The time zone information has to be stripped before submitting it to
    the database because otherwise psycopg will store it in local time
    rather than the original UTC value.
    """

    impl = DateTime

    def process_bind_param(self, value, engine):
        if value is not None:
            return value.astimezone(datetime.UTC).replace(tzinfo=None)

    def process_result_value(self, value, engine):
        if value is not None:
            return datetime.datetime(
                value.year,
                value.month,
                value.day,
                value.hour,
                value.minute,
                value.second,
                value.microsecond,
                tzinfo=datetime.UTC,
            )
