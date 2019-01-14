from django.test import TestCase
import db_query.views as views


class BuildCustomSQLTestCase(TestCase):
    def test_get_format_keys(self):
        self.assertEqual(views.get_format_keys("{a}, {b}, {c}"), ["a", "b", "c"])

    def test_build_replace_dict(self):
        result = views.build_replace_dict(["a", "b", "c"], {"a": 1, "b": 2, "c": 3, "d": 4}, None)
        self.assertEqual(result, {"a": 1, "b": 2, "c": 3})

    def test_replace_query_params(self):
        """
        String params must be replaced with corresponding arguments from params dictionary
        """
        self.assertEqual(
            views.replace_query_params("{a}, {b}, {c}", {"a": 1, "b": "BE", "c": 3}, None),
            "1, 'BE', 3"
        )

        self.assertEqual(
            views.replace_query_params("{a}, {b}, {c}", {"a": 1, "b": "BE"}, views.REPLACE_WITH_KEY),
            "1, 'BE', c"
        )

        self.assertEqual(
            views.replace_query_params("{a}, {b}, {c}", {"a": 1, "b": "BE"}, views.REPLACE_WITH_NULL),
            "1, 'BE', null"
        )

    def test_get_update_sql(self):
        request_data = {
            "pk": 5,
            "update_data": {"a": 1, "b": "BE"}
        }

        self.assertEqual(
            views.get_update_sql(None, "public.teste", "id", request_data),
            "update public.teste set a = 1, b = 'BE' where id = 5"
        )

        custom_sql = "update my.table set x = {x}, a = {a}, b = {b} where my_pk = {pk}"
        self.assertEqual(
            views.get_update_sql(custom_sql, "public.teste", "id", request_data),
            "update my.table set x = x, a = 1, b = 'BE' where my_pk = 5"
        )


class BuildSQLTestCase(TestCase):
    def test_build_update_sql(self):
        request_data = {
            "pk": 5,
            "update_data": {"a": 1, "b": "BE"}
        }

        self.assertEqual(
            views.build_update_sql("teste", request_data, "id"),
            "update teste set a = 1, b = 'BE' where id = 5"
        )

    def test_build_update_sql_2(self):
        request_data = {
            "pk": "char-id",
            "update_data": {"a": 1, "b": "BE"}
        }

        self.assertEqual(
            views.build_update_sql("teste", request_data, "id"),
            "update teste set a = 1, b = 'BE' where id = 'char-id'"
        )
