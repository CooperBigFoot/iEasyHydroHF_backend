import factory
from django.contrib.auth import get_user_model
from django.db.models import signals
from faker import Faker

User = get_user_model()

fake = Faker()


@factory.django.mute_signals(signals.post_save, signals.post_delete)
class UserFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = User
        django_get_or_create = ("username",)

    first_name = fake.first_name()
    last_name = fake.last_name()
