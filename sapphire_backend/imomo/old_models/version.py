# -*- encoding: UTF-8 -*-
from sqlalchemy import Column, String

from .orm import ImomoBase


class ODMVersion(ImomoBase):
    """Table that holds the current schema version number.

    Current schema is the ODM specification v1.1 with some additions and
    modifications for the imomo hydromet use case.

    Attributes:
        version_number: The version code for the schema (50 char limit).
    """
    version_number = Column(String(50), default='1.1-imomo',
                            nullable=False, unique=True)
