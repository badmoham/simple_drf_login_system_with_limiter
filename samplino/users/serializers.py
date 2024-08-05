from rest_framework import serializers

from users.models import CustomUser, UserPreRegister

from samplino.settings import REGISTRATION_SMS_CODE_LENGTH
__all__ = ["UserPhoneNumberSerializer", "PhoneNumberValidationSerializer",
           "UserRegisterSerializer", "UserSignInSerializer"]


class UserPhoneNumberSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomUser
        fields = ['phone_number']


class PhoneNumberValidationSerializer(serializers.ModelSerializer):
    code = serializers.CharField(max_length=REGISTRATION_SMS_CODE_LENGTH, min_length=REGISTRATION_SMS_CODE_LENGTH)

    class Meta:
        model = CustomUser
        fields = ['phone_number', 'code']


class UserSignInSerializer(serializers.Serializer):
    phone_number = serializers.CharField(max_length=16)
    password = serializers.CharField(max_length=128)


class UserRegisterSerializer(serializers.ModelSerializer):
    registration_id = serializers.CharField(required=True, write_only=True)

    class Meta:
        model = CustomUser
        fields = ('username', 'password', 'email', 'first_name', 'last_name', 'registration_id')
        write_only_fields = ('password',)

    def create(self, validated_data):
        user = CustomUser.objects.create(
            phone_number=validated_data['phone_number'],
            username=validated_data['username'],
            email=validated_data['email'],
            first_name=validated_data['first_name'],
            last_name=validated_data['last_name']
        )
        user.set_password(validated_data['password'])
        user.save()

        return user

    def validate(self, data):
        """ will validate the registration id and add phon_number """
        registration_id = data["registration_id"]
        pre_register = UserPreRegister.objects.filter(unique_registration_id=registration_id, is_registered=False)
        if pre_register.exists() is False:
            raise serializers.ValidationError({"registration_id": "is not a valid value"})
        pre_register = pre_register.get()
        pre_register.is_registered = True
        pre_register.save()
        data["phone_number"] = pre_register.phone_number
        return data

