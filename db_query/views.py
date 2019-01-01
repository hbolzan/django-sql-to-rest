import json
from django.shortcuts import render
from django.http import HttpResponse
from django.views import View
from django.db import connections

# Create your views here.
class DbQueryView(View):
    def get(self, request):
        return HttpResponse(table_data_as_json(request), content_type="application/json")


def table_data_as_json(request):
    return json.dumps({
        "status": "OK",
        "table": request.GET.get('table'),
        "data": table_data(get_sql(request)),
    })


def table_data(sql):
    cursor = connections['query_db'].cursor()
    cursor.execute(sql)
    return cursor.fetchall()


def get_sql(request):
    return 'select * from {}'.format(request.GET.get('table'))
