# -*- encoding: UTF-8 -*-
from sqlalchemy import Column, ForeignKey, Index, Text, UniqueConstraint
from sqlalchemy.orm import relationship, backref

from .observation_values import DataValue
from .orm import ImomoBase


class GroupDescription(ImomoBase):
    """Table that contains all the groups of data values.

    This table generates an unique ID for every group created and associates
    with a description.

    Attributes:
        group_description: Description of the created group.
    """
    group_description = Column(Text, nullable=False)

    data_values = relationship(
        DataValue,
        secondary='group',
        lazy="dynamic",
        backref=backref('groups', lazy="dynamic"),
    )


class Group(ImomoBase):
    """Table for grouping data values according to different criteria.

    This table represents the relations between different data values. A
    value may belong to 0 to many groups while a group can have 1 to many
    values.

    Attributes:
        group_id: Foreign key to the a group description.
        value_id: Foreign key to the data value.
        group: ORM relation to the group instance.
        value: ORM relation to the data value instance.
    """
    __table_args__ = (
        UniqueConstraint('group_id', 'value_id'),
        Index('ix_groups_value_id_group_id', 'value_id', 'group_id')
        )

    group_id = Column(ForeignKey(GroupDescription.id),
                      nullable=False)
    value_id = Column(ForeignKey(DataValue.id), nullable=False)

    group = relationship(GroupDescription, innerjoin=True, lazy='joined')
    value = relationship(DataValue, innerjoin=True, lazy='joined')
