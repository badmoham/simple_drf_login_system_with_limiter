from rest_framework.generics import CreateAPIView
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

from rest_framework_simplejwt.views import TokenObtainPairView

from users.models import CustomUser, BannedFromSignUp, PhoneNumberValidation, UserSignUpTry, BannedFromSignIn, \
    UserSignInTry
from users.serializers import UserPhoneNumberSerializer, PhoneNumberValidationSerializer, UserRegisterSerializer, \
    UserSignInSerializer
from users.utils import get_user_ip, send_registration_code
__all__ = ["UserExistView", "SignInView", "SendSMSForRegistrationView", "RegistrationConfirmSMSView", "UserRegisterView"]


class UserExistView(APIView):
    """ will answer if a user with a phone_number exist or not """

    def post(self, request):
        """
        take a phone number and return True if user exists else False.
        """
        serializer = UserPhoneNumberSerializer(data=request.POST)
        serializer.is_valid(raise_exception=True)
        user_exist = CustomUser.objects.filter(phone_number=serializer.data["phone_number"]).exists()
        return Response(data={"exist": user_exist}, status=status.HTTP_200_OK)


class SendSMSForRegistrationView(APIView):
    """ will send sms for registration if user is not registered """

    def post(self, request):
        """
        take a phone number and will return success status for sending sms
        """
        serializer = UserPhoneNumberSerializer(data=request.POST)
        serializer.is_valid(raise_exception=True)
        user_ip = get_user_ip(request)
        phone_number = serializer.data["phone_number"]
        if BannedFromSignUp.is_banned(phone_number=phone_number, user_ip=user_ip):
            return Response(data={"success": False,
                                  "errors": ["user is restricted"]},
                            status=status.HTTP_403_FORBIDDEN)

        if CustomUser.objects.filter(phone_number=phone_number).exists():
            return Response(data={"success": False,
                                  "errors": ["user already registered"]},
                            status=status.HTTP_409_CONFLICT)
        sms_code = send_registration_code(phone_number=phone_number)
        PhoneNumberValidation.add_new_validation_code(phone_number=phone_number, user_ip=user_ip, sms_code=sms_code)
        return Response(data={"success": True, "errors": None}, status=status.HTTP_200_OK)


class RegistrationConfirmSMSView(APIView):
    """ will confirm sms sent to a number and generate a unique id/key for registration """

    def post(self, request):
        """ take number and code as argument and return a unique id if is valid """
        serializer = PhoneNumberValidationSerializer(data=request.POST)
        serializer.is_valid(raise_exception=True)
        phone_number = serializer.data["phone_number"]
        code = serializer.data["code"]
        user_ip = get_user_ip(request)
        if BannedFromSignUp.is_banned(phone_number=phone_number, user_ip=user_ip):
            return Response(data={"success": False,
                                  "errors": ["user is restricted"]},
                            status=status.HTTP_403_FORBIDDEN)
        validation = PhoneNumberValidation.objects.filter(phone_number=phone_number, last_sent_sms_code=code,
                                                          is_validated=False)
        if validation.exists():  # we normally should have considered using sms sent time too, but it was not requested
            validation = validation.get()
            register_id = validation.create_user_pre_register()
            UserSignUpTry.add_try(phone_number=phone_number, user_ip=user_ip, is_success=True)
            return Response({"success": True, "errors": None, "registerId": register_id})

        UserSignUpTry.add_try(phone_number=phone_number, user_ip=user_ip)
        return Response(data={"success": False, "errors": ["combination is wrong!"], "registerId": None})


class UserRegisterView(CreateAPIView):
    """ will register a user with a registration_id as a key """
    model = CustomUser
    serializer_class = UserRegisterSerializer


class SignInView(TokenObtainPairView):
    """ will take user credentials and return a JWT token, it also has a limiter to stop abusers """

    def post(self, request, *args, **kwargs):
        """ inherit from parent class and also add a limiter """
        serializer = UserSignInSerializer(data=request.POST)
        serializer.is_valid(raise_exception=True)
        user_ip = get_user_ip(request)
        phone_number = serializer.data["phone_number"]
        if BannedFromSignIn.is_banned(phone_number=phone_number, user_ip=user_ip):
            return Response(status=status.HTTP_429_TOO_MANY_REQUESTS)
        try:
            response = super().post(request, *args, **kwargs)
        except Exception as e:
            UserSignInTry.add_try(phone_number=phone_number, user_ip=user_ip)
            raise e
        return response

