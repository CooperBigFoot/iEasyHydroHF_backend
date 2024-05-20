import logging
import os

from django.core.management.base import BaseCommand

from sapphire_backend.organizations.models import Organization
from sapphire_backend.users.models import User

super_admins = ["andrey", "bea", "tobias", "davor.skalec"]
organization_admins = ["Elvira"]
regular_users = ["Aidai", "Aliya", "Begaim", "Janai", "Munara"]


class Command(BaseCommand):
    def add_arguments(self, parser):
        pass

    def handle(self, *args, **options):
        kgz_org = Organization.objects.get(name="КыргызГидроМет")
        superuser_name = os.environ.get("DJANGO_SUPERUSER_USERNAME", None)
        if superuser_name is None:
            raise Exception("DJANGO_SUPERUSER_USERNAME not set")
        testuser_password = os.environ.get("DJANGO_TESTUSER_PASSWORD", None)

        if testuser_password is None:
            raise Exception("DJANGO_TESTUSER_PASSWORD not set")
        if superuser_name is not None:
            superuser = User.objects.get(username=superuser_name)
            superuser.organization = kgz_org
            superuser.save()

        for username in super_admins:
            User.objects.filter(username=username, organization=kgz_org).delete()
            new_user = User(
                username=username,
                email="testing@testing.abc",
                organization=kgz_org,
                user_role=User.UserRoles.SUPER_ADMIN,
            )
            new_user.set_password(testuser_password)
            new_user.save()
            logging.info(f"Super admin {username} created")

        for username in organization_admins:
            User.objects.filter(username=username, organization=kgz_org).delete()
            new_user = User(
                username=username,
                email="testing@testing.abc",
                organization=kgz_org,
                user_role=User.UserRoles.ORGANIZATION_ADMIN,
            )
            new_user.set_password(testuser_password)
            new_user.save()
            logging.info(f"Organization admin {username} created")

        for username in regular_users:
            User.objects.filter(username=username, organization=kgz_org).delete()
            new_user = User(
                username=username,
                email="testing@testing.abc",
                organization=kgz_org,
                user_role=User.UserRoles.REGULAR_USER,
            )
            new_user.set_password(testuser_password)
            new_user.save()
            logging.info(f"Regular user {username} created")
        logging.info("Test users setup successful")
