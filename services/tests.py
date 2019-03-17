from django.test import TestCase
import services.views as views


class ServicesTestCase(TestCase):
    def test_is_service_response_valid(self):
        '''
        service response is expected to be compliant to service guidelines
        it must be a dict with the following format
        {
            "status": "ERROR" | "OK,
            "data": {
                "messages": {
                    "en": "Message in English",
                    "pt-br": "Mensagem em Portugues"
                   [, messages in other languages]
                }
                [, "additional_information": {<a dicitionary with any data}]
            }
        }
        '''
        self.assertTrue(not views.is_service_response_valid("Just some string"))

        self.assertTrue(
            views.is_service_response_valid(
                {"status": "OK", "data": {"messages": {"en": "x", "pt-br": "y"}}}
            )
        )

        self.assertTrue(
            not views.is_service_response_valid(
                {"status": "OK", "data": {"messages": {"en": "x",}}}
            )
        )

    def test_fix_service_response(self):
        """
        fix_service_response is expected to make some smart guesses and return a valid service response
        """
        self.assertEqual(
            views.fix_service_response("Some message"),
            {
                "status": "OK",
                "data": {"messages": {"en": "Some message", "pt-br": "Some message"}}
            }
        )
