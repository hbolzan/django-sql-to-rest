import simplejson as json
from django.utils.encoding import force_text
from django.shortcuts import render
from django.http import HttpResponse
from django.views import View
from django.db import connections

# Create your views here.
class DbQuerySimple(View):
    def get(self, request):
        return HttpResponse(table_data_as_json(request), content_type="application/json")


def table_data_as_json(request):
    return json.dumps({
        "status": "OK",
        "table": request.GET.get('table'),
        "data": table_data(get_sql(request)),
    }, ensure_ascii=False)


def table_data(sql):
    cursor = connections['query_db'].cursor()
    cursor.execute(sql)
    return dictfetchall(cursor)


def get_sql(request):
    return 'select {} from {}'.format(columns_list(request), request.GET.get('table'))


def columns_list(request):
    columns = request.GET.get('columns')
    if columns is None:
        return '*'
    return ', '.join(columns.split('~'))


def dictfetchall(cursor):
    "Returns all rows from a cursor as a dict"
    desc = cursor.description
    return [
        dict(zip([col[0] for col in desc], row))
            for row in cursor.fetchall()
    ]