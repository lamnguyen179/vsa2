from app import ma
from marshmallow.fields import Nested

from app.base.models import User


class UserSchema(ma.SQLAlchemyAutoSchema):
    class Meta:
        model = User


user_schema = UserSchema()
