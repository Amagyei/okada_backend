# authentication/views.py
from django.shortcuts import render
from rest_framework import status, views, generics
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from rest_framework_simplejwt.tokens import RefreshToken, TokenError
from django.utils import timezone 
from django.contrib.auth import get_user_model
from .serializers import (
    CustomTokenObtainPairSerializer,
    UserLoginSerializer,
    PasswordResetRequestSerializer,
    PasswordResetConfirmSerializer,
    OTPVerificationSerializer,
    PhoneSerializer
)
from datetime import datetime
from datetime import timedelta
from django.core.cache import cache
from django.utils.translation import gettext_lazy as _
from django.conf import settings
from django.core.exceptions import ValidationError
from .utils import send_otp_sms 
from .models import TokenBlacklist
from users.serializers import UserSerializer
from users.models import UserVerification 


User = get_user_model()

class CustomTokenObtainPairView(TokenObtainPairView):
    """_summary_

    Args:
        TokenObtainPairView (_type_): _description_
        takes username and password and returns access and refresh tokens
    """
    serializer_class = CustomTokenObtainPairSerializer


class UserLoginView(views.APIView):

    """ takes phone_number and password and returns access and refresh tokens"""
    permission_classes = (AllowAny,)
    serializer_class = UserLoginSerializer
    
    def post(self, request, *args, **kwargs):
        print(f"User requesting login: {request.user}")
        print(f"Request data: {request.data}")
        try:
            # Validate request data
            serializer = self.serializer_class(data=request.data)
            if not serializer.is_valid():
                print(f"Serializer errors: {serializer.errors}")
                return Response({
                    'error': 'Invalid login credentials',
                    'details': serializer.errors
                }, status=status.HTTP_400_BAD_REQUEST)

            # Get user from validated data
            try:
                user = serializer.validated_data['user']
            except KeyError:
                print(f"User validation failed")
                return Response({
                    'error': 'User validation failed',
                    'details': 'Could not authenticate user with provided credentials'
                }, status=status.HTTP_401_UNAUTHORIZED)

            # -------------------------------------------------------------
            # OPTIONAL USER TYPE VALIDATION
            # -------------------------------------------------------------
            # The mobile apps can send either a body field `user_type` OR a
            # header  `X-USER-TYPE` (case-insensitive). If provided, we
            # validate it against the actual `user.user_type`. This prevents
            # riders from logging in on the driver app and vice-versa. If the
            # client does not provide the hint we assume no restriction (to
            # maintain backwards compatibility).

            # 1) Check JSON body
            requested_user_type = request.data.get('user_type')

            # 2) Fallback to custom header (e.g. X-USER-TYPE: driver)
            if not requested_user_type:
                requested_user_type = request.headers.get('X-USER-TYPE')

            if requested_user_type and requested_user_type.lower() != user.user_type.lower():
                return Response(
                    {
                        'error': 'User type mismatch',
                        'details': f"This account is of type '{user.user_type}', but '{requested_user_type}' access was requested."
                    },
                    status=status.HTTP_403_FORBIDDEN
                )

            # -------------------------------------------------------------
            # Generate tokens
            try:
                refresh = RefreshToken.for_user(user)
            except Exception as e:
                return Response({
                    'error': 'Token generation failed',
                    'details': str(e)
                }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

            # Prepare response data
            try:
                response_data = {
                    'refresh': str(refresh),
                    'access': str(refresh.access_token),
                    'user': {
                        'id': user.id,
                        'username': user.username,
                        'email': user.email,
                        'phone_number': user.phone_number,
                        'first_name': user.first_name,
                        'last_name': user.last_name,
                        'user_type': user.user_type,
                    }
                }
                return Response(response_data, status=status.HTTP_200_OK)
            except AttributeError as e:
                return Response({
                    'error': 'User data error',
                    'details': f'Missing required user attribute: {str(e)}'
                }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        except Exception as e:
            return Response({
                'error': 'Login failed',
                'details': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

OTP_RATE_LIMIT_DURATION = getattr(settings, 'OTP_RATE_LIMIT_DURATION', 60)

class OTPRequestView(generics.GenericAPIView):
    """Requests an OTP to be sent to the user's phone for verification."""
    permission_classes = [AllowAny] 
    serializer_class = PhoneSerializer 

    def post(self, request, *args, **kwargs):
        # print the user requesting
        print(f"User requesting OTP: {request.user}")
        serializer = self.get_serializer(data=request.data)

        serializer.is_valid(raise_exception=True)
        phone_number = serializer.validated_data['phone_number']
        cache_key = f"otp_rate_limit_{phone_number}"
        if cache.get(cache_key):
            return Response({"detail": "OTP request limit exceeded. Please try again later."}, status=status.HTTP_429_TOO_MANY_REQUESTS)
        print(f"Sending OTP to {phone_number}")
        success = send_otp_sms(phone_number)
        print(f"OTP sent: {success}")
        if success:
            cache.set(cache_key, True, timeout=OTP_RATE_LIMIT_DURATION)
            return Response({"message": "OTP sent successfully."}, status=status.HTTP_200_OK)
        return Response({"detail": "Failed to send OTP. Please try again later."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class OTPVerifyView(generics.GenericAPIView):
    """Verifies the OTP code sent to the user's phone."""
    permission_classes = [IsAuthenticated] # Require user to be logged in
    serializer_class = OTPVerificationSerializer

    def get_serializer_context(self):
        # Pass user to serializer context, disable user existence check
        context = super().get_serializer_context()
        context['user'] = self.request.user
        context['check_user_exists'] = False 
        return context

    def post(self, request, *args, **kwargs):
        print(request.data) # debugging
        serializer = self.get_serializer(data=request.data)
        print("initial data ", serializer.initial_data) 
        serializer.is_valid(raise_exception=True)
        print("validated data ")
        print(serializer.validated_data) 

        # Serializer validation already checked OTP validity
        verification = serializer.context['verification']
        user = request.user

        # Mark phone as verified
        user.is_phone_verified = True
        user.save(update_fields=['is_phone_verified'])
        verification.phone_verified_at = timezone.now()
        verification.phone_verification_code = None 
        verification.save(update_fields=['phone_verified_at', 'phone_verification_code'])

        return Response({"message": "Phone number verified successfully."}, status=status.HTTP_200_OK)


class PasswordResetRequestView(generics.GenericAPIView):
    """Initiates password reset by sending OTP to the user's phone."""
    permission_classes = (AllowAny,)
    serializer_class = PasswordResetRequestSerializer

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        # Serializer's save method handles OTP sending via signal/utility
        serializer.save()
        return Response({"message": "If an account exists, an OTP has been sent."}, status=status.HTTP_200_OK)


class PasswordResetConfirmView(generics.GenericAPIView):
    """Confirms password reset using phone, OTP, and new password."""
    permission_classes = (AllowAny,)
    serializer_class = PasswordResetConfirmSerializer

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        # Serializer's save method handles password update & clearing OTP
        serializer.save()
        return Response({"message": "Password has been reset successfully."}, status=status.HTTP_200_OK)


class LogoutView(generics.GenericAPIView):
    """Blacklists the provided refresh token."""
    permission_classes = (IsAuthenticated,) # User must be logged in to log out

    def post(self, request, *args, **kwargs):
        try:
            refresh_token = request.data["refresh"]
            if not isinstance(refresh_token, str):
                 raise TypeError
            token = RefreshToken(refresh_token)
            token.blacklist()
            return Response(status=status.HTTP_205_RESET_CONTENT)
        except (TokenError, KeyError, TypeError, Exception) as e:
            print(f"Logout Error: {e}") # Log the error
            # Avoid revealing specific token errors
            return Response({"detail": "Invalid token or request."}, status=status.HTTP_400_BAD_REQUEST)
