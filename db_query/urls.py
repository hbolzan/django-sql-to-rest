from django.urls import path
from db_query.views import DbQuerySimple

urlpatterns = [
    path('simple/', DbQuerySimple.as_view()),
]

