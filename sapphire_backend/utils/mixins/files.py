from typing import Any

from django.conf import settings
from ninja.files import UploadedFile

from sapphire_backend.utils.exceptions import ImageSizeException


class UploadedLimitedSizeFile(UploadedFile):
    @classmethod
    def _validate(cls: type["UploadedFile"], v: Any, _: Any) -> Any:
        v = super()._validate(v, _)
        if v.size > (settings.MAX_IMAGE_SIZE * 1024 * 1024):
            raise ImageSizeException()
        return v
