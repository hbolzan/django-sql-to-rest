from django.test import TestCase
import db_query.views as views


class BuildCustomSQLTestCase(TestCase):
    def test_get_format_keys(self):
        self.assertEqual(views.get_format_keys("{a}, {b}, {c}"), ["a", "b", "c"])

    def test_build_replace_dict(self):
        result = views.build_replace_dict(["a", "b", "c"], {"a": 1, "b": 2, "c": 3, "d": 4}, None)
        self.assertEqual(result, {"a": "1", "b": "2", "c": "3"})

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
            "data": {"a": 1, "b": "BE"}
        }

        self.assertEqual(
            views.get_update_sql(None, "public.teste", "id", request_data, 5),
            "update public.teste set a = 1, b = 'BE' where id = 5"
        )

        custom_sql = "update my.table set x = {x}, a = {a}, b = {b} where my_pk = {pk}"
        self.assertEqual(
            views.get_update_sql(custom_sql, "public.teste", "id", request_data, 5),
            "update my.table set x = x, a = 1, b = 'BE' where my_pk = 5"
        )

    def test_get_insert_sql(self):
        request_data = {
            "data": {"a": 1, "b": "BE"}
        }

        self.assertEqual(
            views.get_insert_sql(None, "public.teste", "id", request_data, None),
            "insert into public.teste (a, b) values (1, 'BE')"
        )

        custom_sql = "insert into my.table (a, b, c) values ({a}, {b}, {c})"
        self.assertEqual(
            views.get_insert_sql(custom_sql, "public.teste", "id", request_data, None),
            "insert into my.table (a, b, c) values (1, 'BE', null)"
        )

    def test_get_delete_sql(self):
        self.assertEqual(
            views.get_delete_sql("delete from my.table where id = {pk}", "my.table", "id", 3),
            "delete from my.table where id = 3"
        )

        self.assertEqual(
            views.get_delete_sql("delete from teste.people where name = {pk}", "my.table", "name", "Fulano"),
            "delete from teste.people where name = 'Fulano'"
        )

        self.assertEqual(
            views.get_delete_sql(None, "my.table", "id", 3),
            "delete from my.table where id = 3"
        )


class BuildUpdateSQLTestCase(TestCase):
    def test_build_update_sql(self):
        request_data = {
            "data": {"a": 1, "b": "BE"}
        }

        self.assertEqual(
            views.build_update_sql("teste", request_data, "id", 5),
            "update teste set a = 1, b = 'BE' where id = 5"
        )

        request_data_b = {
            "data": {"a": 1, "b": "BE"}
        }

        self.assertEqual(
            views.build_update_sql("teste", request_data_b, "id", "char-id"),
            "update teste set a = 1, b = 'BE' where id = 'char-id'"
        )
