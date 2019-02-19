from rest_framework import serializers
from . import models


class CredentialSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Credential
        fields = '__all__'


class SecurityQuestionSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.SecurityQuestion
        fields = '__all__'
