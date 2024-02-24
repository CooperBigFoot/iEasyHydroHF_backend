from django.contrib.admin.views.decorators import staff_member_required
from django.utils.translation import gettext_lazy as _
from ninja_extra import NinjaExtraAPI

from sapphire_backend.metrics.api import HydroMetricsAPIController, MeteoMetricsAPIController
from sapphire_backend.organizations.api import BasinsAPIController, OrganizationsAPIController, RegionsAPIController
from sapphire_backend.stations.api import (
    HydroStationsAPIController,
    MeteoStationsAPIController,
    VirtualStationsAPIController,
)
from sapphire_backend.telegrams.api import TelegramsAPIController
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
api.register_controllers(VirtualStationsAPIController)
