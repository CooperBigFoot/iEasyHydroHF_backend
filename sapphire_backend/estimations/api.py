from datetime import datetime

from ninja import Query
from ninja_extra import api_controller, route
from ninja_jwt.authentication import JWTAuth

from sapphire_backend.utils.mixins.schemas import Message
from sapphire_backend.utils.permissions import (
    regular_permissions, OrganizationExists, IsOrganizationAdmin, IsSuperAdmin, IsOrganizationMember,
)
from .models import DischargeModel
from .schema import (
    DischargeModelOutputDetailSchema, DischargeModelCreateInputPointsSchema, DischargeModelCreateInputDeltaSchema,
)
from .utils import least_squares_fit


@api_controller(
    "estimations", tags=["Discharge Models"], auth=JWTAuth(),
    # permissions=regular_permissions  # TODO PERMISSIONS BASED ON STATION_ID
)
class DischargeModelsAPIController:
    @route.get("discharge-models/{station_id}/list", response={200: list[DischargeModelOutputDetailSchema], 404: Message})
    def get_discharge_models(self, station_id: str, year: int = Query(None, description="Filter by year")):
        try:
            queryset = DischargeModel.objects.filter(station_id=station_id)

            if year is not None:
                start_of_year = datetime(year, 1, 1)
                end_of_year = datetime(year, 12, 31, 23, 59, 59)
                queryset = queryset.filter(valid_from__range=(start_of_year, end_of_year))

            queryset = queryset.order_by('-valid_from')
            return 200, queryset
        except DischargeModel.DoesNotExist:
            return 404, {"detail": _("Discharge model not found."), "code": "not_found"}

    @route.post("discharge-models/{station_id}/create-points",
                response={200: DischargeModelOutputDetailSchema, 404: Message})
    def create_discharge_model_from_points(self, request, station_id: str,
                                           input_data: DischargeModelCreateInputPointsSchema):
        fit_params = least_squares_fit(input_data.points)
        new_model = DischargeModel(
            name=input_data.name,
            param_a=fit_params["param_a"],
            param_b=fit_params["param_b"],
            param_c=fit_params["param_c"],
            valid_from=datetime.fromisoformat(input_data.valid_from),
            station_id=station_id
        )
        new_model.save()
        try:
            return 200, new_model
        except DischargeModel.DoesNotExist:
            return 404, {"detail": _("Discharge model could not be created."), "code": "not_found"}


    @route.post("discharge-models/{station_id}/create-delta",
                response={200: DischargeModelOutputDetailSchema, 404: Message})
    def create_discharge_model_from_delta(self, request, station_id: str,
                                           input_data: DischargeModelCreateInputDeltaSchema):
        old_model = DischargeModel.objects.get(id=input_data.from_model_id)
        param_a = float(old_model.param_a) + input_data.param_delta
        param_b = float(old_model.param_b)
        param_c = float(old_model.param_c)

        new_model = DischargeModel(
            name=input_data.name,
            param_a=param_a,
            param_b=param_b,
            param_c=param_c,
            valid_from=datetime.fromisoformat(input_data.valid_from),
            station_id=station_id
        )
        new_model.save()
        try:
            return 200, new_model
        except DischargeModel.DoesNotExist:
            return 404, {"detail": _("Discharge model could not be created."), "code": "not_found"}
