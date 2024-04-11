import logging

from django.contrib.admin.views.decorators import staff_member_required
from django.core.exceptions import ObjectDoesNotExist
from django.db import IntegrityError
from django.http import Http404
from django.utils.translation import gettext_lazy as _
from ninja.errors import ValidationError as NinjaValidationError
from ninja_extra import NinjaExtraAPI
from pydantic import ValidationError as PydanticValidationError

from sapphire_backend.estimations.api import DischargeModelsAPIController, EstimationsAPIController
from sapphire_backend.metrics.api import HydroMetricsAPIController, MeteoMetricsAPIController
from sapphire_backend.metrics.exceptions import DischargeNormParserException
from sapphire_backend.organizations.api import BasinsAPIController, OrganizationsAPIController, RegionsAPIController
from sapphire_backend.stations.api import (
    HydroStationsAPIController,
    MeteoStationsAPIController,
    VirtualStationsAPIController,
)
from sapphire_backend.telegrams.api import TelegramsAPIController
from sapphire_backend.telegrams.exceptions import TelegramParserException
from sapphire_backend.users.api import UsersAPIController
from sapphire_backend.users.auth.api import AuthController

api = NinjaExtraAPI(
    title="iEasyHydroHF API",
    description=_("REST API service for the iEasyHydroHF application."),
    version="1.0",
    docs_decorator=staff_member_required,
)

api.register_controllers(AuthController)
api.register_controllers(BasinsAPIController)
api.register_controllers(HydroMetricsAPIController)
api.register_controllers(MeteoMetricsAPIController)
api.register_controllers(OrganizationsAPIController)
api.register_controllers(RegionsAPIController)
api.register_controllers(MeteoStationsAPIController)
api.register_controllers(HydroStationsAPIController)
api.register_controllers(TelegramsAPIController)
api.register_controllers(UsersAPIController)
api.register_controllers(DischargeModelsAPIController)
api.register_controllers(EstimationsAPIController)
api.register_controllers(VirtualStationsAPIController)


@api.exception_handler(NinjaValidationError)
@api.exception_handler(PydanticValidationError)
def validation_error(request, exc):
    logging.error(str(exc))
    return api.create_response(
        request,
        {"detail": "Some data is invalid or missing", "code": "schema_error"},
        status=422,
    )


@api.exception_handler(IntegrityError)
def integrity_error(request, exc):
    logging.error(str(exc))
    return api.create_response(
        request,
        {"detail": "Object could not be saved", "code": "integrity_error"},
        status=400,
    )


@api.exception_handler(Http404)
@api.exception_handler(ObjectDoesNotExist)
def not_found_error(request, exc):
    logging.error(str(exc))
    return api.create_response(request, {"detail": "Object does not exist", "code": "not_found"}, status=404)


@api.exception_handler(TelegramParserException)
def telegram_parse_error(request, exc):
    logging.error(str(exc))
    return api.create_response(request, {"detail": str(exc), "code": "invalid_telegram"}, status=400)


@api.exception_handler(DischargeNormParserException)
def discharge_norm_parse_error(request, exc):
    logging.error(str(exc))
    return api.create_response(request, {"detail": str(exc), "code": "invalid_norm_file"}, status=400)
