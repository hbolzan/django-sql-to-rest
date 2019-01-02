from django.contrib import admin
from db_query.models import PersistentQuery


class PersistentQueryModelAdmin(admin.ModelAdmin):
    list_display = ("name", "query_id", "description", "insert_pk", "query_pk", )
    prepopulated_fields = {"query_id": ("name",)}


admin.site.register(PersistentQuery, PersistentQueryModelAdmin)
