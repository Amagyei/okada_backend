<<<<<<< HEAD
# users/views.py
=======
>>>>>>> refs/remotes/origin/main
from rest_framework import viewsets, status, generics
from rest_framework.views import APIView
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
            print(f"Verification record created: {verification.phone_number}")
            send_otp_sms(user.phone_number) # Call the utility function

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


class ChangePasswordView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = ChangePasswordSerializer(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)

        user = request.user
        user.set_password(serializer.validated_data['new_password'])
        user.save()
        return Response({"detail": "Password updated successfully."}, status=status.HTTP_200_OK)
    


class UserProfileView(generics.RetrieveUpdateAPIView):
    """
    Allows authenticated users to retrieve and partially update their profile.
    Ghana Card details can only be set once and become immutable.
<<<<<<< HEAD
    Also accepts fcm_token for push notifications.

=======
>>>>>>> refs/remotes/origin/main
    """
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated]

    def get_object(self):
        return self.request.user

    def patch(self, request, *args, **kwargs):
        user = self.get_object()
        data = request.data.copy()

        # Enforce immutability for Ghana Card fields
        if user.ghana_card_number and data.get("ghana_card_number"):
            if data["ghana_card_number"] != user.ghana_card_number:
                return Response(
                    {"ghana_card_number": ["Ghana Card number cannot be changed once set."]},
                    status=status.HTTP_400_BAD_REQUEST
                )
<<<<<<< HEAD
        

=======
>>>>>>> refs/remotes/origin/main

        if user.ghana_card_image and data.get("ghana_card_image"):
            return Response(
                {"ghana_card_image": ["Ghana Card image cannot be changed once uploaded."]},
                status=status.HTTP_400_BAD_REQUEST
            )
<<<<<<< HEAD
        
        # Handle fcm_token
        if data.get("fcm_token"):
            user.fcm_token = data["fcm_token"]
            user.save()
        
        
=======
>>>>>>> refs/remotes/origin/main

        serializer = self.get_serializer(user, data=data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)


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