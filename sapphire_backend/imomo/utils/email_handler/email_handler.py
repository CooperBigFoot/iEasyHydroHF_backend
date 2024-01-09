# -*- encoding: UTF-8 -*-

import os

from celery import Celery
from mako.template import Template
import requests

from imomo import secrets
from imomo.utils.strings import to_str
import logging

logger = logging.getLogger('hydromet')


app = Celery(
    'hydromet',
    backend='redis://{host}:{port}'.format(
        host=secrets.REDIS_HOST,
        port=secrets.REDIS_PORT,
    ),
    broker='redis://{host}:{port}'.format(
        host=secrets.REDIS_HOST,
        port=secrets.REDIS_PORT,
    )
)


class EmailServer(object):


    base_template_vars = {
        "login_href": secrets.FRONTEND_URL,
        "home_href": secrets.FRONTEND_URL,
        "change_password_href": secrets.FRONTEND_URL + '/users/me',
        "reset_password_href": secrets.FRONTEND_URL + '/reset-password/',
        "grant_access_href": secrets.FRONTEND_URL + '/organization/new',
        "footer": '<br>iMoMo team<br>hs@hydrosolutions.ch<br>'
                  'Lindenbachstrasse 11, 8006 Zürich, Switzerland',
        'header': 'iEasyHydro',
    }

    @classmethod
    def load_template(cls, template_name='basic'):
        template_path = os.path.join(secrets.EMAIL_TEMPLATES_PATH, template_name + '.html')
        return Template(
            filename=template_path,
            disable_unicode=True,
        )

    @classmethod
    def encode_utf8(cls, template_vars):
        for key, value in template_vars.iteritems():
            template_vars[key] = to_str(value)

    @classmethod
    def send_register_email(cls, created_user, password):
        send_to = created_user['email']
        username = created_user['username']
        template_vars = {
            'intro_message': _(
                'Hi <b>{full_name}</b>, <br><br> welcome to the iMoMo '
                'Hydrometeorology application. Your username is:').format(
                full_name=to_str(created_user.get('full_name', ''))
            ),
            'password_message': _(
                'Here is also a generated password for your account:'),
            'message_final': _(
                ' We highly recommend you to change your '
                'generated password immediately after login.'),
            'button_label': _('CHANGE YOUR PASSWORD'),
            'generated_password': password,
            'username': username,
        }
        template_vars.update(cls.base_template_vars)
        cls.encode_utf8(template_vars)
        template = cls.load_template(template_name='register_basic')
        formatted_template = template.render(**template_vars)
        send_email(
            _('Welcome to iEasyHydro'),
            formatted_template,
            send_to
        )

    @classmethod
    def send_reset_password(cls, full_name, token, send_to):
        template_vars = {
            'message': _(
                'Hi <b>{full_name}</b>, You received this email because you '
                'requested a password reset for your user account at '
                'Hydromet application.').format(full_name=to_str(full_name)),
            'button_label': _('RESET PASSWORD'),
            'token': token,
        }
        template_vars.update(cls.base_template_vars)
        cls.encode_utf8(template_vars)
        template = cls.load_template(template_name='password_reset_basic')
        formatted_template = template.render(**template_vars)
        send_email(
            _('iEasyHydro password'),
            formatted_template,
            send_to
        )

    @classmethod
    def send_request_access_email(cls, send_to, template_vars):
        template_vars.update(cls.base_template_vars)
        cls.encode_utf8(template_vars)
        template = cls.load_template(template_name='request_access')
        formatted_template = template.render(**template_vars)
        send_email('iEasyHydro access request', formatted_template, send_to)

    @classmethod
    def send_super_admin_warning_email(
            cls, source_name, message, admins, super_admins
    ):
        admin_emails_html = ', '.join(
            [
                '<a href="mailto:{email}">{name}</a>'.format(
                    email=admin.email,
                    name=admin.full_name
                ) for admin in admins
            ])
        template_vars = {
            'organization_name': source_name,
            'message': message,
            'admin_emails': admin_emails_html
        }
        template_vars.update(cls.base_template_vars)
        cls.encode_utf8(template_vars)
        template = cls.load_template(template_name='expiration_warning_admin')
        formatted_template = template.render(**template_vars)
        send_email_(
            'iEasyHydro subscription expiration',
            formatted_template,
            [admin.email for admin in super_admins]
        )

    @classmethod
    def send_user_warning_email(cls, source_name, message, admins):
        template_vars = {
            'intro_message': _(
                    "Subscription to the iEasyHydro "
                    "application for <b>{org}</b> organization:"
                ).format(org=to_str(source_name)),
            'details_message': _(
                'For more details, please contact '
                '<a href="mailto:hs@hydrosolutions.ch"> iMoMo team</a>'),
            'expiration_details': message,
        }
        template_vars.update(cls.base_template_vars)
        cls.encode_utf8(template_vars)
        template = cls.load_template(template_name='expiration_warning_user')
        formatted_template = template.render(**template_vars)
        send_email_(
            _('iEasyHydro subscription expiration'),
            formatted_template,
            [admin.email for admin in admins]
        )

    @classmethod
    def send_invitation_email(cls, user_invitation, admin):
        template_vars = {
            'message_1': _(
                'Hi <b>{full_name}</b>, <br><br> You are invited to register '
                'to the iEasyHydro application as a member '
                'of <b>{organization}</b> organization.').format(
                    full_name=to_str(user_invitation.full_name),
                    organization=to_str(user_invitation.source.organization)),
            'message_2': _(
                'For more details, please contact the organization admin, '
                '<a href="mailto:{admin_email}">{admin_full_name}</a>.').format(
                    admin_email=to_str(admin.email),
                    admin_full_name=to_str(admin.full_name),
            ),
            'register_href': '{url}/invitations/?invitation_uuid={uuid}'.format(
                url=secrets.FRONTEND_URL,
                uuid=user_invitation.uuid,
            ),
            'button_label': _('REGISTER'),
        }
        template_vars.update(cls.base_template_vars)
        cls.encode_utf8(template_vars)
        template = cls.load_template(template_name='user_invitation')
        formatted_template = template.render(**template_vars)
        send_email(
            'iEasyHydro invitation',
            formatted_template,
            user_invitation.email,
        )

    @classmethod
    def send_report_email(
            cls,
            report_url,
            report_type,
            period,
            subscriptions,
    ):
        template_vars = {
            'button_label': _('DOWNLOAD'),
            'message': _(
                'New <b>{report_type}</b> report has been generated:').format(
                report_type=_(report_type)),
            'report_url': report_url,
            'period': period,
        }
        template_vars.update(cls.base_template_vars)
        cls.encode_utf8(template_vars)
        template = cls.load_template(template_name='report_generated')
        formatted_template = template.render(**template_vars)
        send_email_(
            _('iEasyHydro {} report').format(_(report_type)),
            formatted_template,
            subscriptions
        )

    @classmethod
    def send_retraining_email(cls, organization_name, admins):
        template_vars = {
            'message': _(
                'All forecasting models related to the <b>{org}</b> '
                'organization was retrained.').format(
                    org=to_str(organization_name)),
        }
        template_vars.update(cls.base_template_vars)
        cls.encode_utf8(template_vars)
        template = cls.load_template(template_name='models_retrained')
        formatted_template = template.render(**template_vars)
        send_email_(
            # TRANSLATOR_NOTE: subject for email sent when all forecast
            #  models are retrained
            _('iEasyHydro - models retrained'),
            formatted_template,
            [admin.email for admin in admins]
        )


def send_email(subject, body, send_to):
    send_email_(subject, body, send_to)


@app.task
def send_email_(subject, body, send_to):

    send_to = send_to if isinstance(send_to, list) else [send_to]

    response = requests.post(
        url=secrets.EMAIL_URL,
        json={
            'toEmails': send_to,
            'subject': subject,
            'message': body,
        }
    )
