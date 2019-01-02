from django.urls import path
from db_query.views import DbQuerySimple

urlpatterns = [
    path('adhoc/', DbQuerySimple.as_view()),
]
