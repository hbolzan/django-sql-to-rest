from django.urls import path
from services.views import Services
from django.views.decorators.csrf import csrf_exempt


urlpatterns = [
    path('<service_name>/<method>/', csrf_exempt(Services.as_view())),
    path('get/<service>/<method>/<param>/', csrf_exempt(Services.as_view())),
    path('get/<service>/<method>/', csrf_exempt(Services.as_view())),
]
