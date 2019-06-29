import simplejson as json
from django.views import View
from django.http import HttpResponse
from menus.models import SystemMenu, as_dict


class SystemMenuView(View):

    def get(self, request):
        return HttpResponse(
            json.dumps({
                "status": "OK",
                "data": as_dict(SystemMenu)
            }),
            content_type="application/json"
        )
