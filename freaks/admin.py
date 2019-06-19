from django.contrib import admin
from freaks import models


class CredentialAdmin(admin.ModelAdmin):
    pass


class SecurityQuestionAdmin(admin.ModelAdmin):
    pass


class TempValuesAdmin(admin.ModelAdmin):
    pass


admin.site.register(models.Credential, CredentialAdmin)
admin.site.register(models.SecurityQuestion, SecurityQuestionAdmin)
admin.site.register(models.TempValues, TempValuesAdmin)
