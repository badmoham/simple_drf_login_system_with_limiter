import secrets

from django.contrib.auth.models import AbstractUser
from django.core.validators import RegexValidator
from django.db import models
from django.db.models import Q
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from users.managers import CustomUserManager
from users.validators import phone_number_regex_validator

from samplino.settings import SMS_MAX_WRONG_RETRY, BAN_RETRY_DURATION

__all__ = ["CustomUser", "UserPreRegister", "BannedFromSignUp", "PhoneNumberValidation", "UserSignUpTry"]


class CustomUser(AbstractUser):
    """ model to be used as default user model """
    phone_number = models.CharField(_("phone number"), unique=True, max_length=16,
                                    validators=[phone_number_regex_validator])

    USERNAME_FIELD = "phone_number"
    REQUIRED_FIELDS = []

    objects = CustomUserManager()


class PhoneNumberValidation(models.Model):
    """ will hold phone_number and code send for validation """
    phone_number = models.CharField(_("phone number"), unique=True, max_length=16, validators=[
        RegexValidator(
            regex='^[a-zA-Z0-9]*$',
            message='Username must be Alphanumeric',
            code='invalid_username'
        ),
    ])
    created = models.DateTimeField(_("created at"), auto_now_add=True)
    updated = models.DateTimeField(_("updated at"), auto_now=True)
    last_sent_sms_code = models.CharField(_("last sent sms code"), max_length=16)
    last_sent_sms_datetime = models.DateTimeField(_("last sms sent at"))
    is_validated = models.BooleanField(_("is this number validated using this record"), default=False)

    @staticmethod
    def add_new_validation_code(phone_number: str, user_ip, sms_code):
        """ will create ro update validation record for user registration """
        UserSignUpTry.add_try(phone_number=phone_number, user_ip=user_ip)
        PhoneNumberValidation.objects.update_or_create(phone_number=phone_number, defaults={
            "last_sent_sms_code": sms_code,
            "last_sent_sms_datetime": timezone.now()
        })

    def create_user_pre_register(self) -> str:
        """ will create a UserPreRegister record according to this record """
        unique_registration_id = secrets.token_urlsafe(32)
        UserPreRegister.objects.create(phone_number=self.phone_number, unique_registration_id=unique_registration_id)
        self.is_validated = True
        self.save(update_fields=["is_validated", "updated"])
        return unique_registration_id


class UserPreRegister(models.Model):
    """ this model is used to hold users registration data before confirming their phone_number """

    phone_number = models.CharField(_("phone number"), unique=True, max_length=16, validators=[
        RegexValidator(
            regex='^[a-zA-Z0-9]*$',
            message='Username must be Alphanumeric',
            code='invalid_username'
        ),
    ])
    start_time = models.DateTimeField(_("when user started registering with this number"), auto_now_add=True)
    unique_registration_id = models.CharField(_("unique id given to user to identify for completing registration"),
                                              max_length=32, unique=True)
    is_registered = models.BooleanField(_("is user registered using this record?"), default=False)


class UserSignUpTry(models.Model):
    """ will hold records of signup tries for every try """
    phone_number = models.CharField(_("phone number"), max_length=16, db_index=True)
    user_ip = models.GenericIPAddressField(_("user ip while registering"), db_index=True)
    is_success = models.BooleanField(_("did this try resulted in a success"))
    is_used_for_ban = models.BooleanField(_("is this record used for banning"), default=False)

    @staticmethod
    def add_try(phone_number: str, user_ip: str, is_success: bool = False):
        """ will add a retry record """
        UserSignUpTry.objects.create(phone_number=phone_number, user_ip=user_ip, is_success=is_success)


class UserSignInTry(models.Model):
    """ will hold records of login tries for every try """
    phone_number = models.CharField(_("phone number"), max_length=16, db_index=True)
    user_ip = models.GenericIPAddressField(_("user ip while trying to log in"), db_index=True)
    is_success = models.BooleanField(_("did this try resulted in a success"))
    is_used_for_ban = models.BooleanField(_("is this record used for banning"), default=False)

    @staticmethod
    def add_try(phone_number: str, user_ip: str, is_success: bool = False):
        """ will add a retry record """
        UserSignInTry.objects.create(phone_number=phone_number, user_ip=user_ip, is_success=is_success)


class BannedFromSignUp(models.Model):
    """ records of users/ips that are banned for signup and its durations """
    phone_number = models.CharField(_("phone number"), max_length=16, db_index=True)
    user_ip = models.GenericIPAddressField(_("user ip while registering"), db_index=True)
    banned_until = models.DateTimeField(_("can not retry until"), null=True)

    @staticmethod
    def is_banned(phone_number: str, user_ip: str):
        """ will check if user is or should be banned from singing up """
        is_banned = BannedFromSignUp.objects.filter(Q(phone_number=phone_number) |
                                                    Q(user_ip=user_ip), banned_until__gt=timezone.now()).exists()
        if is_banned is True:
            return True
        signup_tries = UserSignUpTry.objects.filter(Q(phone_number=phone_number) | Q(user_ip=user_ip),
                                                    is_used_for_ban=False, is_success=False)
        if signup_tries.count() >= SMS_MAX_WRONG_RETRY:
            BannedFromSignUp.objects.create(phone_number=phone_number, user_ip=user_ip,
                                            banned_until=timezone.now() + BAN_RETRY_DURATION)
            signup_tries.update(is_used_for_ban=True)
            return True
        return False


class BannedFromSignIn(models.Model):
    """ records of users/ips that are banned for login and its durations """
    phone_number = models.CharField(_("phone number"), max_length=16, db_index=True)
    user_ip = models.GenericIPAddressField(_("user ip while trying to log in"), db_index=True)
    banned_until = models.DateTimeField(_("can not retry until"), null=True)

    @staticmethod
    def is_banned(phone_number: str, user_ip: str):
        """ will check if user is or should be banned from singing in """
        is_banned = UserSignInTry.objects.filter(Q(phone_number=phone_number) |
                                                 Q(user_ip=user_ip), banned_until__gt=timezone.now()).exists()
        if is_banned is True:
            return True
        signup_tries = UserSignInTry.objects.filter(Q(phone_number=phone_number) | Q(user_ip=user_ip),
                                                    is_used_for_ban=False, is_success=False)
        if signup_tries.count() >= SMS_MAX_WRONG_RETRY:
            BannedFromSignIn.objects.create(phone_number=phone_number, user_ip=user_ip,
                                            banned_until=timezone.now() + BAN_RETRY_DURATION)
            signup_tries.update(is_used_for_ban=True)
            return True
        return False

