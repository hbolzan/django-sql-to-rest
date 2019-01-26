from django.contrib import admin
from django.contrib.admin import TabularInline, StackedInline
from db_query.models import PersistentQuery, PersistentNestedQuery


class PersistentNesteQueryInLine(TabularInline):
    model = PersistentNestedQuery
    fk_name = "parent"
    extra = 1


class PersistentQueryModelAdmin(admin.ModelAdmin):
    list_display = ("name", "query_id", "description", "insert_pk", "query_pk", )
    prepopulated_fields = {"query_id": ("name",)}
    inlines = [PersistentNesteQueryInLine,]


admin.site.register(PersistentQuery, PersistentQueryModelAdmin)
