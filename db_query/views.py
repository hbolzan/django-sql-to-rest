import simplejson as json
import pprint
import string
from django.utils.encoding import force_text
from django.shortcuts import render, get_object_or_404
from django.http import HttpResponse
from django.views import View
from django.db import connections
from db_query.models import PersistentQuery


DELETE = "DELETE"
POST = "POST"
PUT = "PUT"

REPLACE_WITH_KEY = "K"
REPLACE_WITH_NULL = "N"


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

    http_method_names = ["get", "post", "put", "delete"]

    def post(self, request):
        print(POST)
        return self.post_put_delete(request, POST)

    def put(self, request):
        request_data = json.loads(request.body)
        query = get_query_obj(request_data.get("query"))
        source, pk_field = query.insert_pk.split("/")
        sql = get_update_sql(query.sql_update, source, pk_field, request_data)
        sql_retrieve =  "; select * from {} where {} = {};".format(
            source, pk_field, request_data.get("pk")
        )
        return HttpResponse(
            persistent_query_data_as_json(query.name, sql+sql_retrieve),
            content_type="application/json"
        )

    def delete(self, request, query, pk):
        print(DELETE, query, pk)
        return self.post_put_delete(request, DELETE, query, pk)

    def post_put_delete(self, request, method, query_id=None, delete_pk=None):
        query = get_query_obj(query_id)
        sql = custom_sql_by_method(query, method)
        replace_sql_fn = get_delete_sql if method == DELETE else get_insert_or_update_sql
        exec_fn = persistent_query_execute if method == DELETE else persistent_query_data_as_json
        return HttpResponse(
            exec_fn(
                query.name,
                trace(replace_sql_fn(query, request, sql, delete_pk))
            ),
            content_type="application/json"
        )


def trace(x):
    print(x)
    return x


def get_query_obj(query_id):
    return get_object_or_404(
        PersistentQuery,
        query_id=query_id
    )


def custom_sql_by_method(query, method):
   return {
        POST: query.sql_insert,
        PUT: query.sql_update,
        DELETE: query.sql_delete
    }[method]


def get_insert_or_update_sql(query, request, sql_dml, delete_pk):
    request_data = json.loads(request.body)
    source, pk_field = query.insert_pk.split("/")
    if pk_field in request_data:
        pk_value = quoted_if_non_numeric(request_data[pk_field])
        sql_retrieve =  "; select * from {} where {} = {};".format(source, pk_field, pk_value)
    else:
        sql_retrieve = "; select * from {} where {} = (select max({}) from {});".format(
            source, pk_field, pk_field, source)
    return replace_query_params(sql_dml, request_data) + sql_retrieve


def get_insert_sql(custom_sql, source, pk_field, request_data):
    pk_value = request_data.get("pk")
    return replace_query_params(
        custom_sql.replace("{pk}", str(quoted_if_non_numeric(pk_value))),
        request_data.get("data"),
        REPLACE_WITH_NULL
    )


def get_update_sql(custom_sql, source, pk_field, request_data):
    pk_value = request_data.get("pk", "null")
    if custom_sql is None or not custom_sql.strip():
        return build_update_sql(source, request_data, pk_field)
    return replace_query_params(
        custom_sql.replace("{pk}", str(quoted_if_non_numeric(pk_value))),
        request_data.get("data"),
        REPLACE_WITH_KEY
    )


def build_update_sql(table_name, request_data, pk_field_name):
    data = request_data.get("data")
    pk_value = request_data.get("pk", "null")
    return 'update {} set {} where {}'.format(
        table_name,
        build_columns_assignments(data, pk_field_name),
        build_where(pk_field_name, pk_value)
    )


def build_columns_assignments(data, pk_field_name):
    return ", ".join(
        ["{} = {}".format(k, quoted_if_non_numeric(v))
         for k, v in data.items()]
    )


def build_where(pk_field_name, pk_value):
    return "{} = {}".format(pk_field_name, quoted_if_non_numeric(pk_value))


def get_delete_sql(query, request, sql, pk):
    return replace_query_params(sql, {"pk": pk})


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


def persistent_query_execute(query_name, sql):
    cursor = exec_sql(sql)
    return json.dumps({
        "status": "OK",
        "query": query_name,
        "affected_rows": cursor.rowcount,
    }, ensure_ascii=False)


def persistent_query_data_as_json(query_name, sql):
    return json.dumps({
        "status": "OK",
        "query": query_name,
        "data": exec_sql_with_result(sql),
    }, ensure_ascii=False)


def replace_query_params(sql, params, default_rule):
    """
    Replace sql with params with string format.
    * Expected keys missing in params will be replaced according to default_rule (key or null).
    * Non numeric values will be automatically quoted.
    * Query parameters must use string format syntax
      Examples: select * from some_table where id = {id} and age > {min_age}
    """
    return sql.format(**build_replace_dict(get_format_keys(sql), params, default_rule))

def build_replace_dict(expected_keys, params, default_rule):
    replace_dict = {}
    for xk in expected_keys:
        param_value = params.get(xk)
        if param_value is None:
            value = xk if default_rule == REPLACE_WITH_KEY else "null"
        else:
            value = quoted_if_non_numeric(param_value)
        replace_dict[xk] = value
    return replace_dict


def get_format_keys(s):
    f = string.Formatter()
    return [k[1] for k in f.parse(s)]


def request_data_to_dict(request_data):
    return {p: request_data.get(p) for p in request_data}


def table_data_as_json(request):
    return json.dumps({
        "status": "OK",
        "table": request.GET.get('table'),
        "data": exec_sql_with_result(get_sql(request)),
    }, ensure_ascii=False)


def exec_sql_with_result(sql):
    return dictfetchall(exec_sql(sql))


def exec_sql(sql):
    cursor = connections['query_db'].cursor()
    cursor.execute(sql)
    return cursor


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
