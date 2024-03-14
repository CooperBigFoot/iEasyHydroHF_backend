from django.conf import settings
from ninja_extra.exceptions import APIException
from ninja_extra.status import HTTP_400_BAD_REQUEST


class ImageSizeException(APIException):
    status_code = HTTP_400_BAD_REQUEST
    message = f"Image size exceeded allowed size of {settings.MAX_IMAGE_SIZE}MB"
