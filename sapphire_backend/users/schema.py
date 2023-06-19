from django.contrib.auth import get_user_model
from ninja import ModelSchema

User = get_user_model()


class UserOutputSchema(ModelSchema):
    class Config:
        model = User
        model_fields = ["id", "username", "email", "first_name", "last_name", "contact_phone", "user_role"]
