from datetime import datetime
from typing import Any

from django.utils.translation import gettext_lazy as _
from ninja import Query
from ninja_extra import api_controller, route
from ninja_jwt.authentication import JWTAuth

from sapphire_backend.utils.mixins.schemas import Message
from sapphire_backend.utils.permissions import (
    regular_permissions,
)

from ..stations.models import HydrologicalStation
from ..utils.datetime_helper import SmartDatetime
from .models import DischargeModel
from .query import EstimationsViewQueryManager
from .schema import (
    DischargeModelBaseSchema,
    DischargeModelCreateInputDeltaSchema,
    DischargeModelCreateInputPointsSchema,
    DischargeModelDeleteOutputSchema,
    EstimationsFilterSchema,
    OrderQueryParamSchema,
)
from .utils import least_squares_fit


@api_controller("estimations", tags=["Discharge Models"], auth=JWTAuth(), permissions=regular_permissions)
class DischargeModelsAPIController:
    @route.get("discharge-models/{station_uuid}/list", response={200: list[DischargeModelBaseSchema], 404: Message})
    def get_discharge_models(self, station_uuid: str, year: int = Query(None, description="Filter by year")):
        try:
            hydro_station = HydrologicalStation.objects.get(uuid=station_uuid)
            queryset = DischargeModel.objects.filter(station__uuid=station_uuid)

            if year is not None:
                start_of_year_utc = SmartDatetime(datetime(year, 1, 1), hydro_station, local=True).day_beginning_utc
                end_of_year_utc = SmartDatetime(datetime(year, 12, 31, 23, 59, 59), hydro_station, local=True).utc
                queryset = queryset.filter(valid_from__range=(start_of_year_utc, end_of_year_utc))

            queryset = queryset.order_by("-valid_from")

            return 200, queryset
        except DischargeModel.DoesNotExist:
            return 404, {"detail": _("Discharge model not found."), "code": "not_found"}

    @route.post(
        "discharge-models/{station_uuid}/create-points", response={200: DischargeModelBaseSchema, 404: Message}
    )
    def create_discharge_model_from_points(
        self, request, station_uuid: str, input_data: DischargeModelCreateInputPointsSchema
    ):
        fit_params = least_squares_fit(input_data.points)

        hydro_station = HydrologicalStation.objects.get(uuid=station_uuid)
        valid_from_utc = SmartDatetime(
            datetime.fromisoformat(input_data.valid_from).replace(hour=0), hydro_station, local=True
        ).day_beginning_utc

        DischargeModel.objects.filter(station__uuid=station_uuid, valid_from=valid_from_utc).delete()

        new_model = DischargeModel(
            name=input_data.name,
            param_a=fit_params["param_a"],
            param_b=fit_params["param_b"],
            param_c=fit_params["param_c"],
            valid_from=valid_from_utc,
            station=hydro_station,
        )
        new_model.save()
        return 200, new_model

    @route.post("discharge-models/{station_uuid}/create-delta", response={200: DischargeModelBaseSchema})
    def create_discharge_model_from_delta(
        self, request, station_uuid: str, input_data: DischargeModelCreateInputDeltaSchema
    ):
        old_model = DischargeModel.objects.get(uuid=input_data.from_model_uuid)
        param_a = float(old_model.param_a) + input_data.param_delta
        param_b = float(old_model.param_b)
        param_c = float(old_model.param_c)
        hydro_station = HydrologicalStation.objects.get(uuid=station_uuid)
        valid_from_utc = SmartDatetime(input_data.valid_from, hydro_station, local=True).day_beginning_utc

        DischargeModel.objects.filter(station__uuid=station_uuid, valid_from=valid_from_utc).delete()

        new_model = DischargeModel(
            name=input_data.name,
            param_a=param_a,
            param_b=param_b,
            param_c=param_c,
            valid_from=valid_from_utc,
            station=hydro_station,
        )
        new_model.save()
        return 200, new_model

    @route.delete("discharge-models/delete/{discharge_model_uuid}", response={200: DischargeModelDeleteOutputSchema})
    def delete_discharge_model(self, request, discharge_model_uuid: str):
        model = DischargeModel.objects.filter(uuid=discharge_model_uuid).get()
        name = model.name
        model.delete()

        response = DischargeModelDeleteOutputSchema(name=name)
        return 200, response


@api_controller(
    "estimations/{organization_uuid}", tags=["Estimations"], auth=JWTAuth(), permissions=regular_permissions
)
class EstimationsAPIController:
    @route.get("discharge-daily-average", response={200: list[dict[str, Any]], 400: Message})
    def get_water_discharge_daily_average(
        self,
        organization_uuid: str,
        order: Query[OrderQueryParamSchema],
        filters: Query[EstimationsFilterSchema],
        limit: int | None = 365,
    ):
        return EstimationsViewQueryManager(
            "estimations_water_discharge_daily_average",
            organization_uuid,
            filters.dict(exclude_none=True),
            order.order_param,
            order.order_direction,
        ).execute_query(limit)
