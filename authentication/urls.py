# authentication/urls.py

from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView

from .views import (
    CustomTokenObtainPairView,
    UserLoginView,
    LogoutView,
    PasswordResetRequestView,
    PasswordResetConfirmView,
    OTPRequestView,
    OTPVerifyView,
    UserTokenRefreshView
)

app_name = 'authentication'

urlpatterns = [
    # JWT Token endpoints
    path('token/obtain/', CustomTokenObtainPairView.as_view(), name='token_obtain_pair'), # Username/password
    path('token/refresh/', UserTokenRefreshView.as_view(), name='token_refresh'), # Use simplejwt view

    # Custom Authentication endpoints
    path('login/', UserLoginView.as_view(), name='phone_login'),
    path('logout/', LogoutView.as_view(), name='logout'),

    # Password Reset endpoints
    path('password/reset/request/', PasswordResetRequestView.as_view(), name='password_reset_request'),
    path('password/reset/confirm/', PasswordResetConfirmView.as_view(), name='password_reset_confirm'),

    # OTP Verification endpoints (for logged-in user phone verification)
    path('otp/request/', OTPRequestView.as_view(), name='otp_request'),
    path('otp/verify/', OTPVerifyView.as_view(), name='otp_verify'),

    # Note: Signup/Registration is handled under /api/users/ via UserViewSet
]