import simplejson as json
from django.utils.encoding import force_text
from django.shortcuts import render, get_object_or_404
from django.http import HttpResponse
from django.views import View
from django.db import connections
from db_query.models import PersistentQuery

# Create your views here.
class DbQueryAdhoc(View):
    def get(self, request):
        return HttpResponse(table_data_as_json(request), content_type="application/json")


class DbQueryPersistent(View):
    def get(self, request):
        query = get_object_or_404(PersistentQuery, query_id=request.GET.get('query'))
        return HttpResponse(
            json.dumps({
                "status": "OK",
                "query": request.GET.get('query'),
                "data": table_data(replace_query_params(query.sql_query, request)),
            }, ensure_ascii=False),
            content_type="application/json"
        )


def replace_query_params(sql, request):
    """
    Query parameters must use string format syntax
    Example: select * from some_table where id = {id} and age > {min_age}
    """
    return sql.format(**request.GET)


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
    return 'select {} from {}'.format(
        sql_columns_list(request), request.GET.get('table')
    ) + sql_where(request) + sql_order_by(request)


def sql_columns_list(request):
    columns = request.GET.get('columns')
    if columns is None:
        return '*'
    return ', '.join(columns.split('~'))


def sql_where(request):
    where = request.GET.get('where')
    if where is None:
        return ''
    return ' where {}'.format(where)


def sql_order_by(request):
    order_by = request.GET.get('order')
    if order_by is None:
        return ''
    return ' order by {}'.format(', '.join(order_by.split('~')))


def dictfetchall(cursor):
    "Returns all rows from a cursor as a dict"
    desc = cursor.description
    return [
        dict(zip([col[0] for col in desc], row))
            for row in cursor.fetchall()
    ]
