from django.test import TestCase
from db_query.middleware import complex_forms


class ApplyMiddlewareTestCase(TestCase):
    def test_mark_key_column(self):
        """
        data column referenced by some lookup column must be marked with LK type
        """
        self.assertEqual(
            complex_forms.mark_key_column({"campo": "name-b"}, ["name-a", "name-b", "name-c"]),
            {"campo": "name-b", "tipo": "LK"}
        )

        self.assertEqual(
            complex_forms.mark_key_column({"campo": "name-d"}, ["name-a", "name-b", "name-c"]),
            {"campo": "name-d"}
        )
