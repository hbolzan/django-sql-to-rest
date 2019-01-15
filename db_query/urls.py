from django.urls import path
from db_query.views import DbQueryAdhoc, DbQueryPersistent
from django.views.decorators.csrf import csrf_exempt


urlpatterns = [
    path('adhoc/', DbQueryAdhoc.as_view()),
    path('persistent/', csrf_exempt(DbQueryPersistent.as_view())),
    path('persistent/delete/<query>/<pk>/', csrf_exempt(DbQueryPersistent.as_view())),
]
