# users/urls.py

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import UserViewSet, UserProfileView
from .views import (
    DriverProfileViewSet, RiderProfileViewSet, DriverDocumentViewSet, UserVerificationViewSet
)

# Create a router instance
router = DefaultRouter()

# --- Register ONLY ViewSets here ---
router.register(r'', UserViewSet, basename='user')
router.register(r'driver-profiles', DriverProfileViewSet, basename='driver-profiles')
router.register(r'rider-profiles', RiderProfileViewSet, basename='rider-profiles')
router.register(r'driver-documents', DriverDocumentViewSet, basename='driver-documents')
router.register(r'verifications', UserVerificationViewSet, basename='verifications')

app_name = 'users'

urlpatterns = [
    # --- Define explicit paths for non-ViewSet views FIRST ---
    # Maps GET/PUT/PATCH requests for '/api/users/me/' to UserProfileView
    path('me/', UserProfileView.as_view(), name='user-profile'),

    # --- Include the router-generated URLs for ViewSets AFTER specific paths ---
    path('', include(router.urls)),
]