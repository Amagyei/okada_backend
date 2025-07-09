# rides/permissions.py

from rest_framework import permissions
from .models import Ride # Import the Ride model to check relationships

class IsAssignedDriverOrReadOnly(permissions.BasePermission):
    """
    Allows SAFE_METHODS (GET, HEAD, OPTIONS) for any authenticated user.
    Allows unsafe methods (POST, PUT, PATCH, DELETE) only for the driver assigned to the ride.
    """
    message = "You do not have permission to modify this ride."

    def has_object_permission(self, request, view, obj):
        # 'obj' here is expected to be an instance of the Ride model.
        # Read permissions are allowed for any request,
        # so we'll always allow GET, HEAD or OPTIONS requests.
        if request.method in permissions.SAFE_METHODS:
            # Allow read access if the user is the rider or the driver (optional check)
            # return request.user == obj.rider or request.user == obj.driver
            # Or simply allow any authenticated user to view ride details:
            return request.user.is_authenticated

        # Write permissions are only allowed to the driver of the ride.
        # Ensure the ride has a driver assigned and it matches the request user.
        return obj.driver is not None and obj.driver == request.user


class IsRideOwnerOrDriver(permissions.BasePermission):
    """
    Allows access only to the rider who created the ride or the driver assigned to it.
    Useful for actions like cancelling or viewing specific details.
    """
    message = "You do not have permission to access or modify this ride."

    def has_object_permission(self, request, view, obj):
        # 'obj' here is expected to be an instance of the Ride model.
        # Check if the request user is either the rider or the assigned driver.
        return request.user == obj.rider or (obj.driver is not None and request.user == obj.driver)

# You can add more ride-specific permissions, e.g.,
# class CanCancelRide(permissions.BasePermission):
#     """Checks if the user can cancel based on status and role."""
#     def has_object_permission(self, request, view, obj):
#         user = request.user
#         is_participant = (user == obj.rider or user == obj.driver)
#         cancellable_statuses = [
#             Ride.StatusChoices.REQUESTED,
#             Ride.StatusChoices.ACCEPTED,
#             Ride.StatusChoices.ON_ROUTE_TO_PICKUP,
#         ]
#         return is_participant and obj.status in cancellable_statuses

