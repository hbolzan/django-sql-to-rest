import os
import json
from nameko.exceptions import UnknownService
from nameko.standalone.rpc import ServiceRpcProxy
from django.shortcuts import render
from django.views import View
from django.http import HttpResponse


RABBIT_USER = os.environ.get("RABBIT_USER", "guest")
RABBIT_PASSWORD = os.environ.get("RABBIT_PASSWORD", "guest")
RABBIT_HOST = os.environ.get("RABBIT_HOST", "localhost")
RABBIT_PORT = os.environ.get("RABBIT_PORT", "5672")


AMQP_URI = "amqp://{username}:{password}@{host}:{port}".format(
    username=RABBIT_USER,
    password=RABBIT_PASSWORD,
    host=RABBIT_HOST,
    port=RABBIT_PORT,
)
CONFIG = {"AMQP_URI": AMQP_URI}

class Services(View):
    def __init__(self):
        self.http_method_names = ['options', 'get', 'post', 'put', 'delete']

    def options(self, request, service, method):
        response = HttpResponse()
        response['allow'] = ','.join(self.http_method_names)
        return response

    def get(self, request, service, method):
        kwargs = {k: v for k, v in request.GET.items()}
        service_response = handle_service_request(service, method, **kwargs)
        return HttpResponse(
            content=json.dumps(service_response.get("body"), ensure_ascii=False),
            content_type="application/json",
            status=service_response.get("http_status", 200),
        )


def handle_service_request(service_name, method_name, *args, **kwargs):
    try:
        rpc_response = get_rpc_service_response(service_name, method_name, **kwargs)
        status = rpc_response.get("status")
        http_status = 409 if status == "ERROR" else 200
        return get_service_response(http_status, status, rpc_response.get("messages"))

    except UnknownService:
        return get_unknown_service_response()


def get_rpc_service_response(service_name, method_name, *args, **kwargs):
    with ServiceRpcProxy(service_name, CONFIG) as service:
        method = getattr(service, method_name)
        return method(*args, **kwargs)


def get_unknown_service_response():
    return get_service_response(
        404,
        "ERROR",
        {"en": "Unknown service", "pt-br": "Serviço não encontrado",}
    )


def get_service_response(http_status, status, messages):
    return {
        "http_status": http_status,
        "body": {
            "status": status,
            "data": messages_as_dict(messages),
        }
    }


def messages_as_dict(messages):
    if type(messages) != dict:
        return {
            "en": messages,
            "pt-br": messages,
        }
    default_message = messages.get("pt-br", "Unknown error")
    return {
        "en": messages.get("en", default_message),
        "pt-br": messages.get("pt-br", default_message),
    }
