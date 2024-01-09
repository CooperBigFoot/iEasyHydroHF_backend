# -*- encoding: UTF-8 -*-
import calendar

from enum import Enum as pyEnum
from sqlalchemy import Column, DateTime, Enum, Integer, Sequence, Text

from .orm import ImomoBase


class TelegramStatus(pyEnum):
    new = 1
    processed = 2
    discarded = 3


class Telegram(ImomoBase):
    telegram_id = Column(
        'TelegramID', Integer,
        Sequence('telegramid_telegram_seq'),
        primary_key=True)
    content = Column('Content', Text, nullable=False, unique=True, index=True)
    created_on = Column('CreatedOn', DateTime, nullable=False)
    updated_on = Column('UpdatedOn', DateTime)
    status = Column('Status',
                    Enum(*[status.name for status in list(TelegramStatus)],
                         name='telegram_statuses'),
                    default=TelegramStatus.new.name,
                    nullable=False,
                    index=True)

    def to_jsonizable(self):
        json_telegram = {
            'telegramId': self.telegram_id,
            'content': self.content,
            'createdOn': calendar.timegm(self.created_on.utctimetuple()),
            'status': self.status
        }
        if self.updated_on is not None:
            json_telegram['updatedOn'] = calendar.timegm(
                self.updated_on.utctimetuple())
        return json_telegram
