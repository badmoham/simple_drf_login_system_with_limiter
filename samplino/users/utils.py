""" contain utility functions """
import random
import string

from samplino.settings import REGISTRATION_SMS_CODE_LENGTH

__all__ = ["send_registration_code", "get_user_ip"]


def send_sms_in_an_awesome_and_async_manner(sms_code, sms_number):
    """ will do as thr name state """
    ...


def generate_random_code(length) -> str:
    """ will generate random numbers with given length """
    return ''.join(random.choices(string.digits, k=length))


def send_registration_code(phone_number) -> str:
    """ will send registration code to given number and return the code """
    code = generate_random_code(REGISTRATION_SMS_CODE_LENGTH)
    send_sms_in_an_awesome_and_async_manner(sms_code=code, sms_number=phone_number)
    # return code
    return "123456"  # we will return a static code for testing


def get_user_ip(request) -> str:
    """will parse a request Meta for user ip and return user_ip"""
    if request.META.get('HTTP_X_FORWARDED_FOR', False):
        return request.META['HTTP_X_FORWARDED_FOR'].split(',')[0]
    return request.META.get('REMOTE_ADDR')

