# -*- encoding: UTF-8 -*-
import datetime
import random
import string
import uuid

from enum import Enum as pyEnum
import datetime
from sqlalchemy import Column, String, Integer, ForeignKey, Enum, Sequence
from sqlalchemy.orm import deferred, relationship, validates, composite


from  sapphire_backend.imomo import lexicon
from .data_sources import Source
from .orm import ImomoBase, PasswordType, UTCDateTime


class UserRoleEnum(pyEnum):
    user = 1
    admin = 2
    super_admin = 3

    def to_jsonizable(self):
        return {'roleId': self.value, 'roleName': self.name}


class User(ImomoBase):
    """Table for users.

    This table holds the information of all registered users in the system.

    Attributes:
        username: Unique username (50 char limit).
        password: Hashed password field.
        email: The associated e-mail address.
        full_name: Full name of the user.
        source_id: Foreign key to the data source which the user is a member
                   of.
        registered_on: UTC date time when the user was registered.
        user_role: User role (user/admin/super_admin)
    """
    username = Column(String(50), nullable=False, index=True,
                      unique=True)
    password = deferred(Column(PasswordType, nullable=False))
    email = Column(String(255), nullable=False, index=True, unique=True)
    full_name = Column(String(255), nullable=False)
    source_id = Column(ForeignKey(Source.id), nullable=False, index=True)
    registered_on = Column(UTCDateTime, nullable=False,
                           default=lambda: datetime.datetime.now(datetime.timezone.utc))

    source = relationship(Source, innerjoin=True, lazy='joined')
    invitation = relationship('UserInvitation', cascade="all,delete")

    role = Column(
        Enum(*[role.name for role in list(UserRoleEnum)], name='roles'),
        nullable=False, default=UserRoleEnum.user
    )

    phone = Column(String(30), nullable=True)

    @validates('username')
    def validate_username(self, key, username):
        """Validates the username column according to the lexicon."""
        return lexicon.username(username)

    @validates('password')
    def validate_password(self, key, password):
        """Validates the password column according to the lexicon."""
        return lexicon.password(password)

    @validates('email')
    def validate_email(self, key, email):
        """Validates the email column according to the lexicon."""
        return lexicon.email(email)

    @validates('full_name')
    def validate_fullname(self, key, full_name):
        """Validates the full_name column according to the lexicon."""
        return lexicon.full_name(full_name)

    @validates('registered_on')
    def validate_registered_on(self, key, registered_on):
        """Checks that the registered on date is in the present or past."""
        assert registered_on <= datetime.datetime.now(datetime.timezone.utc)

    def to_jsonizable(self, exclude=None):
        """Overrides the superclass method to ensure that the password is not
        serialized.
        """
        exclude = exclude or []
        exclude.append('password')
        return super(User, self).to_jsonizable(exclude)

    @classmethod
    def generate_password(cls, length=8):
        """
        Generates valid password
        """
        # limit generated password length
        length = max(min(lexicon.MAX_PASSWORD_LENGTH, length), lexicon.MIN_PASSWORD_LENGTH)

        password = ''.join(random.choice(string.ascii_letters + string.digits) for i in range(length - 2))

        # add digit and uppercase - password must contain at least one uppercase letter and at least one digit
        password += random.choice(string.digits)
        password += random.choice(string.uppercase)

        return password

    def __repr__(self):
        try:
            if self.source_id is not None:
                organization_name = self.source.organization.encode('utf-8')
            else:
                organization_name = ''
            return "<User: {username} ({user_role} @ {source})>".format(
                username=self.username,
                user_role=self.role,
                source=organization_name
            )
        except Exception as ex:
            return super(User, self).__repr__()


def generate_uuid():
    return str(uuid.uuid4())


class UserInvitation(ImomoBase):
    uuid = Column(
        String(255),
        nullable=False,
        unique=True,
        primary_key=True,
        default=generate_uuid,
    )

    email = Column(String(255), nullable=False)
    full_name = Column(String(255), nullable=False)

    created_on = Column(
        UTCDateTime,
        nullable=False,
        default=lambda: datetime.datetime.now(datetime.timezone.utc),
    )

    used_on = Column(
        UTCDateTime,
        nullable=True,
    )

    source_id = Column(ForeignKey(Source.id), nullable=False, index=True)
    user_id = Column(ForeignKey(User.id), nullable=True, index=True)

    source = relationship(Source, innerjoin=True, lazy='joined')

    @validates('email')
    def validate_email(self, key, email):
        """Validates the email column according to the lexicon."""
        return lexicon.email(str(email))

    def to_jsonizable(self, exclude=None):
        return_json = super(UserInvitation, self).to_jsonizable(exclude)
        if return_json.get('created_on') is not None:
            return_json['created_on'] = return_json['created_on'].isoformat()

        if return_json.get('used_on') is not None:
            return_json['used_on'] = return_json['used_on'].isoformat()

        return_json['source'] = self.source.to_jsonizable()

        return return_json
