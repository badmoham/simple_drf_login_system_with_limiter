from django.core.validators import RegexValidator
from django.utils.translation import gettext_lazy as _

__all__ = ["phone_number_regex_validator"]

phone_number_regex_validator = RegexValidator(regex=r"^09[0-3,9]\d{8}$",
                                              message=_("number you entered is invalid"),
                                              code="invalid number")

