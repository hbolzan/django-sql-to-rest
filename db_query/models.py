from django.db import models


class PersistentQuery(models.Model):
    name = models.CharField("Query name", max_length=80)
    query_id = models.SlugField("Query ID", max_length=80, primary_key=True, blank=True, db_index=True)
    insert_pk = models.CharField("Insert PK", blank=True, null=True, max_length=255, help_text="Inform insert table pk field to allow retrieving last inserted row")
    query_pk = models.CharField("Query PK", blank=True, null=True, max_length=255, help_text="Inform query pk qualified field to allow retrieving last inserted row")
    description = models.CharField(max_length=255, blank=True, null=True)
    sql_query = models.TextField("SQL Query", blank=True, null=True)
    sql_insert = models.TextField("SQL Insert", blank=True, null=True)
    sql_update = models.TextField("SQL Update", blank=True, null=True)
    sql_delete = models.TextField("SQL Delete", blank=True, null=True)

    def __str__(self):
        return self.query_id

    class Meta:
        verbose_name = "Persistent query"
        verbose_name_plural = "Persistent queries"
