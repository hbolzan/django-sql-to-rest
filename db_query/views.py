import simplejson as json
import pprint
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
        columns = request.GET.get("columns")
        where = request.GET.get("where")
        order_by = request.GET.get("order")
        sql = replace_query_params(query.sql_query, request_data_to_dict(request.GET))
        return HttpResponse(
            persistent_query_data_as_json(
                query.name,
                apply_params_to_wrapped_sql(sql, columns, where, order_by)
            ),
            content_type="application/json"
        )

    def post(self, request):
        post_data = json.loads(request.body)
        print(post_data)
        query = get_object_or_404(PersistentQuery, query_id=post_data.get('query'))
        return HttpResponse(
            persistent_query_data_as_json(
                query.name,
                get_insert_sql(query, post_data)
            ),
            content_type="application/json"
        )


def get_insert_sql(query, post_data):
    source, pk_field = query.insert_pk.split("/")
    if pk_field in post_data:
        pk_value = quoted_if_non_numeric(post_data[pk_field])
        sql_retrieve =  "; select * from {} where {} = {};".format(source, pk_field, pk_value)
    else:
        pk_value = None
        sql_retrieve = "; select * from {} where {} = (select max({}) from {});".format(
            source, pk_field, pk_field, source)
    return replace_query_params(query.sql_insert, post_data) + sql_retrieve


def quoted_if_non_numeric(s):
    if type(s) == str:
        return s if s.isnumeric() else "'{}'".format(s)
    return s


def apply_params_to_wrapped_sql(sql, columns, where, order_by):
    if columns is None and where is None and order_by is None:
        return sql
    return 'select {} from {}'.format(
        sql_columns_list(columns),
        "({}) as outer_query".format(sql)
    ) + sql_where(where) + sql_order_by(order_by)


def persistent_query_data_as_json(query_name, sql):
    return json.dumps({
        "status": "OK",
        "query": query_name,
        "data": exec_sql_with_result(sql),
    }, ensure_ascii=False)


def replace_query_params(sql, params):
    """
    Query parameters must use string format syntax
    Example: select * from some_table where id = {id} and age > {min_age}
    """
    return sql.format(**params)


def request_data_to_dict(request_data):
    return {p: request_data.get(p) for p in request_data}


def table_data_as_json(request):
    return json.dumps({
        "status": "OK",
        "table": request.GET.get('table'),
        "data": exec_sql_with_result(get_sql(request)),
    }, ensure_ascii=False)


def exec_sql_with_result(sql):
    cursor = connections['query_db'].cursor()
    cursor.execute(sql)
    return dictfetchall(cursor)


def get_sql(request):
    return 'select {} from {}'.format(
        sql_columns_list(request.GET.get("columns")), request.GET.get('table')
    ) + sql_where(request.GET.get("where")) + sql_order_by(request.GET.get("order"))


def sql_columns_list(columns):
    if columns is None:
        return '*'
    return ', '.join(columns.split('~'))


def sql_where(where):
    if where is None:
        return ''
    return ' where {}'.format(where)


def sql_order_by(order_by):
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
