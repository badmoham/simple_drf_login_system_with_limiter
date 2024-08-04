from django.urls import path

from rest_framework_simplejwt.views import TokenRefreshView

from users.views import (UserExistView, SignInView, SendSMSForRegistrationView,
                         RegistrationConfirmSMSView, UserRegisterView)

urlpatterns = [
    path('token/signin/', SignInView.as_view(), name='token_sign_in'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),

    path('signin/userexists/', UserExistView.as_view(), name='user_exists'),
    path('signup/send_registration_sms/', SendSMSForRegistrationView.as_view(), name='send_registration_sms'),
    path('signup/confirm_registration_sms/', RegistrationConfirmSMSView.as_view(), name='confirm_registration_sms'),
    path('signup/finish_registration/', UserRegisterView.as_view(), name='finish_registration'),
]

