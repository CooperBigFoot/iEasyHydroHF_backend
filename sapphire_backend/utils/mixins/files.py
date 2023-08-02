from typing import Any

from django.conf import settings
from ninja.files import UploadedFile

from sapphire_backend.utils.exceptions import ImageSizeError


class UploadedLimitedSizeFile(UploadedFile):
    @classmethod
    def _validate(cls: type["UploadedFile"], v: Any) -> Any:
        v = super()._validate(v)
        if v.size > (settings.MAX_IMAGE_SIZE * 1024 * 1024):
            raise ImageSizeError()
        return v
