from django.utils.translation import gettext_lazy as _
from datetime import timedelta
from django.forms.models import model_to_dict
from django.utils import timezone
from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from users.models import User, UserVerification
from .utils import send_otp_sms
import re


class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)
        # Add custom claims
        token['name'] = user.get_full_name()
        token['email'] = user.email
        token['phone'] = user.phone
        token['is_driver'] = hasattr(user, 'driver')
        if hasattr(user, 'driver'):
            token['driver_status'] = user.driver.status
        return token

class UserLoginSerializer(serializers.Serializer):
    phone_number = serializers.CharField(max_length=15, trim_whitespace=True) 
    password = serializers.CharField(
        style={'input_type': 'password'},
        trim_whitespace=False,
        write_only=True
    )
<<<<<<< HEAD
    fcm_token = serializers.CharField(max_length=255, required=False, allow_blank=True)
=======
>>>>>>> refs/remotes/origin/main

    def validate(self, data):
        phone_number = data.get('phone_number')
        password = data.get('password')
<<<<<<< HEAD
        fcm_token = data.get('fcm_token')
=======
>>>>>>> refs/remotes/origin/main

        if not phone_number or not password:
            raise serializers.ValidationError(
                _('Must include "phone_number" and "password".'),
                code='authorization'
            )

        # Find user by phone number
        try:
            user = User.objects.get(phone_number=phone_number)
        except User.DoesNotExist:
            raise serializers.ValidationError(
                _('Unable to log in with provided credentials.'),
                code='authorization'
            )

        # Check password
        if not user.check_password(password):
            raise serializers.ValidationError(
                _('Unable to log in with provided credentials.'),
                code='authorization'
            )
<<<<<<< HEAD
        if fcm_token:
            user.fcm_token = fcm_token
            user.save(update_fields=['fcm_token'])
=======
>>>>>>> refs/remotes/origin/main

        # Optional: Check if user is active
        if not user.is_active:
            raise serializers.ValidationError(
                _('User account is disabled.'),
                code='authorization'
            )

<<<<<<< HEAD
        # Update FCM token if provided
        if data.get('fcm_token'):
            user.fcm_token = data['fcm_token']
            user.save(update_fields=['fcm_token'])

=======
>>>>>>> refs/remotes/origin/main
        # Add the validated user object to the dictionary
        data['user'] = user
        return data


GHANA_PHONE_REGEX = r'^0[2-5]\d{8}$'

class PhoneSerializer(serializers.Serializer):
    """Serializer expecting a phone number."""
    phone_number = serializers.CharField(max_length=15, required=True)

    def validate_phone_number(self, value):
        """
        Validate the phone number format.
        """
        if not re.match(GHANA_PHONE_REGEX, value):
            raise serializers.ValidationError(
                "Enter a valid Ghanaian phone number starting with 0 and 10 digits (e.g., 024xxxxxxx)."
            )
        return value


class OTPVerifySerializer(serializers.Serializer):
    """Serializer expecting phone number and OTP code."""
    phone_number = serializers.CharField(max_length=15, required=True)
    otp_code = serializers.CharField(max_length=6, required=True) # Assuming 6 digit OTP

    def validate_phone_number(self, value):
        """
        Validate the phone number format.
        """
        if not re.match(GHANA_PHONE_REGEX, value):
            raise serializers.ValidationError(
                "Enter a valid Ghanaian phone number starting with 0 and 10 digits (e.g., 024xxxxxxx)."
            )
        return value

    def validate_otp_code(self, value):
        """
        Validate OTP code format (e.g., ensure it's numeric and correct length).
        """
        if not value.isdigit() or len(value) != 6:
            raise serializers.ValidationError("OTP code must be 6 digits.")
        return value

class OTPVerificationSerializer(PhoneSerializer):
    # Define the desired field names used in your validation logic.
    otp = serializers.CharField(max_length=6, min_length=6)
    phone_number = serializers.CharField()

    def to_internal_value(self, data):
        # Remap "code" to "otp" and "number" to "phone_number"
        if 'code' in data:
            data['otp'] = data.pop('code')
        if 'number' in data:
            data['phone_number'] = data.pop('number')
        # Now call the parent's method to further process data.
        return super().to_internal_value(data)

    def validate(self, data):
        # Now data has keys "otp" and "phone_number" for validation.
        otp_code = data.get('otp')
        phone_number = data.get('phone_number')
        user = self.context.get('user')
        if not user:
            raise serializers.ValidationError("User not found.")

        try:
            verification = UserVerification.objects.get(user=user)
            verification_data = model_to_dict(verification)
            print(f"Verification record found: {verification_data}")  # Debugging line
            # expiry_time = verification.phone_verification_sent_at + timedelta(minutes=10)
            # print(f"OTP expiry time: {expiry_time}")  # Debugging line
            # if verification.phone_verification_code != otp_code:
            #     raise serializers.ValidationError("Invalid OTP code.")
            # if timezone.now() > expiry_time:
            #     raise serializers.ValidationError("OTP code has expired.")

            self.context['verification'] = verification_data
        except UserVerification.DoesNotExist:
            raise serializers.ValidationError("Verification record not found. Please request a new OTP.")
        except TypeError:  
            raise serializers.ValidationError("OTP verification unavailable. Please request an OTP.")

        return data

class PasswordResetRequestSerializer(PhoneSerializer):
    def save(self, **kwargs):
        user = self.context['user']
        try:
             verification, created = UserVerification.objects.get_or_create(user=user)
             # Send OTP (function handles saving the code and timestamp)
             success = send_otp_sms(verification)
             if not success:
                 raise serializers.ValidationError("Failed to send OTP. Please try again later.")
        except Exception as e:
             print(f"Error in PasswordResetRequestSerializer save: {e}")
             raise serializers.ValidationError("An error occurred while processing your request.")


class PasswordResetConfirmSerializer(OTPVerificationSerializer):
    new_password = serializers.CharField(write_only=True, min_length=8, style={'input_type': 'password'})
    # Add confirm_password if needed
    # confirm_password = serializers.CharField(write_only=True, style={'input_type': 'password'})

    def validate(self, data):
        # First validate phone and OTP using parent class
        data = super().validate(data)
        # Add password confirmation validation if using confirm_password field
        # if data['new_password'] != data['confirm_password']:
        #     raise serializers.ValidationError({"new_password": "Passwords do not match."})
        # Add more password validation rules if needed (e.g., complexity)
        return data

    def save(self, **kwargs):
        user = self.context['user']
        verification = self.context['verification']
        new_password = self.validated_data['new_password']

        user.set_password(new_password)
        user.save(update_fields=['password'])

        # Clear OTP code after successful use
        verification.phone_verification_code = None
        verification.save(update_fields=['phone_verification_code'])
