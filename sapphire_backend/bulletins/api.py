import os
from time import time

from django.conf import settings
from django.db.models import Prefetch
from django.http import FileResponse, HttpRequest
from ninja import File, Form, Query, UploadedFile
from ninja_extra import api_controller, route
from ninja_jwt.authentication import JWTAuth

from sapphire_backend.stations.models import HydrologicalStation
from sapphire_backend.utils.mixins.schemas import Message
from sapphire_backend.utils.permissions import (
    regular_permissions,
)

from .choices import BulletinTagType
from .ieasyreports.tags import daily_tags
from .models import BulletinTemplate, BulletinTemplateTag
from .schema import (
    BulletinGenerateSchema,
    BulletinInputSchema,
    BulletinOutputSchema,
    BulletinTemplateTagOutputSchema,
    BulletinTypeFilterSchema,
)


@api_controller("bulletins/{organization_uuid}", tags=["Bulletins"], auth=JWTAuth(), permissions=regular_permissions)
class BulletinsAPIController:
    @route.get("", response={200: list[BulletinOutputSchema]})
    def get_organization_bulletins(self, organization_uuid: str, filters: Query[BulletinTypeFilterSchema]):
        filters_dict = filters.dict(exclude_none=True)
        return BulletinTemplate.objects.for_organization(organization_uuid).filter(**filters_dict)

    @route.post("upload-new", response={201: BulletinOutputSchema})
    def upload_new_bulletin_template(
        self, request: HttpRequest, organization_uuid: str, data: Form[BulletinInputSchema], file: File[UploadedFile]
    ):
        bulletin = BulletinTemplate(filename=file, organization_id=organization_uuid, user=request.user, **data.dict())
        bulletin.save()

        default_tags = BulletinTemplateTag.objects.default()
        bulletin.tags.add(*default_tags)

        return bulletin

    @route.post("generate-daily-bulletin", response={200: str})
    def generate_daily_bulletin(
        self, request: HttpRequest, organization_uuid: str, bulletin_input_data: BulletinGenerateSchema
    ):
        templates = BulletinTemplate.objects.filter(uuid__in=bulletin_input_data.bulletins)
        stations = HydrologicalStation.objects.filter(uuid__in=bulletin_input_data.stations).select_related(
            "site", "site__basin", "site__region"
        )
        station_ids = stations.values_list("id", flat=True)

        context = {"station_ids": station_ids, "target_date": bulletin_input_data.date}

        for template in templates:
            template_generator = settings.IEASYREPORTS_CONF.template_generator_class(
                tags=daily_tags,
                # already a full path so the templates directory path will basically be ignored
                template=template.filename.path,
                templates_directory_path=settings.IEASYREPORTS_CONF.templates_directory_path,
                reports_directory_path=settings.IEASYREPORTS_CONF.report_output_path,
                tag_settings=settings.IEASYREPORTS_TAG_CONF,
                requires_header=True,
            )
            template_generator.validate()
            template_generator.generate_report(
                list_objects=stations, output_filename=f"daily_bulletin_{int(time())}.xlsx", context=context
            )

        return 200, "received"

    @route.get("{bulletin_uuid}", response={200: None, 404: Message})
    def download_bulletin_template(self, organization_uuid: str, bulletin_uuid: str):
        bulletin = BulletinTemplate.objects.for_organization(organization_uuid).get(uuid=bulletin_uuid)

        if os.path.exists(bulletin.filename.path):
            response = FileResponse(
                open(bulletin.filename.path, "rb"),
                as_attachment=True,
                filename=os.path.basename(bulletin.filename.name),
            )
            return response
        else:
            return 404, {"detail": "Could not retrieve the file", "code": "file_not_found"}

    @route.delete("{bulletin_uuid}", response={200: Message})
    def delete_bulletin_template(self, organization_uuid: str, bulletin_uuid: str):
        bulletin = BulletinTemplate.objects.for_organization(organization_uuid).get(uuid=bulletin_uuid)
        bulletin.delete()

        return 200, {"detail": "Bulletin deleted successfully", "code": "success"}

    @route.get("{bulletin_uuid}/tags", response={200: BulletinTemplateTagOutputSchema})
    def get_bulletin_tags(self, organization_uuid: str, bulletin_uuid: str):
        bulletin = BulletinTemplate.objects.prefetch_related(
            Prefetch("tags", queryset=BulletinTemplateTag.objects.all())
        ).get(organization_id=organization_uuid, uuid=bulletin_uuid)

        tags = bulletin.tags.all()
        response_data = {"general": [], "header": [], "data": []}

        for tag in tags:
            if tag.type == BulletinTagType.DATA:
                response_data["data"].append(tag)
            elif tag.type == BulletinTagType.HEADER:
                response_data["header"].append(tag)
            else:
                response_data["general"].append(tag)

        return response_data
