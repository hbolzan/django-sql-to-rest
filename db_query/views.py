import os
import sys
import re
import importlib
import pprint
import string
import simplejson as json
from datetime import date, datetime
from functools import reduce
from django.core.serializers import serialize
from django.core.exceptions import ValidationError
from django.core.serializers.json import DjangoJSONEncoder
from django.utils.encoding import force_text
from django.conf import settings
from django.shortcuts import render, get_object_or_404
from django.http import HttpResponse
from django.views import View
from django.db import connections
from django_sql_to_rest.common import trace
from dstr_common_lib.controller import handle_simple_service_request
from db_query.models import PersistentQuery


DELETE = "DELETE"
POST = "POST"
PUT = "PUT"
OPTIONS = "OPTIONS"

REPLACE_WITH_KEY = "K"
REPLACE_WITH_NULL = "N"
DEFAULT_CONN_NAME = 'query_db'


def load_middleware():
    pysearchre = re.compile('.py$', re.IGNORECASE)
    pluginfiles = filter(pysearchre.search, os.listdir(os.path.join(os.path.dirname(__file__), 'middleware')))
    package_name = os.path.dirname(__file__).split(os.sep)[-1] + ".middleware"
    form_module = lambda fp: '.' + os.path.splitext(fp)[0]
    plugins = map(form_module, pluginfiles)
    return {
        plugin.strip("."): importlib.import_module(plugin, package=package_name)
            for plugin in plugins if not plugin.startswith('.__')
    }

MIDDLEWARE = load_middleware()


class DbQueryAdhoc(View):
    def get(self, request):
        return HttpResponse(table_data_as_json(request), content_type="application/json")


class DbWithConnQueryAdhoc(View):
    def get(self, request, conn_name):
        return HttpResponse(table_data_as_json(request, conn_name), content_type="application/json")


class DbBaseQueryPersistent(View):

    http_method_names = ["options", "get", "post", "put", "delete"]

    def __init__(self):
        self.http_method_names = ['options', 'get', 'post', 'put', 'delete']

    def options(self, request, query_id=None):
        response = HttpResponse()
        response['allow'] = ','.join(self.http_method_names)
        return response


class DbQueryPersistent(DbBaseQueryPersistent):

    def get(self, request, query_id):
        return do_get(request, query_id)

    def post(self, request, query_id):
        return do_method(self, request, query_id, POST, get_insert_sql)

    def put(self, request, query_id, pk):
        return do_method(self, request, query_id, PUT, get_update_sql, pk)

    def delete(self, request, query_id, pk):
        return do_delete(request, query_id, pk)


class DbWithConnQueryPersistent(DbBaseQueryPersistent):

    def get(self, request, conn_name, query_id):
        return do_get(request, query_id, conn_name)

    def post(self, request, conn_name, query_id):
        return do_method(self, request, query_id, POST, get_insert_sql, None, conn_name)

    def put(self, request, conn_name, query_id, pk):
        return do_method(self, request, query_id, PUT, get_update_sql, pk, conn_name)

    def delete(self, request, conn_name, query_id, pk):
        return do_delete(request, query_id, pk, conn_name)


class DbBaseQueryPersistentBatch(View):

    http_method_names = ["options", "post",]

    def get_insert_sql(self, query, source, row):
        return get_insert_sql(query.sql_insert, source, None, {"data": row}, None) + ";"

    def get_update_sql(self, query, source, pk_fields, row):
        pk_values = [value_to_sql(row.get(k)) for k in pk_fields]
        return get_update_sql(query.sql_update, source, pk_fields, {"data": row}, pk_values) + ";"

    def get_delete_sql(self, query, source, pk_fields, row):
        pk_values = [value_to_sql(v) for k, v in row.items() if k in pk_fields]
        return get_delete_sql(query.sql_delete, source, pk_fields, pk_values) + ";"


class DbQueryPersistentBatch(DbBaseQueryPersistentBatch):
    def post(self, request, query_id):
        return do_batch_post(self, request, query_id)


class DbWithConnQueryPersistentBatch(DbBaseQueryPersistentBatch):
    def post(self, request, conn_name, query_id):
        return do_batch_post(self, request, query_id, conn_name)


def do_batch_post(self, request, query_id, _conn_name=None):
    request_data = json.loads(request.body)
    query = get_query_obj(query_id)
    conn_name = _conn_name or query.conn_name or DEFAULT_CONN_NAME
    source, _ = query.insert_pk.split("/")
    pk_fields = request_data.get("data", {}).get("meta", {}).get("pk-fields")
    try:
        inserts = [self.get_insert_sql(query, source, apply_service_method(query.before_insert, row))
               for row in request_data.get("data", {}).get("append", [])]
        updates = [self.get_update_sql(query, source, pk_fields, apply_service_method(query.before_update, row))
               for row in request_data.get("data", {}).get("update", [])]
        deletes = [self.get_delete_sql(query, source, pk_fields, apply_service_method(query.before_delete, row))
               for row in request_data.get("data", {}).get("delete", [])]
    except Exception as error:
        return service_error_response(error.args[0], status=500)
    "\n".join(deletes + updates + inserts)
    exec_sql("\n".join(deletes + updates + inserts), conn_name)
    return HttpResponse(json.dumps({"data": "OK"}), content_type="application/json")


def apply_middleware(data, middleware, exec_sql_fn):
    if middleware is None:
        return data
    mw_fns = [MIDDLEWARE.get(mw).apply_middleware for mw in middleware.split("~")]
    return reduce(lambda d, fn: fn(d, exec_sql_fn), mw_fns, data)


def get_children(parent_query, parent_data, depth, exec_sql_fn):
    if depth < 1:
        return parent_data
    return [get_current_row_children(row, parent_query, depth, exec_sql_fn) for row in parent_data]


def get_current_row_children(data_row, parent_query, depth, exec_sql_fn):
    _, parent_pk_field = parent_query.insert_pk.split("/")
    parent_pk = data_row.get(parent_pk_field)
    for nested_query in parent_query.nested_query.all():
        base_sql = nested_query.child.sql_query
        sql = base_sql.format(parent_pk=value_to_sql(parent_pk))
        data_row[nested_query.attr_name] = get_children(
            nested_query.child,
            exec_sql_fn(sql),
            depth-1,
            exec_sql_fn
        )
    return data_row


def do_get(request, query_id, _conn_name=None):
    query = get_object_or_404(PersistentQuery, query_id=query_id)
    conn_name = _conn_name or query.conn_name or DEFAULT_CONN_NAME
    exec_sql_fn = lambda sql: exec_sql_with_result(sql, conn_name)
    columns = request.GET.get("columns")
    where = request.GET.get("where")
    depth = int(request.GET.get("depth", 0))
    order_by = request.GET.get("order")
    sql = replace_query_params(query.sql_query, request_data_to_dict(request.GET), None)
    data = apply_middleware(
        get_children(
            query,
            exec_sql_fn(apply_params_to_wrapped_sql(sql, columns, where, order_by)),
            depth,
            exec_sql_fn
        ),
        request.GET.get("middleware"),
        lambda conn: lambda sql: exec_sql_with_result(sql, conn or conn_name)
    )
    return HttpResponse(
        persistent_query_data_as_json(query.name, data),
        content_type="application/json"
    )


def do_delete(request, query_id, pk, _conn_name=None):
    query = get_query_obj(query_id)
    conn_name = _conn_name or query.conn_name or DEFAULT_CONN_NAME
    source, pk_field = query.insert_pk.split("/")
    return HttpResponse(
        persistent_query_execute(
            query.name,
            get_delete_sql(query.sql_delete, source, pk_field, pk),
            conn_name
        ),
        content_type="application/json"
    )


def do_method(self, request, query_id, method, get_sql_fn, pk_value=None, _conn_name=None):
    query = get_query_obj(query_id)
    before_method_action = get_before_method_action(method, query)
    try:
        request_data = apply_service_method(before_method_action,  json.loads(request.body))
    except Exception as error:
        return service_error_response(error.args[0], status=500)
    conn_name = _conn_name or query.conn_name or DEFAULT_CONN_NAME
    source, pk_field = query.insert_pk.split("/")
    sql = get_sql_fn(custom_sql_by_method(query, method), source, pk_field, request_data, pk_value)
    sql_retrieve = get_sql_retrieve(
        get_query_source(source, query),
        pk_field,
        get_retrieve_pk_value(request_data, pk_field, query.query_pk, pk_value)
    )
    data = exec_sql_with_result(sql+sql_retrieve, conn_name)
    return HttpResponse(
        persistent_query_data_as_json(query.name, data),
        content_type="application/json"
    )


def get_before_method_action(method, query):
    return {
        POST: query.before_insert,
        PUT: query.before_update,
        DELETE: query.before_delete,
    }.get(method)


def apply_service_method(action, payload):
    try:
        service, method = action.split("/")
    except (AttributeError, ValueError):
        return payload

    service_response = handle_simple_service_request(service, method, payload)
    if is_service_error(service_response):
        raise Exception(service_response)
    return service_response or payload


def is_service_error(service_response):
    return bool(
        isinstance(service_response, dict) and
        service_response.get("status") and
        service_response["status"] == "ERROR"
    )


def service_error_response(response, status):
    return HttpResponse(
        content=json.dumps(response, ensure_ascii=False),
        content_type="application/json",
        status=status
    )


def get_query_source(source, query):
    if not query.sql_query:
        return source
    return "({}) qsearch".format(query.sql_query.replace("{_search_}", "'%%'"))


def get_retrieve_pk_value(request_data, pk_field, query_pk, pk_value):
    if not pk_value:
        pk_value = request_data.get('data', {}).get(pk_field)
    if not query_pk or not pk_value:
        return pk_value
    return replace_query_pk(query_pk, pk_value)


def replace_query_pk(query_pk, pk_value):
    if pk_value:
        try:
            return query_pk.replace("{pk_value}", pk_value)
        except AttributeError:
            return pk_value
    return pk_value


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


def get_sql_retrieve(source, pk_field, pk_value):
    if pk_value:
        return "; select * from {} where {} = {};".format(
            source, pk_field, value_to_sql(pk_value)
        )
    return "; select * from {} where {} = (select max({}) from {});".format(
        source, pk_field, pk_field, source
    )


def get_insert_sql(custom_sql, source, pk_field, request_data, _):
    if custom_sql is None or not custom_sql.strip():
        return build_insert_sql(source, request_data)
    return replace_query_params(
        custom_sql.replace("{pk}", value_to_sql(request_data.get("pk"))),
        request_data.get("data"),
        REPLACE_WITH_NULL
    )


def get_update_sql(custom_sql, source, pk_field, request_data, pk_value):
    if custom_sql is None or not custom_sql.strip():
        return build_update_sql(source, request_data, pk_field, pk_value)
    return replace_query_params(
        custom_sql.replace("{pk}", value_to_sql(pk_value)),
        request_data.get("data"),
        REPLACE_WITH_KEY
    )


def get_delete_sql(custom_sql, source, pk_field, pk_value):
    if custom_sql is None or not custom_sql.strip():
        return build_delete_sql(source, pk_field, pk_value)
    return replace_query_params(custom_sql, {"pk": pk_value}, REPLACE_WITH_NULL)


def build_delete_sql(source, pk_field, pk_value):
    return "delete from {} where {}".format(source, build_where(pk_field, pk_value))


def build_insert_sql(table_name, request_data):
    data = request_data.get("data")
    return "insert into {} ({}) values ({})".format(
        table_name,
        build_insert_columns_list(data),
        build_insert_values_list(data)
    )


def build_update_sql(table_name, request_data, pk_field_name, pk_value):
    data = request_data.get("data")
    return 'update {} set {} where {}'.format(
        table_name,
        build_columns_assignments(data, pk_field_name),
        build_where(pk_field_name, pk_value)
    )


def build_insert_columns_list(data):
    return ", ".join([k for k, v in data.items()])


def build_insert_values_list(data):
    return ", ".join([value_to_sql(v) for k, v in data.items()])


def build_columns_assignments(data, pk_field_name):
    return ", ".join(
        ["{} = {}".format(k, value_to_sql(v))
         for k, v in data.items()]
    )


def build_where(pk_field, pk_value):
    if isinstance(pk_field, list):
        return " and ".join([_build_where(field, value) for field, value in zip(pk_field, pk_value)])
    return _build_where(pk_field, pk_value)


def _build_where(pk_field_name, pk_value):
    if pk_value == "null":
        return "{} is null".format(pk_field_name)
    return "{} = {}".format(pk_field_name, value_to_sql(pk_value))


def value_to_sql(value):
    if value is None:
        return 'null'
    return str(quoted_if_non_numeric(value))


# TODO: REFACTOR THIS!!!
def quoted_if_non_numeric(s):
    if s == "null":
        return s
    return "'{}'".format(str(s).strip("'"))
    # if type(s) == str:
    #     return s if s.isnumeric() else "'{}'".format(s.strip("'"))
    # return s


def apply_params_to_wrapped_sql(sql, columns, where, order_by):
    if columns is None and where is None and order_by is None:
        return sql
    return 'select {} from {}'.format(
        sql_columns_list(columns),
        "({}) as outer_query".format(sql)
    ) + sql_where(where) + sql_order_by(order_by)


def persistent_query_execute(query_name, sql, conn_name):
    cursor = exec_sql(sql, conn_name)
    return json.dumps({
        "status": "OK",
        "query": query_name,
        "affected_rows": cursor.rowcount,
    }, ensure_ascii=False)


def json_serial(obj):
    """JSON serializer for objects not serializable by default json code"""
    if isinstance(obj, (datetime, date)):
        return obj.isoformat()
    raise TypeError ("Type %s not serializable" % type(obj))


def persistent_query_data_as_json(query_name, data):
    return json.dumps(
        {
            "status": "OK",
            "query": query_name,
            "data": data,
        },
        ensure_ascii=False,
        default=json_serial
    )


def replace_query_params(sql, params, default_rule):
    """
    Replace sql params using string format.
    * Expected keys missing in params will be replaced according to default_rule (key or null).
    * Non numeric values will be automatically quoted.
    * Query parameters must use string format syntax
      Example:
          select * from some_table where id = {id} and age > {min_age}
    * Special key _search_ will be replaced with %<value>%
    """
    return sql.format(**build_replace_dict(get_format_keys(sql), params, default_rule))


def build_replace_dict(expected_keys, params, default_rule):
    replace_dict = {}
    for xk in expected_keys:
        param_value = params.get(xk)
        if param_value is None:
            value = xk if default_rule == REPLACE_WITH_KEY else "null"
        else:
            value = value_to_sql(modify_special_search_value(xk, param_value))
        replace_dict[xk] = value
    return replace_dict


def modify_special_search_value(key, param_value):
    if key == "_search_":
        return "%{}%".format(param_value)
    return param_value


def get_format_keys(s):
    f = string.Formatter()
    return [k[1] for k in f.parse(s)]


def request_data_to_dict(request_data):
    return {p: request_data.get(p) for p in request_data}


def table_data_as_json(request, conn_name=DEFAULT_CONN_NAME):
    return json.dumps({
        "status": "OK",
        "table": request.GET.get('table'),
        "data": exec_sql_with_result(get_sql(request), conn_name),
    }, ensure_ascii=False)


def exec_sql_with_result(sql, conn_name):
    return dictfetchall(exec_sql(sql, conn_name))


def exec_sql(sql, conn_name):
    cursor = connections[conn_name].cursor()
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
