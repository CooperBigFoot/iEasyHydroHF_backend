from django.utils.translation import gettext_lazy as _
from ninja_extra import NinjaExtraAPI

from sapphire_backend.users.api import UserAPIController
from sapphire_backend.users.auth.api import AuthController

api = NinjaExtraAPI(
    title="iEasyHydroHF API", description=_("REST API service for the iEasyHydroHF application."), version="1.0"
)

api.register_controllers(AuthController)
api.register_controllers(UserAPIController)
