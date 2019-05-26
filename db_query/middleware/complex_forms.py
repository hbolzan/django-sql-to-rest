import functools
from services.models import get_validation


YES = "S"
NO = "N"
LOOKUP_KEY = "LK"

FIELD_KINDS = {
    "C": "yes-no",
    "D": "data",
    "L": "lookup",
}

DATA_TYPES = {
    "C": "char",
    "D": "date",
    "E": "time",
    "F": "float",
    "I": "integer",
    "M": "memo",
    "T": "timestamp",
}

ALIGNMENTS = {
    "C": "center",
    "D": "default",
    "L": "left",
    "R": "right",
}


def apply_middleware(raw_data, exec_sql_fn):
    return list(map(functools.partial(adapt_complex_table, exec_sql_fn, get_validation), raw_data))


def adapt_complex_table(exec_sql_fn, get_validation_fn, raw_complex_table):
    fields_defs = adapt_columns(raw_complex_table.get("columns"), exec_sql_fn, get_validation_fn)
    editable = raw_complex_table.get("read_only") != "S"
    return {
        "id": raw_complex_table.get("id").replace("_", "-").lower(),
        "dataset-name": raw_complex_table.get("tabela_nome").split(";")[0].replace('.', '-'),
        "title": raw_complex_table.get("descricao"),
        "pk-fields": raw_complex_table.get("coluna_pk").split(","),
        "auto-pk": raw_complex_table.get("pk_automatica") == "S",
        "order-by-fields": raw_complex_table.get("coluna_order_by").split(","),
        "permissions": {
            "insert": editable and raw_complex_table.get("pode_inserir") == "S",
            "edit": editable and raw_complex_table.get("pode_editar") == "S",
            "delete": editable and raw_complex_table.get("pode_excluir") == "S",
        },
        "fields-defs": fields_defs,
        "search-columns": sorted(
            filter(lambda c: c["search-result?"], fields_defs),
            key=lambda c: c.get("search-result-order") or 0
        ),
    }


def adapt_columns(raw_columns, exec_sql_fn, get_validation_fn):
    marked_raw_columns = mark_key_columns(raw_columns)
    key_columns = filter(lambda c: c.get("tipo") == LOOKUP_KEY, marked_raw_columns)
    return [merge_lookup_column(c, key_columns, exec_sql_fn, get_validation_fn)
            for c in marked_raw_columns
            if c.get("tipo") != LOOKUP_KEY and c.get("visivel") == YES]


def mark_key_columns(raw_columns):
    lookup_columns_names = list(
        map(
            lambda c: c.get("lookup_campos_chave"),
            filter(lambda c: c.get("tipo") == "L", raw_columns)
        )
    )
    if lookup_columns_names:
        return [mark_key_column(c, lookup_columns_names) for c in raw_columns]
    return raw_columns


def mark_key_column(column, lookup_columns_names):
    if column.get("campo") in lookup_columns_names:
        return dict(column, tipo=LOOKUP_KEY)
    return column


def merge_lookup_column(column, key_columns, exec_sql_fn, get_validation_fn):
    # find corresponding data column
    if column.get("tipo") == "L":
        key_field = column.get("lookup_campos_chave")
        try:
            key_column = next(filter(lambda c: c.get("campo") == key_field, key_columns))
            valor_default = key_column.get("valor_default")
            return dict(
                adapt_column(column, get_validation_fn),
                **{
                    "name": key_field,
                    "data-type": DATA_TYPES.get(key_column.get("data_type"), "char"),
                    "default": valor_default if valor_default else None,
                    "options": process_lookup_options(column, exec_sql_fn),
                }
            )
        except IndexError:
            return adapt_column(column, get_validation_fn)
    return adapt_column(column, get_validation_fn)


def adapt_column(column, get_validation_fn):
    default_value = str(column.get("valor_default", "")).strip()
    return dict({
        "order": column.get("ordem"),
        "name": column.get("campo"),
        "label": column.get("caption"),
        "field-kind": FIELD_KINDS.get(column.get("tipo"), "D"),
        "required": column.get("obrigatorio") == YES,
        "visible": column.get("visivel") == YES,
        "read-only": column.get("read_only") == YES,
        "persistent": column.get("gravar") == YES,
        "data-type": DATA_TYPES.get(column.get("data_type"), "char"),
        "alignment": ALIGNMENTS.get(column.get("alinhamento"), "default"),
        "default": default_value if default_value else None,
        "size": column.get("tamanho"),
        "width": column.get("largura"),
        "lookup-key": column.get("lookup_campos_lookup"),
        "lookup-result": column.get("lookup_campo_resultado"),
        "lookup-filter": column.get("lookup_filtro"),
        "validation": adapt_validation(column.get("validacao"), get_validation_fn),
        "search-result?": column.get("visivel_pesquisa") == "S",
        "search-result-order": column.get("ordem_pesquisa")
    }, **adapt_input_mask(column.get("mascara")))


def adapt_validation(validation_name, get_validation_fn):
    validation = get_validation_fn(validation_name)
    if not hasattr(validation, "method_name"):
        return None
    return {
        "service": validation.service_name,
        "method": validation.method_name,
        "single-argument": validation.single_argument,
        "named-arguments": split_kv_multilines(validation.named_arguments, "="),
        "expected-results": split_kv_multilines(validation.expected_results, "<="),
        "show-message-on-error": validation.message_on_error,
        "before-validate": split_lines(validation.before_validate),
    }


def split_kv_multilines(lines_str, kv_separator):
    try:
        return {pair[0]: pair[1] for pair in
                [l.strip().split(kv_separator) for l in lines_str.split("\n")]
                if len(pair) > 1}
    except AttributeError:
        return lines_str


def split_lines(lines_str):
    try:
        return [l.strip() for l in lines_str.split("\n")]
    except AttributeError:
        return None


def adapt_input_mask(original_mask):
    if not original_mask:
        return {}
    mask, maskchar = split_mask_and_maskchar(original_mask)
    format_chars = {"9": "[0-9]", "a": "[A-Za-z]", "A": "[A-Z]", "*": "[A-Za-z0-9]"}
    # TODO: peraments
    return {
        "mask": mask,
        "mask-char": maskchar,
        "format-chars": format_chars,
    }


def split_mask_and_maskchar(original_mask):
    mask_parts = original_mask.split(";")
    try:
        mask, maskchar = mask_parts
    except ValueError:
        mask = mask_parts[0]
        maskchar = "_" if len(mask_parts) == 1 else mask_parts[-1]
    return fix_mask(mask), maskchar


def fix_mask(mask):
    return mask.replace("dd/mm/yyyy", "99/99/9999") \
        .replace("hh:nn", "99:99") \
        .replace("hh:mm", "99:99") \
        .replace("#", "9") \
        .replace("0", "9") \
        .replace(">", "") \
        .replace("L", "A")


def process_lookup_options(column, exec_sql_fn):
    return exec_sql_fn(column.get("lookup_query_sql"))
