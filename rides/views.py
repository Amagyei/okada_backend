# rides/views.py

from decimal import Decimal # Import Decimal for fares
from django.db import transaction # Import transaction for atomic operations
from django.db.models import Q # Import Q objects for complex queries
from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework import viewsets, status, mixins, permissions
from rest_framework.decorators import action
from rest_framework.response import Response

# Import models from the current app
from .models import Ride, RideRating, SavedLocation
# Import serializers from the current app
from .serializers import (
    RideSerializer, RideDetailSerializer, RideCreateSerializer,
    RideCancelSerializer, RideCompleteSerializer,
    RideRatingSerializer, SavedLocationSerializer, RideEstimateFareSerializer
)

from .utils import get_estimated_fare # Import utility function for fare estimation


# Import permission classes (replace placeholders with actual imports if created)
# from .permissions import IsRideOwnerOrDriver, IsAssignedDriverOrReadOnly
from users.permissions import IsRider, IsDriver


# Placeholder Permissions (Remove or replace with actual imports from permissions.py)
# It's better to define these in users/permissions.py and rides/permissions.py
# and import them here. Keeping them here temporarily for completeness if not created yet.
class IsOwner(permissions.BasePermission):
    """Placeholder: Allow only owner of object."""
    def has_object_permission(self, request, view, obj):
        # Example: return obj.user == request.user
        return True # Replace with actual logic

# Remove these if importing from users.permissions
# class IsRiderUser(permissions.BasePermission):
#     """Placeholder: Allow only users with user_type='rider'."""
#     def has_permission(self, request, view):
#         return request.user.is_authenticated and request.user.user_type == 'rider'

# class IsDriverUser(permissions.BasePermission):
#     """Placeholder: Allow only users with user_type='driver'."""
#     def has_permission(self, request, view):
#         return request.user.is_authenticated and request.user.user_type == 'driver'

class IsAssignedDriverOrReadOnly(permissions.BasePermission):
    """Placeholder: Allow assigned driver to modify, others read-only."""
    message = "You do not have permission to modify this ride."
    def has_object_permission(self, request, view, obj):
        # Allow GET, HEAD, OPTIONS requests for any authenticated user
        if request.method in permissions.SAFE_METHODS:
            return request.user.is_authenticated
        # Allow write actions only if a driver is assigned and it's the current user
        return obj.driver is not None and obj.driver == request.user

class IsRideOwnerOrDriver(permissions.BasePermission):
    """Placeholder: Allow access only to the rider or assigned driver."""
    message = "You do not have permission to access or modify this ride."
    def has_object_permission(self, request, view, obj):
        # Check if the user is the rider OR the assigned driver
        is_rider = request.user == obj.rider
        is_assigned_driver = (obj.driver is not None and request.user == obj.driver)
        return is_rider or is_assigned_driver
# --- End Placeholders ---


# --- Ride ViewSet ---
class RideViewSet(mixins.CreateModelMixin, # For POST /api/rides/
                  viewsets.ReadOnlyModelViewSet): # For GET /api/rides/, GET /api/rides/{pk}/
    """
    ViewSet for viewing and managing Rides.
    - Riders can create and view their rides.
    - Drivers can view assigned rides and available requests.
    - Specific actions handle ride lifecycle updates.
    """
    serializer_class = RideSerializer # Default for list view
    permission_classes = [permissions.IsAuthenticated] # Base permission for all actions

    def get_queryset(self):
        """
        Filter rides based on user type.
        - Riders see their requested/ongoing rides.
        - Drivers see rides assigned to them AND available rides (requested, unassigned).
        """
        user = self.request.user
        if not user.is_authenticated:
            return Ride.objects.none()

        if user.user_type == 'driver':
            # Combine rides assigned to this driver OR rides that are available
            assigned_rides = Q(driver=user)
            available_rides = Q(status=Ride.StatusChoices.REQUESTED, driver__isnull=True)

            # TODO: Refine 'available_rides' with GeoDjango spatial query
            # Requires driver's current location (PointField) and ride pickup_location (PointField)
            # Example (requires GeoDjango setup):
            # from django.contrib.gis.db.models.functions import Distance
            # from django.contrib.gis.measure import D # Distance unit object
            # driver_location = user.current_location # Assuming user model has PointField
            # if driver_location:
            #     radius_km = 5 # Example search radius
            #     available_rides = available_rides & Q(pickup_location__dwithin=(driver_location, D(km=radius_km)))
            # else:
            #     available_rides = Q(pk__in=[]) # No available rides if driver location unknown

            queryset = Ride.objects.filter(assigned_rides | available_rides)

        elif user.user_type == 'rider':
            # Show rides requested by the rider
            queryset = Ride.objects.filter(rider=user)
        else:
             queryset = Ride.objects.none()

        # Optimize database query by fetching related user objects
        return queryset.select_related('rider', 'driver').distinct()

    def get_serializer_class(self):
        """Return appropriate serializer based on action."""
        action_serializers = {
            'estimate_fare': RideEstimateFareSerializer,
            'retrieve': RideDetailSerializer,
            'create': RideCreateSerializer,
            'cancel_ride': RideCancelSerializer,
            'rate_ride': RideRatingSerializer,
            'complete_trip': RideCompleteSerializer,

        }
        # Return specific serializer for the action, or default (RideSerializer for list)
        return action_serializers.get(self.action, super().get_serializer_class())

    # --- Rider Actions ---

    # Overrides CreateModelMixin's create method for ride requests
    # permission_classes defined at ViewSet level or action level can handle IsRiderUser check
    def create(self, request, *args, **kwargs):
        """
        Creates a new ride request for the authenticated Rider.
        Expects pickup/destination coordinates and optional addresses.
        """
        # Explicit permission check (alternative to action-level permission)
        if not request.user.user_type == 'rider':
             return Response({"detail": "Only riders can create ride requests."}, status=status.HTTP_403_FORBIDDEN)

        serializer = self.get_serializer(data=request.data) # Gets RideCreateSerializer
        serializer.is_valid(raise_exception=True)

       

        # Save the ride request, associating rider and setting status/fare
        ride = serializer.save(
            rider=request.user,
            status=Ride.StatusChoices.REQUESTED,
            
        )

        # Return detailed data for the newly created ride
        response_serializer = RideDetailSerializer(ride, context={'request': request})
        headers = self.get_success_headers(response_serializer.data)
        return Response(response_serializer.data, status=status.HTTP_201_CREATED, headers=headers)
    
    @action(detail=False, methods=['post'], permission_classes=[permissions.IsAuthenticated]) # Any authenticated user can estimate
    def estimate_fare(self, request, *args, **kwargs):
        """
        Calculates and returns an estimated fare based on pickup and destination coordinates.
        Expects: {'pickup_location_lat': ..., 'pickup_location_lng': ..., 'destination_lat': ..., 'destination_lng': ...}
        Returns: {'estimated_fare': ...}
        """
        serializer = self.get_serializer(data=request.data) # Gets RideEstimateFareSerializer
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        try:
            # Call the utility function from rides/utils.py
            estimated_fare = get_estimated_fare(
                pickup_lat=data['pickup_location_lat'],
                pickup_lng=data['pickup_location_lng'],
                dest_lat=data['destination_lat'],
                dest_lng=data['destination_lng']
            )
            if estimated_fare is None:
                # Handle cases where calculation might fail internally in the util
                return Response({"detail": "Could not calculate fare at this time."}, status=status.HTTP_400_BAD_REQUEST)

            # Return just the fare value
            return Response({"estimated_fare": estimated_fare}, status=status.HTTP_200_OK)

        except Exception as e:
            # Catch unexpected errors during calculation
            print(f"Error in estimate_fare view: {e}")
            return Response({"detail": "An error occurred during fare estimation."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    # --- End New Action ---

    @action(detail=True, methods=['post'], permission_classes=[permissions.IsAuthenticated, IsRideOwnerOrDriver])
    def cancel_ride(self, request, pk=None):
        """
        Action for a Rider or assigned Driver to cancel a ride.
        Requires 'cancellation_reason' in request data.
        """
        ride = self.get_object() # Checks object permissions via IsRideOwnerOrDriver
        user = request.user

        # State Check: Ensure ride is in a cancellable state
        cancellable_statuses = [
            Ride.StatusChoices.REQUESTED, Ride.StatusChoices.ACCEPTED,
            Ride.StatusChoices.ON_ROUTE_TO_PICKUP, Ride.StatusChoices.ARRIVED_AT_PICKUP,
        ]
        if ride.status not in cancellable_statuses:
            return Response({"detail": f"Ride cannot be cancelled in its current state ('{ride.get_status_display()}')."}, status=status.HTTP_400_BAD_REQUEST)

        serializer = self.get_serializer(ride, data=request.data, partial=True) # Gets RideCancelSerializer
        serializer.is_valid(raise_exception=True)

        new_status = Ride.StatusChoices.CANCELLED_BY_RIDER if ride.rider == user else Ride.StatusChoices.CANCELLED_BY_DRIVER

        # TODO: Implement cancellation fee logic if applicable
        cancellation_fee = Decimal('0.00') # Placeholder

        # Save the changes (status, timestamp, reason, fee)
        # Serializer handles saving the cancellation_reason field
        serializer.save(
            status=new_status,
            cancelled_at=timezone.now(),
            cancellation_fee = cancellation_fee,
        )

        # Return updated ride details
        response_serializer = RideDetailSerializer(ride, context={'request': request})
        return Response(response_serializer.data, status=status.HTTP_200_OK)

    # --- Driver Actions ---

    @action(detail=True, methods=['post'], permission_classes=[permissions.IsAuthenticated, IsDriver])
    def accept_ride(self, request, pk=None):
        """Action for an authenticated Driver to accept a requested ride."""
        ride = get_object_or_404(Ride, pk=pk) # Get ride directly first
        driver = request.user

        # State Check
        if ride.status != Ride.StatusChoices.REQUESTED:
            return Response({"detail": "This ride is no longer available for acceptance."}, status=status.HTTP_400_BAD_REQUEST)
        # Ensure another driver hasn't accepted it simultaneously
        if ride.driver is not None:
             return Response({"detail": "This ride has already been accepted by another driver."}, status=status.HTTP_400_BAD_REQUEST)

        # Assign driver and update status atomically to prevent race conditions
        with transaction.atomic():
            # Re-fetch ride instance inside transaction with select_for_update to lock row
            ride_to_update = Ride.objects.select_for_update().get(pk=ride.pk)
            # Double-check status and driver inside transaction
            if ride_to_update.status != Ride.StatusChoices.REQUESTED or ride_to_update.driver is not None:
                 # Return 409 Conflict if state changed concurrently
                 return Response({"detail": "Ride status changed or was accepted while processing."}, status=status.HTTP_409_CONFLICT)

            ride_to_update.driver = driver
            ride_to_update.status = Ride.StatusChoices.ACCEPTED
            ride_to_update.accepted_at = timezone.now()
            ride_to_update.save(update_fields=['driver', 'status', 'accepted_at'])
            # Update the original ride instance for the response serializer
            ride = ride_to_update

        # TODO: Send notification to Rider that ride was accepted

        response_serializer = RideDetailSerializer(ride, context={'request': request})
        return Response(response_serializer.data, status=status.HTTP_200_OK)

    @action(detail=True, methods=['post'], permission_classes=[permissions.IsAuthenticated, IsAssignedDriverOrReadOnly])
    def update_ride_status(self, request, pk=None):
         """Generic action for assigned driver to update status to valid next steps."""
         ride = self.get_object() # Checks object permissions via IsAssignedDriverOrReadOnly

         new_status = request.data.get('status')
         if not new_status:
              return Response({"detail": "Status field is required."}, status=status.HTTP_400_BAD_REQUEST)
         # Validate if the provided status is a valid choice
         if new_status not in Ride.StatusChoices.values:
              return Response({"detail": f"Invalid status value '{new_status}' provided."}, status=status.HTTP_400_BAD_REQUEST)

         now = timezone.now()
         update_fields = ['status']
         valid_transition = False

         # Define valid transitions and associated actions/timestamps
         if new_status == Ride.StatusChoices.ON_ROUTE_TO_PICKUP and ride.status == Ride.StatusChoices.ACCEPTED:
              valid_transition = True; print("TODO: Notify Rider - Driver En Route")
         elif new_status == Ride.StatusChoices.ARRIVED_AT_PICKUP and ride.status == Ride.StatusChoices.ON_ROUTE_TO_PICKUP:
              ride.arrived_at_pickup_at = now; update_fields.append('arrived_at_pickup_at'); valid_transition = True; print("TODO: Notify Rider - Driver Arrived")
         elif new_status == Ride.StatusChoices.ON_TRIP and ride.status == Ride.StatusChoices.ARRIVED_AT_PICKUP:
              ride.trip_started_at = now; update_fields.append('trip_started_at'); valid_transition = True; print("TODO: Notify Rider - Trip Started")

         if not valid_transition:
             if new_status == ride.status: return Response({"detail": f"Ride is already in '{ride.get_status_display()}' state."}, status=status.HTTP_400_BAD_REQUEST)
             return Response({"detail": f"Invalid status transition from '{ride.get_status_display()}' to '{new_status}'."}, status=status.HTTP_400_BAD_REQUEST)

         # Update status and relevant timestamp fields
         ride.status = new_status
         ride.save(update_fields=update_fields)

         response_serializer = RideDetailSerializer(ride, context={'request': request})
         return Response(response_serializer.data, status=status.HTTP_200_OK)


    @action(detail=True, methods=['post'], permission_classes=[permissions.IsAuthenticated, IsAssignedDriverOrReadOnly])
    def complete_trip(self, request, pk=None):
        """Action for the assigned driver to mark the trip as completed."""
        ride = self.get_object() # Checks object permissions

        # State Check
        if ride.status != Ride.StatusChoices.ON_TRIP:
            return Response({"detail": f"Ride cannot be completed from state '{ride.get_status_display()}'."}, status=status.HTTP_400_BAD_REQUEST)

        # Use RideCompleteSerializer if driver provides final distance/duration
        serializer = self.get_serializer(ride, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        # Use provided values or fall back to existing values on the ride object
        final_distance = serializer.validated_data.get('distance_km', ride.distance_km)
        final_duration = serializer.validated_data.get('duration_seconds', ride.duration_seconds)

        # TODO: Implement robust final fare calculation
        print("TODO: Implement final fare calculation.")
        final_fare = ride.estimated_fare or Decimal('50.00') # Use estimated or fallback

        # Update ride details
        ride.status = Ride.StatusChoices.COMPLETED
        ride.completed_at = timezone.now()
        ride.actual_fare = final_fare
        ride.distance_km = final_distance # Update actuals if provided
        ride.duration_seconds = final_duration
        ride.payment_status = Ride.PaymentStatusChoices.PENDING # Assume payment initiated after

        ride.save(update_fields=[
            'status', 'completed_at', 'payment_status',
            'actual_fare', 'distance_km', 'duration_seconds'
        ])

        # TODO: Trigger payment processing (e.g., queue Celery task)
        print("TODO: Trigger payment processing.")
        # TODO: Send notification to Rider (Trip Completed, Fare)

        response_serializer = RideDetailSerializer(ride, context={'request': request})
        return Response(response_serializer.data, status=status.HTTP_200_OK)

    @action(detail=True, methods=['post'], permission_classes=[permissions.IsAuthenticated, IsRideOwnerOrDriver])
    def rate_ride(self, request, pk=None):
        """Action for Rider or Driver to rate the *other* party after ride completion."""
        ride = self.get_object() # Checks object permissions
        rater = request.user

        # State Check: Only rate completed rides
        if ride.status != Ride.StatusChoices.COMPLETED:
            return Response({"detail": "Only completed rides can be rated."}, status=status.HTTP_400_BAD_REQUEST)

        # Determine who is being rated
        rated_user = None
        if ride.rider == rater and ride.driver: rated_user = ride.driver
        elif ride.driver == rater and ride.rider: rated_user = ride.rider
        else: return Response({"detail": "You cannot rate this ride participant."}, status=status.HTTP_403_FORBIDDEN)

        # Check if already rated by this user
        if RideRating.objects.filter(ride=ride, rater=rater).exists():
             return Response({"detail": "You have already rated this ride."}, status=status.HTTP_400_BAD_REQUEST)

        # Validate rating data using RideRatingSerializer
        serializer = self.get_serializer(data=request.data) # Gets RideRatingSerializer
        serializer.is_valid(raise_exception=True)

        # Create the rating, associating ride, rater, and rated_user
        rating_instance = serializer.save(
            ride=ride,
            rater=rater,
            rated_user=rated_user
        )

        # TODO: Update aggregate rating for the rated_user (e.g., using a signal or async task)
        print(f"TODO: Update aggregate rating for user {rated_user.id}")

        # Return the created rating data (using RideRatingSerializer by default)
        return Response(serializer.data, status=status.HTTP_201_CREATED)


# --- SavedLocation ViewSet ---
class SavedLocationViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing the User's Saved Locations (Home, Work, etc.).
    Provides full CRUD capabilities for the logged-in user.
    """
    serializer_class = SavedLocationSerializer
    permission_classes = [permissions.IsAuthenticated] # Only authenticated users

    def get_queryset(self):
        """Return only locations saved by the currently authenticated user."""
        return SavedLocation.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        """Automatically associate the saved location with the logged-in user."""
        serializer.save(user=self.request.user)

    # Default update/destroy methods provided by ModelViewSet are sufficient
    # as get_queryset ensures users can only affect their own locations.
