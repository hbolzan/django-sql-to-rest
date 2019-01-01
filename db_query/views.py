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
    # return str(table_data(get_sql(request)))
    return json.dumps({
        "status": "OK",
        "table": request.GET.get('table'),
        "data": table_data(get_sql(request)),
    }, ensure_ascii=False)

# return unicode(text).encode('iso-8859-1').decode('cp1252')

def table_data(sql):
    cursor = connections['query_db'].cursor()
    cursor.execute(sql)
    return dictfetchall(cursor)


def get_sql(request):
    return 'select * from {}'.format(request.GET.get('table'))


def dictfetchall(cursor):
    "Returns all rows from a cursor as a dict"
    desc = cursor.description
    return [
        dict(zip([col[0] for col in desc], row))
            for row in cursor.fetchall()
    ]
