from django.urls import path
from db_query.views import DbQueryView

urlpatterns = [
    path('simple/', DbQueryView.as_view()),
]

