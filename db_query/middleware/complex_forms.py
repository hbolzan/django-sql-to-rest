YES = "S"
NO = "N"

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


def apply_middleware(raw_data):
    return list(map(adapt_complex_table, raw_data))


def adapt_complex_table(raw_complex_table):
    return {
        "id": raw_complex_table.get("id").replace("_", "-").lower(),
        "dataset-name": raw_complex_table.get("tabela_nome").split(";")[0],
        "title": raw_complex_table.get("descricao"),
        "fields-defs": adapt_columns(raw_complex_table.get("columns")),
    }


def adapt_columns(raw_columns):
    return [adapt_column(c) for c in raw_columns]


def adapt_column(column):
    default_value = str(column.get("valor_default", "")).strip()
    return {
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
        # "options": column.get(""),
        "default": default_value if default_value else None,
        "size": column.get("tamanho"),
        "width": column.get("largura"),
    }
