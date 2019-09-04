import requests
import functools
from django.shortcuts import get_object_or_404
from db_query.models import PersistentQuery


def apply_middleware(raw_data, exec_sql_fn, *args, **kw_args):
    return adapt_bundle(raw_data[0], exec_sql_fn)


def adapt_bundle(raw_data, exec_sql_fn):
    return {
        "id": raw_data.get("id"),
        "form-title": raw_data.get("titulo_do_form"),
        "bundled-tables": adapt_bundled_tables(raw_data.get("bundled-tables"), exec_sql_fn),
    }


def adapt_bundled_tables(bundled_tables, exec_sql_fn):
    return [adapt_bundled_table(table, exec_sql_fn) for table in bundled_tables]


def adapt_bundled_table(table, exec_sql_fn):
    raw_params = params_to_dict(table.get("parametros").split("\n"))
    return {
        "tab-title": raw_params.get("TITULO_ABA"),
        "master": raw_params.get("PAINEL_MASTER") == "S",
        "complex-id": raw_params.get("COMPLEXA_ID"),
        "detail": raw_params.get("DETAIL") == "S",
        "related-fields": [c.strip() for c in raw_params.get("COLUNAS_DETAIL", "").split(",")],
        "master-fields": [c.strip() for c in raw_params.get("COLUNAS_MASTER", "").split(",")],
        "bundle-actions": parse_bundle_actions(raw_params.get("BUNDLE_ACTIONS", "")),
        "definition": fix_none_results(get_child_definition(raw_params.get("COMPLEXA_ID"))),
    }


def parse_bundle_actions(raw_actions):
    try:
        return [parse_bundle_action(raw_action) for raw_action in raw_actions.split("~")]
    except (IndexError, AttributeError):
        return []


def parse_bundle_action(raw_action):
    """
    Parse action attributes such as
    caption:Recalcular;type:primary;action:reglass_cotacoes.recalcular;enabled-states:@view,pending
    """
    def parse_array_attr(attr):
        print(attr)
        if attr[0] != "@":
            return attr
        return attr[1:].split(",")

    def parse_attr(attrs, attr):
        attr_parts = attr.split(":")
        return dict(attrs, **{attr_parts[0]: parse_array_attr(attr_parts[1])})

    return functools.reduce(
        parse_attr,
        [action_attrs for action_attrs in raw_action.split(";")],
        {}
    )


def get_complex_definition(raw_params):
    if raw_params.get("DETAIL") != "S":
        return None
    complex_id = raw_params.get("COMPLEXA_ID")
    related_fields = [c.strip() for c in raw_params.get("COLUNAS_DETAIL", "").split(",")]
    master_fields = [c.strip() for c in raw_params.get("COLUNAS_MASTER", "").split(",")]


# TODO: do this in a better way
HOST = "http://localhost:8000"
PATH = "/api/query/persistent/complex-tables/?id={id}&middleware=complex_forms&depth=1"
BASE_URL = HOST + PATH

def get_child_definition(complex_id):
    r = requests.get(BASE_URL.format(id=complex_id))
    if r.status_code == 200:
        return r.json().get("data")
    return {}


def fix_none_results(data):
    if isinstance(data, dict):
        return {k: fix_none_results(v) for k, v in data.items()}

    if isinstance(data, list):
        return [fix_none_results(v) for v in data]

    if data == "None":
        return None
    return data


def params_to_dict(params):
    def split_param(param):
        p = param.split("=")
        if len(p) < 2:
            return [param, None]
        return p[0], p[1].strip()

    return {p[0]: p[1] for p in map(split_param, params)}


# "COMPLEXA_ID": None,
# "TITULO_ABA": "tab-title",
# "PAINEL_MASTER": "master",
# "DETAIL": None,
# "COLUNAS_DETAIL": "related-columns",
# "COLUNAS_MASTER": "master-columns",
# "DETAIL_PAGINA_MASTER": ,
