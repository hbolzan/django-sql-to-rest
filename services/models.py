import time
from django.db import models
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver


# reset_cache is at the end of this file
VALIDATION_CACHE = {"validations": {}}


def get_validation(name):
    cached_validation = cache_get(name)
    if cached_validation is None:
        return cache_set(name, get_validation_object(name))
    return cached_validation.get("validation")


def get_validation_object(name):
    try:
        return FieldValidation.objects.get(name=name)
    except FieldValidation.DoesNotExist:
        return None


def cache_set(name, validation):
    VALIDATION_CACHE["validations"][name] = {"time": time.time(), "validation": validation}
    return validation


def cache_get(name):
    return VALIDATION_CACHE["validations"].get(name)


class FieldValidation(models.Model):
    """
    FieldValidation class allows adapting existing complex forms validation names
    - name: must match `validacao` field in app_tabelas_complexas_colunas
    - service_name and method_name: identify the service and method that must be called
    - single_argument: name the field which value must be passed as part of the URL when calling the service
    - named_arguments: describe the relations between form fields and method parameters,
                       in pairs `argument_name=field_name`, one line for each pair
    - expected_results: describe expected results and which fields receive them
                        in pairs `field_name<=additional_information_field`
                        assuming that every response have the format
                        {
                            "status": HTTP_STATUS,
                            "data": {
                                "messages": {"en": "Message in english", "pt-br": "Mensagem em português"},
                                "additional_information": {"key": "value", ...}
                            }
                        }

    IMPORTANT
    if no arguments are informed, the validated field value will be sent as a single argument
    """
    name = models.CharField("Validation name", max_length=100, unique=True)
    service_name = models.CharField("Service name", max_length=200)
    method_name = models.CharField("Method name", max_length=200)
    single_argument = models.CharField(
        "Single argument",
        max_length=200,
        blank=True,
        null=True,
        help_text="Single argument source field appended to URI (optional)"
    )
    named_arguments = models.TextField(
        "Named arguments",
        blank=True,
        null=True,
        help_text="Named URL arguments in pairs `argument_name=field_name` (optional)",
    )
    expected_results = models.TextField(
        "Expected results",
        blank=True,
        null=True,
        help_text="Expected results in pairs `field_name<=additional_information_field` (optional)"
    )
    message_on_error = models.BooleanField(
        "Show error message",
        default=True,
        help_text="Indicates whether the frontend should display the returned message if an error occurs"
    )

    def __str__(self):
        return self.name


# @receiver(post_save, sender=FieldValidation)
def reset_cache(sender, **kwargs):
    VALIDATION_CACHE["validations"] = {}


post_save.connect(reset_cache, sender=FieldValidation)
post_delete.connect(reset_cache, sender=FieldValidation)
