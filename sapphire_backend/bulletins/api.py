import os

from django.http import FileResponse, HttpRequest
from ninja import File, Form, Query, UploadedFile
from ninja_extra import api_controller, route
from ninja_jwt.authentication import JWTAuth

from sapphire_backend.utils.mixins.schemas import Message
from sapphire_backend.utils.permissions import (
    regular_permissions,
)

from .models import BulletinTemplate
from .schema import BulletinInputSchema, BulletinOutputSchema, BulletinTypeFilterSchema


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

        return bulletin

    @route.get("{bulletin_uuid}", response={200: None, 404: Message})
    def download_bulletin_template(self, organization_uuid: str, bulletin_uuid: str):
        bulletin = BulletinTemplate.objects.for_organization(organization_uuid).get(uuid=bulletin_uuid)

        if os.path.exists(bulletin.filename.path):
            response = FileResponse(
                open(bulletin.filename, "rb"), as_attachment=True, filename=os.path.basename(bulletin.filename.name)
            )
            return response
        else:
            return 404, {"detail": "Could not retrieve the file", "code": "file_not_found"}

    @route.delete("{bulletin_uuid}", response={200: Message})
    def delete_bulletin_template(self, organization_uuid: str, bulletin_uuid: str):
        bulletin = BulletinTemplate.objects.for_organization(organization_uuid).get(uuid=bulletin_uuid)
        bulletin.delete()

        return 200, {"detail": "Bulletin deleted successfully", "code": "success"}
