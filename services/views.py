import os
import json
from django.views import View
from django.http import HttpResponse
from dstr_common_lib.controller import handle_service_request, build_response_body
from dstr_common_lib.consts import HTTP_STATUS_OK, HTTP_STATUS_ERROR


class Services(View):
    def __init__(self):
        self.http_method_names = ['options', 'get', 'post', 'put', 'delete']

    def options(self, request, service, method, param=None):
        response = HttpResponse()
        response['allow'] = ','.join(self.http_method_names)
        return response

    def get(self, request, service_name, method, param=None):
        kwargs = {k: v for k, v in request.GET.items()}
        return self.response_body(
            lambda: handle_service_request(service_name, method, param, **kwargs)
        )

    def post(self, request, service_name, method):
        request_data = json.loads(request.body.decode("utf-8"))
        return self.response_body(
            lambda: handle_service_request(service_name, method, request_data)
        )

    def response_body(self, service_fn):
        try:
            return self.http_response(HTTP_STATUS_OK, service_fn())
        except Exception as e:
            return self.http_response(
                HTTP_STATUS_ERROR, self.error_response(e.args[0])
            )

    def error_response(self, message):
        return {"body": build_response_body(HTTP_STATUS_ERROR, message, message)}

    def http_response(self, status, response):
        return HttpResponse(
            content=json.dumps(response.get("body"), ensure_ascii=False),
            content_type="application/json",
            status=response.get("http_status", status),
        )
