from rest_framework import routers
from . import api

router = routers.DefaultRouter()
router.register(r'credential', api.CredentialViewSet)
router.register(r'security-question', api.SecurityQuestionViewSet)
