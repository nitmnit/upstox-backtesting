from django.db import models

from django_extensions.db.models import TimeStampedModel

NAME_LENGTH = 60


class Credential(TimeStampedModel):
    name = models.CharField(max_length=NAME_LENGTH)
    description = models.CharField(max_length=NAME_LENGTH)
    client_id = models.CharField(max_length=NAME_LENGTH)
    password = models.CharField(max_length=NAME_LENGTH)
    api_secret = models.CharField(max_length=NAME_LENGTH)
    api_key = models.CharField(max_length=NAME_LENGTH)
    access_token = models.CharField(max_length=NAME_LENGTH)


class SecurityQuestion(TimeStampedModel):
    question = models.CharField(max_length=NAME_LENGTH * 10)
    answer = models.CharField(max_length=NAME_LENGTH)
    credentials = models.ForeignKey(Credential, on_delete=models.CASCADE)
