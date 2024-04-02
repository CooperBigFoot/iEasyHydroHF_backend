from datetime import datetime

from ninja import Query
from ninja_extra import api_controller, route
from ninja_jwt.authentication import JWTAuth

from sapphire_backend.utils.mixins.schemas import Message
from .models import DischargeModel
from .schema import (
    DischargeModelCreateInputDeltaSchema,
    DischargeModelCreateInputPointsSchema,
    DischargeModelOutputDetailSchema, DischargeModelDeleteOutputSchema,
)
from .utils import least_squares_fit
from ..stations.models import HydrologicalStation
from ..utils.datetime_helper import SmartDatetime
from ..utils.permissions import regular_permissions


@api_controller(
    "estimations",
    tags=["Discharge Models"],
    auth=JWTAuth(),
    permissions=regular_permissions
)
class DischargeModelsAPIController:
    @route.get(
        "discharge-models/{station_id}/list", response={200: list[DischargeModelOutputDetailSchema], 404: Message}
    )
    def get_discharge_models(self, station_id: str, year: int = Query(None, description="Filter by year")):

        try:
            hydro_station = HydrologicalStation.objects.filter(id=station_id).first()

            queryset = DischargeModel.objects.filter(station_id=station_id)

            if year is not None:
                start_of_year = datetime(year, 1, 1)
                end_of_year = datetime(year, 12, 31, 23, 59, 59)
                queryset = queryset.filter(valid_from__range=(start_of_year, end_of_year))

            queryset = queryset.order_by("-valid_from")
            return_list = []
            for obj in queryset:
                transform_valid_from = SmartDatetime(obj.valid_from, station=hydro_station, local=False).local.date()
                transform = DischargeModelOutputDetailSchema(id=obj.id, name=obj.name, param_a=obj.param_a,
                                                             param_b=obj.param_b,
                                                             param_c=obj.param_c, valid_from=transform_valid_from,
                                                             station_id=obj.station_id)
                return_list.append(transform)
            return 200, return_list
        except DischargeModel.DoesNotExist:
            return 404, {"detail": _("Discharge model not found."), "code": "not_found"}

    @route.post(
        "discharge-models/{station_id}/create-points", response={200: DischargeModelOutputDetailSchema, 404: Message}
    )
    def create_discharge_model_from_points(
        self, request, station_id: str, input_data: DischargeModelCreateInputPointsSchema
    ):
        fit_params = least_squares_fit(input_data.points)

        hydro_station = HydrologicalStation.objects.filter(id=station_id).first()
        valid_from_utc = SmartDatetime(datetime.fromisoformat(input_data.valid_from).replace(hour=0), hydro_station,
                                       local=True).day_beginning_utc

        existing_model = DischargeModel.objects.filter(station_id=station_id, valid_from=valid_from_utc).first()
        if existing_model is not None:
            existing_model.delete()

        new_model = DischargeModel(
            name=input_data.name,
            param_a=fit_params["param_a"],
            param_b=fit_params["param_b"],
            param_c=fit_params["param_c"],
            valid_from=valid_from_utc,
            station_id=station_id,
        )
        new_model.save()
        try:
            return 200, new_model
        except DischargeModel.DoesNotExist:
            return 404, {"detail": _("Discharge model could not be created."), "code": "not_found"}

    @route.post(
        "discharge-models/{station_id}/create-delta", response={200: DischargeModelOutputDetailSchema, 404: Message}
    )
    def create_discharge_model_from_delta(
        self, request, station_id: str, input_data: DischargeModelCreateInputDeltaSchema
    ):
        old_model = DischargeModel.objects.get(id=input_data.from_model_id)
        param_a = float(old_model.param_a) + input_data.param_delta
        param_b = float(old_model.param_b)
        param_c = float(old_model.param_c)
        hydro_station = HydrologicalStation.objects.filter(id=station_id).first()
        valid_from_utc = SmartDatetime(datetime.fromisoformat(input_data.valid_from).replace(hour=0), hydro_station,
                                       local=True).day_beginning_utc

        existing_model = DischargeModel.objects.filter(station_id=station_id, valid_from=valid_from_utc).first()
        if existing_model is not None:
            existing_model.delete()

        new_model = DischargeModel(
            name=input_data.name,
            param_a=param_a,
            param_b=param_b,
            param_c=param_c,
            valid_from=valid_from_utc,
            station_id=station_id,
        )
        new_model.save()
        try:
            return 200, new_model
        except DischargeModel.DoesNotExist:
            return 404, {"detail": _("Discharge model could not be created."), "code": "not_found"}

    @route.delete(
        "discharge-models/{discharge_model_id}", response={200: DischargeModelDeleteOutputSchema, 404: Message}
    )
    def delete_discharge_model(
        self, request, discharge_model_id: str):
        model = DischargeModel.objects.filter(id=discharge_model_id).first()
        name = model.name
        model.delete()

        response = DischargeModelDeleteOutputSchema(name=name)
        try:
            return 200, response
        except DischargeModel.DoesNotExist:
            return 404, {"detail": _("Discharge model could not be deleted."), "code": "not_found"}
