from django.contrib.postgres.fields import JSONField
from django.db import models

from django_extensions.db.models import TimeStampedModel
from model_utils import Choices

NAME_LENGTH = 60


class Credential(TimeStampedModel):
    name = models.CharField(max_length=NAME_LENGTH)
    description = models.CharField(max_length=NAME_LENGTH)
    client_id = models.CharField(max_length=NAME_LENGTH)
    password = models.CharField(max_length=NAME_LENGTH)
    api_secret = models.CharField(max_length=NAME_LENGTH)
    api_key = models.CharField(max_length=NAME_LENGTH)
    access_token = models.CharField(max_length=NAME_LENGTH, null=True, blank=True)
    pin = models.IntegerField(null=True, blank=True)

    def __str__(self):
        return self.name


class SecurityQuestion(TimeStampedModel):
    question = models.CharField(max_length=NAME_LENGTH * 10)
    answer = models.CharField(max_length=NAME_LENGTH)
    credentials = models.ForeignKey(Credential, on_delete=models.CASCADE)

    def __str__(self):
        return self.question


class Instrument(TimeStampedModel):
    EXCHANGES = Choices(
        ('NSE', 'NSE'),
        ('NFO', 'NFO'),
        ('CDS', 'CDS'),
        ('BSE', 'BSE'),
        ('MCX', 'MCX'),
    )

    name = models.CharField(max_length=NAME_LENGTH, null=True, blank=True)
    instrument_token = models.IntegerField()
    exchange_token = models.IntegerField()
    trading_symbol = models.CharField(max_length=NAME_LENGTH)
    last_price = models.FloatField(null=True, blank=True)
    expiry = models.DateTimeField(null=True, blank=True)
    strike = models.FloatField(null=True, blank=True)
    tick_size = models.FloatField(null=True, blank=True)
    lot_size = models.IntegerField()
    instrument_type = models.CharField(max_length=NAME_LENGTH)
    segment = models.CharField(max_length=NAME_LENGTH)
    exchange = models.CharField(max_length=NAME_LENGTH, choices=EXCHANGES)

    def __str__(self):
        return '{}-{}'.format(self.name, self.instrument_token)


class QuotesData(TimeStampedModel):
    data = JSONField()
    timestamp = models.DateTimeField()

    def __str__(self):
        return 'QuotesData: {}'.format(self.id)


class TempValues(TimeStampedModel):
    name = models.CharField(max_length=NAME_LENGTH, unique=True)
    value = models.CharField(max_length=NAME_LENGTH)

    def __str__(self):
        return 'TempValue-{}:{}'.format(self.name, self.value)

# TODO Create a model to store all orders placed
