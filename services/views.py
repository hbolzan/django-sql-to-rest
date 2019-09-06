import os
import json
from django.views import View
from django.http import HttpResponse
from dstr_common_lib.controller import handle_service_request
from dstr_common_lib.consts import HTTP_STATUS_OK


class Services(View):
    def __init__(self):
        self.http_method_names = ['options', 'get', 'post', 'put', 'delete']

    def options(self, request, service, method, param=None):
        response = HttpResponse()
        response['allow'] = ','.join(self.http_method_names)
        return response

    def get(self, request, service_name, method, param=None):
        kwargs = {k: v for k, v in request.GET.items()}
        service_response = handle_service_request(service_name, method, param, **kwargs)
        return HttpResponse(
            content=json.dumps(service_response.get("body"), ensure_ascii=False),
            content_type="application/json",
            status=service_response.get("http_status", HTTP_STATUS_OK),
        )

    def post(self, request, service_name, method):
        request_data = json.loads(request.body)
        service_response = handle_service_request(service_name, method, request_data)
        return HttpResponse(
            content=json.dumps(service_response.get("body"), ensure_ascii=False),
            content_type="application/json",
            status=service_response.get("http_status", HTTP_STATUS_OK),
        )
