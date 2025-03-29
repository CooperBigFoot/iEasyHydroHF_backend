from django.conf import settings
from ninja_extra.exceptions import APIException
from ninja_extra.status import HTTP_400_BAD_REQUEST


class ImageSizeException(APIException):
    status_code = HTTP_400_BAD_REQUEST
    message = f"Image size exceeded allowed size of {settings.MAX_IMAGE_SIZE}MB"


class InsufficientWaterLevelVariationException(APIException):
    status_code = HTTP_400_BAD_REQUEST
    message = "Insufficient variation in water levels for reliable discharge calculation. Measurements need to be taken at different water levels."
    code = "insufficient_water_level_variation"


class InsufficientDischargeVariationException(APIException):
    status_code = HTTP_400_BAD_REQUEST
    message = "Insufficient variation in discharge values for reliable calculation. Measurements need to have different discharge values."
    code = "insufficient_discharge_variation"
