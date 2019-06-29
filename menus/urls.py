from django.urls import path
from menus.views import SystemMenuView
from django.views.decorators.csrf import csrf_exempt


urlpatterns = [
    path('system/', csrf_exempt(SystemMenuView.as_view())),
]
