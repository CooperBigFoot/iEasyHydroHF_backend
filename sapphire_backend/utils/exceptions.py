from django.conf import settings


class BaseAPIException(Exception):
    DETAIL = "An error occurred"
    CODE = "error"

    def __init__(self, detail: str | None = None, code: str | None = None):
        self.detail = detail or self.DETAIL
        self.code = code or self.CODE
        super().__init__(self.detail)


class ImageSizeError(BaseAPIException):
    DETAIL = f"Image size exceeded allowed size of {settings.MAX_IMAGE_SIZE}MB"
    CODE = "max_file_size_exceeded"

    def __init__(self, detail: str | None = None, code: str | None = None):
        super().__init__(detail or self.DETAIL, code or self.CODE)
