from rest_framework import viewsets

from . import models
from . import serializers


class CredentialViewSet(viewsets.ModelViewSet):
    queryset = models.Credential.objects.all()
    serializer_class = serializers.CredentialSerializer


class SecurityQuestionViewSet(viewsets.ModelViewSet):
    queryset = models.SecurityQuestion.objects.all()
    serializer_class = serializers.SecurityQuestionSerializer
