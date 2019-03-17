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
        response = get_service_response(http_status, fix_service_response(rpc_response))
        if not is_service_response_valid(response):
            return get_bad_service_response(response)
        return response

    except UnknownService:
        return get_not_implemented_service_response()


def get_rpc_service_response(service_name, method_name, *args, **kwargs):
    with ServiceRpcProxy(service_name, CONFIG) as service:
        method = getattr(service, method_name)
        return method(*args, **kwargs)


def get_not_implemented_service_response():
    return get_service_response(
        501,
        build_response_body("ERROR",  "Not implemented service",  "Serviço não implementado")
    )


def get_bad_service_response(response):
    return get_service_response(
        500,
        build_response_body(
            "ERROR",
            "Service response not compliant with API standards",
            "Resposta do serviço solicitado fora do padrão da API",
            response,
        )
    )


def get_service_response(http_status, body):
    return {
        "http_status": http_status,
        "body": body,
    }


def is_service_response_valid(response):
    if type(response) != dict:
        return False
    valid_status = "status" in response and response["status"] in ["OK", "ERROR"]
    valid_data = "data" in response and \
        "messages" in response["data"] and \
        "en" in response["data"]["messages"] and "pt-br" in response["data"]["messages"]
    return valid_status and valid_data


def fix_service_response(response):
    if type(response) == str:
        return build_response_body("OK", response, response)
    return response


def build_response_body(status, message_en, message_ptbr, additional_info=None):
    return dict(
        {
            "status": status,
            "data": {"messages": {"en": message_en, "pt-br": message_ptbr}}
        },
        **({} if additional_info is None else {"additional_information": additional_info})
    )
