from django.urls import path
from db_query.views import DbQueryAdhoc, DbQueryPersistent

urlpatterns = [
    path('adhoc/', DbQueryAdhoc.as_view()),
    path('persistent/', DbQueryPersistent.as_view()),
]
