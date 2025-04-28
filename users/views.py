from rest_framework import viewsets, status, generics
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import get_user_model
from django.utils import timezone
import random
import string
from .models import UserVerification, DriverDocument
from .serializers import (
    UserSerializer, UserRegistrationSerializer, DriverProfileSerializer,
    RiderProfileSerializer, DriverDocumentSerializer, UserVerificationSerializer,
    ChangePasswordSerializer, UpdateProfileSerializer
)

from authentication.utils import send_otp_sms 


User = get_user_model()

class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    # serializer_class = UserSerializer # Default serializer
    permission_classes = [IsAuthenticated]

    def get_serializer_class(self):
        if self.action == 'create':
            # Use the registration serializer from this app
            return UserRegistrationSerializer
        elif self.action in ['update', 'partial_update']:
             # Use a different serializer for profile updates if needed
            return UpdateProfileSerializer # Make sure UpdateProfileSerializer is defined/imported
        # Default serializer for list, retrieve etc.
        return UserSerializer

    def get_permissions(self):
        # Allow anyone to create a user (signup)
        if self.action == 'create':
            return [AllowAny()]
        # Require authentication for other actions
        return super().get_permissions()

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save() 
        # Create verification record after user is saved
        try:
            verification = UserVerification.objects.create(user=user)
            # Send OTP immediately after registration
            send_otp_sms(verification) # Call the utility function

        except Exception as e:
            print(f"Error creating verification/sending OTP for {user.username}: {e}")

        # Generate tokens for the new user
        refresh = RefreshToken.for_user(user)
        headers = self.get_success_headers(serializer.data)

        # Return user data (using the default UserSerializer) and tokens
        response_data = {
            # Use the UserSerializer for the response, not UserRegistrationSerializer
            'user': UserSerializer(user, context={'request': request}).data,
            'refresh': str(refresh),
            'access': str(refresh.access_token),
        }
        return Response(response_data, status=status.HTTP_201_CREATED, headers=headers)

class UserProfileView(generics.RetrieveUpdateAPIView): # Allows GET (retrieve) and PATCH/PUT (update)
    """
    API view for retrieving and updating the authenticated user's profile.
    Uses '/api/users/me/' URL.
    """
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated]

    def get_object(self):
        # Returns the user associated with the current request token
        print(self.request.user)
        return self.request.user

    # Optional: If you want profile updates via PATCH/PUT on /users/me/
    # def perform_update(self, serializer):
    #     serializer.save(user=self.request.user) # Ensure user isn't changed

class DriverProfileViewSet(viewsets.ModelViewSet):
    serializer_class = DriverProfileSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return User.objects.filter(user_type='driver')

    def get_object(self):
        return self.request.user

class RiderProfileViewSet(viewsets.ModelViewSet):
    serializer_class = RiderProfileSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return User.objects.filter(user_type='rider')

    def get_object(self):
        return self.request.user

class DriverDocumentViewSet(viewsets.ModelViewSet):
    serializer_class = DriverDocumentSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return DriverDocument.objects.filter(driver=self.request.user)

    def perform_create(self, serializer):
        serializer.save(driver=self.request.user)

class UserVerificationViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = UserVerificationSerializer
    permission_classes = [IsAuthenticated]

    def get_object(self):
        return UserVerification.objects.get(user=self.request.user)