from sapphire_backend.imomo.utils.strings import snake_to_camel


class IMomoError(Exception):
    """Base error for all iMomo systems.

    Class attributes:
        ERROR_CODES: A dictionary with all error codes registered by error
            classes in the system.

    Attributes:
        details: Error details.
        error_code: 5-digit error code, it is a string rather than an int.
    """

    ERROR_CODES = {"10000": "IMomoError"}

    status_code = 500

    def __init__(self, details=None, error_code=None):
        super().__init__(details)
        self._details = details or ""
        self._error_code = self.class_error_code()

        if error_code is not None:
            self.status_code = error_code

    @property
    def error_code(self):
        return self._error_code

    @property
    def details(self):
        return self._details

    @classmethod
    def _add_error_code(cls, error_code, error_name):
        """Adds an error code to the class-wide error code dictionary.

        Arguments:
            error_code: Unique 5-digit error code for the exception.
            error_name: Name of the error class.
        Raises:
            IMomoError: If the error code is already registered. This is a
            developer error and will occur only in compilation rather
            than runtime.
        """
        assert error_code not in cls.ERROR_CODES
        cls.ERROR_CODES[error_code] = error_name

    @classmethod
    def class_error_code(cls):
        return "10000"

    def raise_http_error(self, http_code=400):
        """Raise a cherrypy HTTP error with the details provided by the current
        error instance and the given http error code.

        Arguments:
            http_code: HTTP error code for the error.
        Raises:
            cherrypy.HTTPError: With the details of the current exception
            iMomonstance and the specified error code.
        """
        print("error")
        # raise cherrypy.HTTPError(status=http_code,
        #                          message=json.dumps({'details': self.details,
        #                                              'error_code':
        #                                             self.error_code}))


class IntegrityError(IMomoError):
    """Generic error for problems in the integrity of the database.

    This kind of error is most unexpected and should be handled immediately.
    """

    IMomoError._add_error_code("10001", "IntegrityError")

    @classmethod
    def class_error_code(cls):
        return "10001"


class DatabaseFlushError(IMomoError):
    """An error occurred while flushing the session."""

    IMomoError._add_error_code("10002", "DatabaseFlushError")
    error_code = "10002"


class NoModelError(IMomoError):
    status_code = 404
    """A database model was not found given a unique key."""
    IMomoError._add_error_code("10003", "NoModelError")
    error_code = "10003"


class InvalidParameterError(IMomoError):
    """An argument was invalid, e.g. a month number was 13."""

    IMomoError._add_error_code("10004", "InvalidParameterError")
    error_code = "10004"


class ManagerError(IMomoError):
    """Generic error raised by manager instances."""

    IMomoError._add_error_code("11000", "ManagerError")

    status_code = 400

    @classmethod
    def class_error_code(cls):
        return "11000"


class UserDoesNotExistError(ManagerError):
    """Error triggered when a User record can not be found
    given some identifier such as username or full name.

    No error details expected.
    """

    ManagerError._add_error_code("11001", "UserDoesNotExistError")

    @classmethod
    def class_error_code(cls):
        return "11001"


class UserRolesInsufficientError(ManagerError):
    """Error triggered when a user attempts an operation without the sufficient
    roles for it.
    """

    ManagerError._add_error_code("11002", "UserRolesInsufficientError")

    @classmethod
    def class_error_code(cls):
        return "11002"


class UserNotInOrganizationError(ManagerError):
    """Error triggered when a user attempts an action outside his own
    organization.
    """

    ManagerError._add_error_code("11004", "UserNotInOrganizationError")

    @classmethod
    def class_error_code(cls):
        return "11004"


class OrganizationNotFoundError(ManagerError):
    """Error triggered when a user tries to register with a non-existent
    organization id."""

    ManagerError._add_error_code("11006", "OrganizationNotFoundError")

    @classmethod
    def class_error_code(cls):
        return "11006"


class UsernameAlreadyExistsError(ManagerError):
    """Error triggered when a user tries to register with an existent
    username."""

    ManagerError._add_error_code("11007", "UsernameAlreadyExistsError")

    @classmethod
    def class_error_code(cls):
        return "11007"


class EmailAlreadyExistsError(ManagerError):
    """Error triggered when a user tries to register with an existent email."""

    ManagerError._add_error_code("11008", "EmailAlreadyExistsError")

    @classmethod
    def class_error_code(cls):
        return "11008"


class UndefinedRoleError(ManagerError):
    """Error triggered when a user requests an inexistent role."""

    ManagerError._add_error_code("11009", "UndefinedRoleError")

    @classmethod
    def class_error_code(cls):
        return "11009"


class TelegramDoesNotExistError(ManagerError):
    """Error triggered when a user requests an inexisting telegram."""

    ManagerError._add_error_code("11010", "TelegramDoesNotExistError")

    @classmethod
    def class_error_code(cls):
        return "11010"


class EntityDoesNotExistError(ManagerError):
    """Error triggered when a user query does not match any entity in the
    database."""

    ManagerError._add_error_code("11011", "EntityDoesNotExistError")

    @classmethod
    def class_error_code(cls):
        return "11011"


class NoWaterLevelMeasurementError(ManagerError):
    """Error triggered when a user attempts to register a water flow
    measurement or calculation without an associated water level measurement.
    """

    ManagerError._add_error_code("11012", "NoWaterLevelMeasurementError")

    @classmethod
    def class_error_code(cls):
        return "11012"


class InvalidWaterRecordParametersError(ManagerError):
    """Error triggered when a user attempts to register a water data record
    without the required fields."""

    ManagerError._add_error_code("11013", "InvalidWaterRecordParametersError")

    @classmethod
    def class_error_code(cls):
        return "11013"


class TelegramAlreadyExistsError(ManagerError):
    """Error triggered when a user attempts to register a telegram record
    with telegram text that already exists in the system."""

    ManagerError._add_error_code("11014", "TelegramAlreadyExistsError")

    @classmethod
    def class_error_code(cls):
        return "11014"


class SiteCodeAlreadyExistsError(ManagerError):
    ManagerError._add_error_code("11015", "SiteCodeAlreadyExistsError")

    @classmethod
    def class_error_code(cls):
        return "11015"


class SiteNameAlreadyExistsError(ManagerError):
    ManagerError._add_error_code("11016", "SiteNameAlreadyExistsError")

    @classmethod
    def class_error_code(cls):
        return "11016"


class SiteNotInSourceError(ManagerError):
    ManagerError._add_error_code("11017", "SiteNotInSourceError")

    status_code = 403

    @classmethod
    def class_error_code(cls):
        return "11017"


class SiteDoesNotExistError(ManagerError):
    ManagerError._add_error_code("11018", "SiteDoesNotExistError")

    status_code = 404

    @classmethod
    def class_error_code(cls):
        return "11018"


class FirstDischargeModelDeleteError(IMomoError):
    """Error indicating that the discharge model can't be deleted
    because it's the first discharge model for the site."""

    IMomoError._add_error_code("11101", "FirstDischargeModelDeleteError")

    status_code = 400

    details = "Discharge model can't be deleted because it's the first " "discharge model for the site."

    @classmethod
    def class_error_code(cls):
        return "11101"


class AuthenticationError(IMomoError):
    """Generic class for authentication errors."""

    IMomoError._add_error_code("12000", "AuthenticationError")

    @classmethod
    def class_error_code(cls):
        return "12000"


class UserAlreadyLoggedInError(AuthenticationError):
    """Error triggered when a user tries to log in while an user is already
    logged in in the current session."""

    AuthenticationError._add_error_code("12001", "UserAlreadyLoggedInError")

    @classmethod
    def class_error_code(cls):
        return "12001"


class InvalidPasswordError(AuthenticationError):
    """Error triggered when a user tries to execute a function that requires
    re-entering the password and fails to provide the correct password."""

    AuthenticationError._add_error_code("12002", "InvalidPasswordError")

    @classmethod
    def class_error_code(cls):
        return "12002"


class LexiconError(IMomoError):
    """Generic error for validation failures against the iMomo lexicon."""

    IMomoError._add_error_code("13000", "LexiconError")

    status_code = 400

    @classmethod
    def class_error_code(cls):
        return "13000"


class KN15ParserError(IMomoError):
    """Error triggered during the parsing of a KN15 telegram."""

    IMomoError._add_error_code("14000", "KN15ParserError")

    @classmethod
    def class_error_code(cls):
        return "14000"


class CodeNotImplementedError(KN15ParserError):
    """Error triggered when attempting to parse a KN15 telegram with a
    code in section 0 that is not yet supported."""

    KN15ParserError._add_error_code("14001", "CodeNotImplementedError")

    @classmethod
    def class_error_code(cls):
        return "14001"


class SectionNotImplementedError(KN15ParserError):
    """Error triggered when trying to parse a KN15 message with a section that
    is not yet supported."""

    KN15ParserError._add_error_code("14002", "SectionNotImplementedError")

    @classmethod
    def class_error_code(cls):
        return "14002"


class GroupNotImplementedError(KN15ParserError):
    """Error triggered when attempting to parse a KN15 telegram with a group
    that is not yet supported for the current section."""

    KN15ParserError._add_error_code("14003", "GroupNotImplementedError")

    @classmethod
    def class_error_code(cls):
        return "14003"


class DischargeModelsError(IMomoError):
    """Error triggered when manipulating DischargeModels objects."""

    IMomoError._add_error_code("15000", "DischargeModelsError")

    @classmethod
    def class_error_code(cls):
        return "15000"


class NoFittingDischargeModelError(DischargeModelsError):
    """Error triggered when it is not possible to fit the data to a
    power discharge model."""

    DischargeModelsError._add_error_code("15001", "NoFittingDischargeModelError")

    @classmethod
    def class_error_code(cls):
        return "15001"


class ValidationError(IMomoError):
    """Error triggered when validating a model before persisting it."""

    IMomoError._add_error_code("16000", "ValidationError")

    status_code = 400

    @classmethod
    def class_error_code(cls):
        return "16000"


class RequiredParameterError(ValidationError):
    """Error triggered when validating a model before persisting it."""

    IMomoError._add_error_code("40003", "RequiredParameterError")

    def __init__(self, parameter_name, to_camel=True, **kwargs):
        if to_camel:
            parameter_name = snake_to_camel(parameter_name)
        message = f'Parameter "{parameter_name}" is required.'
        super().__init__(message, **kwargs)

    @classmethod
    def class_error_code(cls):
        return "40003"


class NullableValidationError(ValidationError):
    """Error triggered when a non-nullable attribute is None."""

    ValidationError._add_error_code("16001", "NullableValidationError")

    @classmethod
    def class_error_code(cls):
        return "16001"


class UniqueValidationError(ValidationError):
    """Error triggered when a unique attribute already exists."""

    ValidationError._add_error_code("16002", "UniqueValidationError")

    @classmethod
    def class_error_code(cls):
        return "16002"


class SitesError(IMomoError):
    IMomoError._add_error_code("17000", "SitesError")

    @classmethod
    def class_error_code(cls):
        return "17000"


class SiteNotFoundError(SitesError):
    SitesError._add_error_code("17001", "SiteNotFoundError")

    @classmethod
    def class_error_code(cls):
        return "17001"


class DataValuesError(IMomoError):
    IMomoError._add_error_code("18000", "DataValuesError")

    @classmethod
    def class_error_code(cls):
        return "18000"


class NoDataFoundError(DataValuesError):
    DataValuesError._add_error_code("18001", "NoDataFoundError")

    @classmethod
    def class_error_code(cls):
        return "18001"


class InvalidOrganizationError(DataValuesError):
    DataValuesError._add_error_code("18002", "InvalidOrganizationError")

    @classmethod
    def class_error_code(cls):
        return "18002"


class ProgrammingError(IMomoError):
    IMomoError._add_error_code("30000", "ProgrammingError")

    @classmethod
    def class_error_code(cls):
        return "30000"


class NoSourceForOrganization(ProgrammingError):
    IMomoError._add_error_code("30001", "NoSourceForOrganization")

    @classmethod
    def class_error_code(cls):
        return "30001"


class IncorrectUserTimezone(ProgrammingError):
    IMomoError._add_error_code("30002", "IncorrectUserTimezone")

    @classmethod
    def class_error_code(cls):
        return "30002"


class UngroupedDataRecord(ProgrammingError):
    IMomoError._add_error_code("30003", "UngroupedDataRecord")

    @classmethod
    def class_error_code(cls):
        return "30003"


class MissingFieldError(IMomoError):
    IMomoError._add_error_code("19000", "MissingFieldError")

    @classmethod
    def class_error_code(cls):
        return "19000"


class InvalidFieldValueError(IMomoError):
    IMomoError._add_error_code("19001", "InvalidFieldValueError")

    @classmethod
    def class_error_code(cls):
        return "19001"


class DuplicatedDataValueError(IMomoError):
    IMomoError._add_error_code("19002", "DuplicatedDataValueError")

    @classmethod
    def class_error_code(cls):
        return "19002"


class BulletinError(IMomoError):
    IMomoError._add_error_code("10100", "BulletinError")

    @classmethod
    def class_error_code(cls):
        return "10100"


class NotAllSitesFoundError(BulletinError):
    BulletinError._add_error_code("10101", "NotAllSitesFoundError")

    @classmethod
    def class_error_code(cls):
        return "10101"


class CurrentDischargeNotAvailable(BulletinError):
    BulletinError._add_error_code("10102", "CurrentDischargeNotAvailable")

    @classmethod
    def class_error_code(cls):
        return "10102"


class PreviousDischargeNotAvailable(BulletinError):
    BulletinError._add_error_code("10103", "PreviousDischargeNotAvailable")

    @classmethod
    def class_error_code(cls):
        return "10103"


class DischargeNormNotAvailable(BulletinError):
    BulletinError._add_error_code("10104", "DischargeNormNotAvailable")

    status_code = 400

    @classmethod
    def class_error_code(cls):
        return "10104"


class DischargeMaxNotAvailable(BulletinError):
    BulletinError._add_error_code("10105", "DischargeMaxNotAvailable")

    @classmethod
    def class_error_code(cls):
        return "10105"


class NoDischargeDataError(IMomoError):
    IMomoError._add_error_code("10106", "NoDischargeDataError")

    @classmethod
    def class_error_code(cls):
        return "10106"


class RequestError(IMomoError):
    IMomoError._add_error_code("10200", "RequestError")

    @classmethod
    def class_error_code(cls):
        return "10200"


class RequiredArgumentMissingError(RequestError):
    RequestError._add_error_code("10201", "RequiredArgumentMissingError")

    @classmethod
    def class_error_code(cls):
        return "10201"


class ArgumentValidationError(RequestError):
    RequestError._add_error_code("10202", "ArgumentValidationError")

    @classmethod
    def class_error_code(cls):
        return "10202"


class TelegramsError(IMomoError):
    IMomoError._add_error_code("10120", "TelegramsError")

    @classmethod
    def class_error_code(cls):
        return "10120"


class InvalidTelegramStatusError(TelegramsError):
    TelegramsError._add_error_code("10121", "InvalidTelegramStatusError")

    @classmethod
    def class_error_code(cls):
        return "10121"


class DuplicatedTelegramError(TelegramsError):
    TelegramsError._add_error_code("10122", "DuplicatedTelegramError")

    @classmethod
    def class_error_code(cls):
        return "10122"


class InexistentTelegramIdError(TelegramsError):
    TelegramsError._add_error_code("10123", "InexistentTelegramIdError")

    @classmethod
    def class_error_code(cls):
        return "10123"


class UnknownError(IMomoError):
    IMomoError._add_error_code("40000", "UnknownError")

    @classmethod
    def class_error_code(cls):
        return "40000"


class SiteNotReadyError(ManagerError):
    ManagerError._add_error_code("11019", "SiteNotReadyError")

    @classmethod
    def class_error_code(cls):
        return "11019"


class RepeatedOperationalDataError(ManagerError):
    ManagerError._add_error_code("18003", "RepeatedOperationalDataError")
    status_code = 400

    @classmethod
    def class_error_code(cls):
        return "18003"


class PermissionDeniedError(IMomoError):
    ManagerError._add_error_code("40300", "PermissionDeniedError")

    status_code = 403

    @classmethod
    def class_error_code(cls):
        return "40300"


class InvalidSourceError(IMomoError):
    ManagerError._add_error_code("40302", "InvalidSourceError")

    status_code = 403

    @classmethod
    def class_error_code(cls):
        return "40302"


class NotFoundError(ManagerError):
    """Error triggered when a user query does not match any object in the
    database."""

    ManagerError._add_error_code("40400", "NotFoundError")

    status_code = 404

    @classmethod
    def class_error_code(cls):
        return "40400"


class ObjectDoesNotExistError(NotFoundError):
    """Error triggered when a user query does not match any object in the
    database."""

    ManagerError._add_error_code("40402", "ObjectDoesNotExistError")

    @classmethod
    def class_error_code(cls):
        return "40402"


class MultipleObjectsReturnedError(ManagerError):
    """Error triggered when querying objects for details and query returns
    multiple objects."""

    ManagerError._add_error_code("400001", "MultipleObjectsReturnedError")

    @classmethod
    def class_error_code(cls):
        return "400001"


class XLSReaderError(ValidationError):
    IMomoError._add_error_code("40001", "XslReaderError")

    @classmethod
    def class_error_code(cls):
        return "40001"


class S3ResponseError(ObjectDoesNotExistError):
    IMomoError._add_error_code("40401", "S3ResponseError")

    @classmethod
    def class_error_code(cls):
        return "40401"


class SitesChangeSource(IMomoError):
    IMomoError._add_error_code("40301", "SitesChangeSource")

    status_code = 403

    @classmethod
    def class_error_code(cls):
        return "40301"


class VariableRelationshipError(IMomoError):
    IMomoError._add_error_code("50001", "VariableRelationshipError")

    status_code = 500

    @classmethod
    def class_error_code(cls):
        return "50001"


class SiteTypeError(SitesError):
    IMomoError._add_error_code("40002", "SiteTypeError")

    status_code = 400

    @classmethod
    def class_error_code(cls):
        return "40002"


class MODISResponseError(IMomoError):
    IMomoError._add_error_code("50002", "MODISResponseError")

    status_code = 500

    @classmethod
    def class_error_code(cls):
        return "50002"


class MODISConnectionError(IMomoError):
    IMomoError._add_error_code("50003", "MODISConnectionError")

    status_code = 500

    @classmethod
    def class_error_code(cls):
        return "50003"
