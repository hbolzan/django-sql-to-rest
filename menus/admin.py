from django.contrib import admin
from django_mptt_admin.admin import DjangoMpttAdmin
from menus.models import SystemMenu


class SystemMenuAdmin(DjangoMpttAdmin):
    pass

admin.site.register(SystemMenu, SystemMenuAdmin)
