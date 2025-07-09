# rides/views.py

from decimal import Decimal # Import Decimal for fares
from django.db import transaction # Import transaction for atomic operations
from django.db.models import Q # Import Q objects for complex queries
from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework import viewsets, status, mixins, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
<<<<<<< HEAD
import logging

# --- Notification imports ---
from django.contrib.auth import get_user_model
from notifications.tasks import send_fcm_notification_task
# Add WebSocket imports
from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer

User = get_user_model()
=======
>>>>>>> refs/remotes/origin/main

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
<<<<<<< HEAD


# 
# 
# TODO: notify driver when rider calclesla dn viseversa 
  
#   wrap fcm send calls in a try except and log failures 
=======
>>>>>>> refs/remotes/origin/main
class IsOwner(permissions.BasePermission):
    """Placeholder: Allow only owner of object."""
    def has_object_permission(self, request, view, obj):
        # Example: return obj.user == request.user
        return True # Replace with actual logic


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
<<<<<<< HEAD
    
=======

>>>>>>> refs/remotes/origin/main
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
<<<<<<< HEAD
        }
=======

        }
        # Return specific serializer for the action, or default (RideSerializer for list)
>>>>>>> refs/remotes/origin/main
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
        print(request.data)
        serializer = self.get_serializer(data=request.data) # Gets RideCreateSerializer
        serializer.is_valid(raise_exception=True)

<<<<<<< HEAD
=======
       

>>>>>>> refs/remotes/origin/main
        # Save the ride request, associating rider and setting status/fare
        ride = serializer.save(
            rider=request.user,
            status=Ride.StatusChoices.REQUESTED,   
        )

<<<<<<< HEAD
        # Notify all drivers about new ride request via FCM
        # TODO: NOTIFY ONLY NEARBY DRIVERS 
        for driver in User.objects.filter(user_type='driver').exclude(fcm_token__isnull=True).exclude(fcm_token=''):
            try:
                result = send_fcm_notification_task.delay(
                    driver.id,
                    title="New Ride Request",
                    body=f"{request.user.get_full_name()} requested a ride from {ride.pickup_address}",
                    data_payload={'ride_id': str(ride.id), 'type': 'NEW_RIDE'}
                )
                logging.info(f"Notification task dispatched for driver {driver.id}: {result}")
            except Exception as e:
                logging.error(f"Failed to dispatch notification for driver {driver.id}: {e}")

        # NEW: Send WebSocket notification to all online drivers
        try:
            channel_layer = get_channel_layer()
            async_to_sync(channel_layer.group_send)(
                "drivers",
                {
                    "type": "send_notification",
                    "payload": {
                        "type": "new_ride_request",
                        "ride_id": str(ride.id),
                        "title": "New Ride Request",
                        "body": f"{request.user.get_full_name()} requested a ride from {ride.pickup_address}",
                        "ride_data": {
                            "id": ride.id,
                            "status": ride.status,
                            "pickup_location_lat": ride.pickup_location_lat,
                            "pickup_location_lng": ride.pickup_location_lng,
                            "pickup_address": ride.pickup_address,
                            "destination_lat": ride.destination_lat,
                            "destination_lng": ride.destination_lng,
                            "destination_address": ride.destination_address,
                            "estimated_fare": str(ride.estimated_fare) if ride.estimated_fare else "0.00",
                            "requested_at": ride.requested_at.isoformat(),
                            "rider": {
                                "id": ride.rider.id,
                                "username": ride.rider.username,
                                "first_name": ride.rider.first_name,
                                "last_name": ride.rider.last_name,
                                "full_name": ride.rider.get_full_name(),
                                "phone_number": ride.rider.phone_number,
                                "email": ride.rider.email,
                                "user_type": ride.rider.user_type,
                                "is_online": ride.rider.is_online,
                                "profile_picture": ride.rider.profile_picture,
                                "current_location": ride.rider.current_location,
                                "fcm_token": ride.rider.fcm_token,
                                "vehicle_model": ride.rider.vehicle_model,
                                "vehicle_number": ride.rider.vehicle_number,
                            } if ride.rider else None,
                        }
                    }
                }
            )
            logging.info(f"WebSocket notification sent to drivers group for ride {ride.id}")
        except Exception as e:
            logging.error(f"Failed to send WebSocket notification for ride {ride.id}: {e}")

=======
>>>>>>> refs/remotes/origin/main
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
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        try:
            estimated_fare = get_estimated_fare(
                pickup_lat=data['pickup_location_lat'],
                pickup_lng=data['pickup_location_lng'],
                dest_lat=data['destination_lat'],
                dest_lng=data['destination_lng']
            )
            if estimated_fare is None:
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

<<<<<<< HEAD
        # Notify assigned driver if rider cancels
        if new_status == Ride.StatusChoices.CANCELLED_BY_RIDER and ride.driver and ride.driver.fcm_token:
            try:
                result = send_fcm_notification_task.delay(
                    ride.driver.id,
                    title="Ride Cancelled",
                    body=f"Passenger cancelled ride {ride.id}.",
                    data_payload={'ride_id': str(ride.id), 'type': 'RIDE_CANCELLED'}
                )
                logging.info(f"Notification task dispatched for driver {ride.driver.id}: {result}")
            except Exception as e:
                logging.error(f"Failed to dispatch notification for driver {ride.driver.id}: {e}")
        
        # 1) Notify rider if driver cancels
        if new_status == Ride.StatusChoices.CANCELLED_BY_DRIVER and ride.rider and ride.rider.fcm_token:
            try:
                result = send_fcm_notification_task.delay(
                    ride.rider.id,
                    title="Ride Cancelled",
                    body=f"Your driver cancelled ride {ride.id}. Please try again.",
                    data_payload={'ride_id': str(ride.id), 'type': 'RIDE_CANCELLED_BY_DRIVER'}
                )
                logging.info(f"Notification task dispatched for rider {ride.rider.id}: {result}")
            except Exception as e:
                logging.error(f"Failed to dispatch notification for rider {ride.rider.id}: {e}")

        # NEW: Send WebSocket notification to all drivers about ride cancellation
        try:
            channel_layer = get_channel_layer()
            async_to_sync(channel_layer.group_send)(
                "drivers",
                {
                    "type": "send_notification",
                    "payload": {
                        "type": "ride_cancelled",
                        "ride_id": str(ride.id),
                        "title": "Ride Cancelled",
                        "body": f"Ride {ride.id} has been cancelled",
                    }
                }
            )
            logging.info(f"WebSocket notification sent to drivers group for cancelled ride {ride.id}")
        except Exception as e:
            logging.error(f"Failed to send WebSocket notification for cancelled ride {ride.id}: {e}")

=======
>>>>>>> refs/remotes/origin/main
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
<<<<<<< HEAD
        # Notify Rider that ride was accepted
        if ride.rider and ride.rider.fcm_token:
            try:
                result = send_fcm_notification_task.delay(
                    ride.rider.id,
                    title="Ride Accepted",
                    body=f"Your ride request {ride.id} has been accepted by {driver.get_full_name()}.",
                    data_payload={'ride_id': str(ride.id), 'type': 'RIDE_ACCEPTED'}
                )
                logging.info(f"Notification task dispatched for rider {ride.rider.id}: {result}")
            except Exception as e:
                logging.error(f"Failed to dispatch notification for rider {ride.rider.id}: {e}")

        # NEW: Send WebSocket notification to all drivers that this ride was accepted
        try:
            channel_layer = get_channel_layer()
            async_to_sync(channel_layer.group_send)(
                "drivers",
                {
                    "type": "send_notification",
                    "payload": {
                        "type": "ride_accepted",
                        "ride_id": str(ride.id),
                        "title": "Ride Accepted",
                        "body": f"Ride {ride.id} has been accepted by another driver",
                    }
                }
            )
            logging.info(f"WebSocket notification sent to drivers group for accepted ride {ride.id}")
        except Exception as e:
            logging.error(f"Failed to send WebSocket notification for accepted ride {ride.id}: {e}")
=======
>>>>>>> refs/remotes/origin/main

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
<<<<<<< HEAD
              valid_transition = True
              # Notify Rider that driver is en route
              if ride.rider and ride.rider.fcm_token:
                  try:
                      result = send_fcm_notification_task.delay(
                          ride.rider.id,
                          title="Driver En Route",
                          body=f"Your driver is on the way for ride {ride.id}.",
                          data_payload={'ride_id': str(ride.id), 'type': 'DRIVER_EN_ROUTE'}
                      )
                      logging.info(f"Notification task dispatched for rider {ride.rider.id}: {result}")
                  except Exception as e:
                      logging.error(f"Failed to dispatch notification for rider {ride.rider.id}: {e}")
         elif new_status == Ride.StatusChoices.ARRIVED_AT_PICKUP and ride.status == Ride.StatusChoices.ON_ROUTE_TO_PICKUP:
              ride.arrived_at_pickup_at = now
              update_fields.append('arrived_at_pickup_at')
              valid_transition = True
              # Notify Rider that driver has arrived
              if ride.rider and ride.rider.fcm_token:
                  try:
                      result = send_fcm_notification_task.delay(
                          ride.rider.id,
                          title="Driver Arrived",
                          body=f"Your driver has arrived at pickup location for ride {ride.id}.",
                          data_payload={'ride_id': str(ride.id), 'type': 'DRIVER_ARRIVED'}
                      )
                      logging.info(f"Notification task dispatched for rider {ride.rider.id}: {result}")
                  except Exception as e:
                      logging.error(f"Failed to dispatch notification for rider {ride.rider.id}: {e}")
         elif new_status == Ride.StatusChoices.ON_TRIP and ride.status == Ride.StatusChoices.ARRIVED_AT_PICKUP:
              ride.trip_started_at = now
              update_fields.append('trip_started_at')
              valid_transition = True
              # Notify Rider that trip has started
              if ride.rider and ride.rider.fcm_token:
                  try:
                      result = send_fcm_notification_task.delay(
                          ride.rider.id,
                          title="Trip Started",
                          body=f"Your trip {ride.id} has started.",
                          data_payload={'ride_id': str(ride.id), 'type': 'TRIP_STARTED'}
                      )
                      logging.info(f"Notification task dispatched for rider {ride.rider.id}: {result}")
                  except Exception as e:
                      logging.error(f"Failed to dispatch notification for rider {ride.rider.id}: {e}")
=======
              valid_transition = True; print("TODO: Notify Rider - Driver En Route")
         elif new_status == Ride.StatusChoices.ARRIVED_AT_PICKUP and ride.status == Ride.StatusChoices.ON_ROUTE_TO_PICKUP:
              ride.arrived_at_pickup_at = now; update_fields.append('arrived_at_pickup_at'); valid_transition = True; print("TODO: Notify Rider - Driver Arrived")
         elif new_status == Ride.StatusChoices.ON_TRIP and ride.status == Ride.StatusChoices.ARRIVED_AT_PICKUP:
              ride.trip_started_at = now; update_fields.append('trip_started_at'); valid_transition = True; print("TODO: Notify Rider - Trip Started")
>>>>>>> refs/remotes/origin/main

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
<<<<<<< HEAD
        # Notify Rider that trip is completed
        if ride.rider and ride.rider.fcm_token:
            try:
                result = send_fcm_notification_task.delay(
                    ride.rider.id,
                    title="Trip Completed",
                    body=f"Your trip {ride.id} is complete. Fare: GH₵ {final_fare:.2f}.",
                    data_payload={'ride_id': str(ride.id), 'type': 'TRIP_COMPLETED'}
                )
                logging.info(f"Notification task dispatched for rider {ride.rider.id}: {result}")
            except Exception as e:
                logging.error(f"Failed to dispatch notification for rider {ride.rider.id}: {e}")
=======
        # TODO: Send notification to Rider (Trip Completed, Fare)
>>>>>>> refs/remotes/origin/main

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
