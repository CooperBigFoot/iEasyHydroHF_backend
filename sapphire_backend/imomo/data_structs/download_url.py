# -*- encoding: UTF-8 -*-


class DownloadURL(object):
    """A simple data structure with a download url.

    Attributes:
        url (str):
    """
    def __init__(self, url):
        self.url = url

    def to_jsonizable(self):
        return {'url': self.url}
