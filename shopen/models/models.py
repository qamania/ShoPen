from tortoise.models import Model
from tortoise import fields


class Pen(Model):
    # service
    _not_null_fields = ["id", "name", "status", "delay", "is_action"]
    id = fields.IntField(primary_key=True, generated=True)
    brand = fields.TextField()
    price = fields.FloatField()
    stock = fields.IntField()
    color = fields.TextField(null=True)
    length = fields.IntField(null=True)
    is_deleted = fields.BooleanField(default=False)


class User(Model):
    id = fields.IntField(primary_key=True, generated=True)
    role = fields.TextField(default='customer')
    name = fields.CharField(unique=True, max_length=50)
    password = fields.TextField()
    credit = fields.FloatField(default=0)
    is_superuser = fields.BooleanField(default=False)


class Transaction(Model):
    id = fields.IntField(primary_key=True, generated=True)
    user: User = fields.ForeignKeyField('models.User',
                                        related_name='transactions',
                                        on_delete=fields.CASCADE)
    price = fields.FloatField()
    timestamp = fields.DatetimeField(auto_now_add=True)
    order = fields.JSONField()  # list of pen ids + number
    status = fields.TextField(default='requested')  # requested, completed, cancelled, refunded


class Session(Model):
    id = fields.IntField(primary_key=True, generated=True)
    user: User = fields.ForeignKeyField('models.User',
                                  related_name='sessions',
                                  on_delete=fields.CASCADE)
    token = fields.TextField()
    expiry = fields.DatetimeField()
