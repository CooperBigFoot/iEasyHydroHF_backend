from django.conf import settings
from ninja_extra.exceptions import APIException
from ninja_extra.status import HTTP_400_BAD_REQUEST


class ImageSizeException(APIException):
    status_code = HTTP_400_BAD_REQUEST
    message = f"Image size exceeded allowed size of {settings.MAX_IMAGE_SIZE}MB"


class InsufficientDataVariationException(APIException):
    status_code = HTTP_400_BAD_REQUEST
    message = "Insufficient variation in water levels for reliable discharge calculation. Measurements need to be taken at different water levels."
