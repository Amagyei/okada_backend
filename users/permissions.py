# users/permissions.py

from rest_framework import permissions

class IsRider(permissions.BasePermission):
    """
    Allows access only to authenticated users with user_type 'rider'.
    """
    message = "Only riders are allowed to perform this action." # Optional custom message

    def has_permission(self, request, view):
        # Check if the user is authenticated and if their user_type is 'rider'
        return request.user.is_authenticated and request.user.user_type == 'rider'


class IsDriver(permissions.BasePermission):
    """
    Allows access only to authenticated users with user_type 'driver'.
    """
    message = "Only drivers are allowed to perform this action." # Optional custom message

    def has_permission(self, request, view):
        # Check if the user is authenticated and if their user_type is 'driver'
        return request.user.is_authenticated and request.user.user_type == 'driver'

