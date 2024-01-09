
from enum import Enum as pyEnum

from .orm import ImomoBase
from sqlalchemy import (
    Column,
    Enum,
    Integer,
    Sequence,
    Text,
    String,
    UniqueConstraint,
)


class ContentTypeEnum(pyEnum):
    help = 1
    about = 2
    announcements = 3


class Content(ImomoBase):

    id = Column(
        Integer,
        Sequence('content_id_seq'),
        primary_key=True,
    )

    type = Column(
        Enum(*[type_.name for type_ in list(ContentTypeEnum)], name='content_types'),
        nullable=False,
    )
    language = Column(String(50), nullable=False, default='ru')

    text = Column(Text, nullable=False, default='')

    __table_args__ = (
        UniqueConstraint('type', 'language', name='_type_language_uc'),
    )

    def to_jsonizable(self, exclude=None):
        exclude = exclude or []
        exclude.append('id')
        return super(Content, self).to_jsonizable(exclude)
