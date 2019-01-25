from django.urls import path
from db_query.views import DbQueryAdhoc, DbQueryPersistent
from django.views.decorators.csrf import csrf_exempt


urlpatterns = [
    path('adhoc/', DbQueryAdhoc.as_view()),
    path('persistent/<query_id>/<pk>/', csrf_exempt(DbQueryPersistent.as_view())),
    path('persistent/<query_id>/', csrf_exempt(DbQueryPersistent.as_view())),
    path('persistent/delete/<query_id>/<pk>/', csrf_exempt(DbQueryPersistent.as_view())),
]
