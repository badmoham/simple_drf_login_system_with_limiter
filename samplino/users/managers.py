""" contain managers for models """
__all__ = ["CustomUserManager"]

from django.contrib.auth.base_user import BaseUserManager


class CustomUserManager(BaseUserManager):
    """ Custom user manager for our custom user model """
    def create_user(self, phone_number, password=None, **extra_fields):
        """ create user by given args """
        if not phone_number:
            raise ValueError('The phone_number field must be set')
        user = self.model(phone_number=phone_number, **extra_fields)
        user.set_password(password)
        user.save()
        return user

    def create_superuser(self, phone_number, password=None, **extra_fields):
        """ create superuser by given args """
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)

        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser must have is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True.')

        return self.create_user(phone_number, password, **extra_fields)