# rides/serializers.py

from rest_framework import serializers
from django.utils.translation import gettext_lazy as _
from .models import Ride, RideRating, SavedLocation # Removed RideLocation import
# Ensure UserPublicSerializer is correctly imported from your users app
# It should expose basic, non-sensitive user info (id, name, maybe profile pic)
from users.serializers import UserPublicSerializer
from decimal import Decimal, ROUND_DOWN

# --- SavedLocation Serializer ---
class SavedLocationSerializer(serializers.ModelSerializer):
    """Serializer for SavedLocation model (CRUD via SavedLocationViewSet)."""
    # User is automatically set based on authenticated request, make read-only
    user = serializers.PrimaryKeyRelatedField(read_only=True)
    # Use DecimalField for latitude and longitude to match model
    latitude = serializers.DecimalField(max_digits=14, decimal_places=7, coerce_to_string=False, required=True)
    longitude = serializers.DecimalField(max_digits=14, decimal_places=7, coerce_to_string=False, required=True)
    location_type = serializers.ChoiceField(choices=SavedLocation.LocationTypes.choices, required=True)
    name = serializers.CharField(max_length=100, required=True)
    address = serializers.CharField(required=False, allow_blank=True, allow_null=True)

    class Meta:
        model = SavedLocation
        fields = (
            'id', 'user', 'name', 'location_type',
            'latitude', 'longitude', # Use specific coordinate fields
            'address', 'is_default', 'created_at'
        )
        # User and created_at are set automatically/read-only
        read_only_fields = ('id', 'user', 'created_at')

# --- RideRating Serializer ---
# Used for creating/displaying a rating (input/output for RideViewSet.rate_ride action)
class RideRatingSerializer(serializers.ModelSerializer):
    """Serializer for creating and viewing Ride Ratings."""
    # Make related fields read-only for output, they are set in the view logic
    rater = UserPublicSerializer(read_only=True)
    rated_user = UserPublicSerializer(read_only=True)
    # Show ride ID in response, but don't require it on input (set in view)
    ride = serializers.PrimaryKeyRelatedField(read_only=True)

    # Define input fields explicitly for clarity
    rating = serializers.IntegerField(min_value=1, max_value=5, required=True, write_only=True)
    comment = serializers.CharField(required=False, allow_blank=True, allow_null=True, write_only=True)

    # Define output fields explicitly
    rating_display = serializers.IntegerField(source='rating', read_only=True)
    comment_display = serializers.CharField(source='comment', read_only=True)


    class Meta:
        model = RideRating
        fields = (
            'id', 'ride', 'rater', 'rated_user', # Output related info
            'rating', 'comment', # Input fields (write_only)
            'rating_display', 'comment_display', # Output fields (read_only)
            'created_at'
        )
        read_only_fields = ('id', 'ride', 'rater', 'rated_user', 'created_at', 'rating_display', 'comment_display')
        # Write only fields are defined above

# --- Ride Serializers ---

# Serializer for displaying basic Ride info (e.g., in lists)
class RideSerializer(serializers.ModelSerializer):
    """Basic serializer for displaying Ride list information."""
    # Use a specific public serializer for nested user display
    rider = UserPublicSerializer(read_only=True)
    driver = UserPublicSerializer(read_only=True, allow_null=True) # Driver can be null
    # Add display values for choices fields
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    payment_status_display = serializers.CharField(source='get_payment_status_display', read_only=True)

    class Meta:
        model = Ride
        fields = (
            'id', 'rider', 'driver', 'status', 'status_display',
            'payment_status', 'payment_status_display',
            'pickup_address', 'destination_address', # Show addresses for quick view
            'estimated_fare', 'estimated_fare', # Show fares
            'requested_at', 'completed_at', # Key timestamps
        )
        read_only_fields = fields # All fields read-only for list display


# Serializer for displaying detailed Ride info (e.g., on retrieve)
class RideDetailSerializer(RideSerializer): # Inherit from RideSerializer
    """Detailed serializer for retrieving a single Ride."""
    # Add nested rating object using its serializer
    rating = RideRatingSerializer(read_only=True, allow_null=True)

    class Meta(RideSerializer.Meta): # Inherit Meta from RideSerializer
         # Add more detailed fields to the inherited list
         fields = RideSerializer.Meta.fields + (
            'pickup_location_lat', 'pickup_location_lng',
            'destination_lat', 'destination_lng',
            'accepted_at', 'arrived_at_pickup_at', 'trip_started_at', 'cancelled_at',
            'distance_km', 'duration_seconds',
            'base_fare', 'distance_fare', 'duration_fare', 'total_fare', # Fare components
            'cancellation_reason', 'cancellation_fee',
            'rating', # Add the nested rating field
         )
         read_only_fields = fields # All fields read-only for detail view


# Serializer for creating a new ride request (Rider input for create_ride_request action)
class RideCreateSerializer(serializers.ModelSerializer):
    """Serializer for validating data when a Rider creates a ride request."""

    def to_internal_value(self, data):
        for field in ['pickup_location_lat', 'pickup_location_lng', 'destination_lat', 'destination_lng']:
            if field in data:
                try:
                    data[field] = str(Decimal(data[field]).quantize(Decimal('0.0000001'), rounding=ROUND_DOWN))
                except Exception:
                    pass
        return super().to_internal_value(data)
    
    # Rider provides location details
    pickup_location_lat = serializers.DecimalField(max_digits=16, decimal_places=7, required=True, coerce_to_string=False)
    pickup_location_lng = serializers.DecimalField(max_digits=16, decimal_places=7, required=True, coerce_to_string=False)
    pickup_address = serializers.CharField(required=False, allow_blank=True, allow_null=True, max_length=255) # Limit length
    destination_lat = serializers.DecimalField(max_digits=16, decimal_places=7, required=True, coerce_to_string=False)
    destination_lng = serializers.DecimalField(max_digits=16, decimal_places=7, required=True, coerce_to_string=False)
    destination_address = serializers.CharField(required=False, allow_blank=True, allow_null=True, max_length=255) # Limit length

    class Meta:
        model = Ride
        # Fields expected from the rider during request creation
        fields = (
            'pickup_location_lat', 'pickup_location_lng', 'pickup_address',
            'destination_lat', 'destination_lng', 'destination_address',
            # Add 'ride_type' here if you have multiple types the user can select
        )
        # Note: 'rider' is set in the view using request.user
        # Note: 'status' defaults to REQUESTED in the model
        # Note: 'estimated_fare' should be calculated in the view/service, not input by rider


# Serializer for cancelling a ride (Rider/Driver input for cancel_ride action)
class RideCancelSerializer(serializers.ModelSerializer):
    """Serializer for validating data when cancelling a ride."""
    # Only requires the reason for cancellation as input
    cancellation_reason = serializers.CharField(
        required=True,
        allow_blank=False,
        error_messages={'required': 'Cancellation reason is required.', 'blank': 'Cancellation reason cannot be blank.'}
        )

    class Meta:
        model = Ride
        fields = ('cancellation_reason',)
        # 'status', 'cancelled_at', 'cancellation_fee' are set in the view action logic


# Serializer for completing a ride (Driver input for complete_trip action, optional)
# Used if driver needs to confirm/provide final distance/duration
class RideCompleteSerializer(serializers.ModelSerializer):
    """Serializer for optional data provided by driver upon ride completion."""
    distance_km = serializers.DecimalField(max_digits=10, decimal_places=2, required=False, coerce_to_string=False)
    duration_seconds = serializers.IntegerField(required=False, min_value=0)

    class Meta:
        model = Ride
        fields = ('distance_km', 'duration_seconds')
        # 'status', 'completed_at', 'actual_fare' etc. are set in the view action logic


# ---  Serializer for Fare Estimation Input ---
class RideEstimateFareSerializer(serializers.Serializer):
    """Serializer for validating input coordinates for fare estimation."""

    def _truncate_value(self, value):
        return Decimal(value).quantize(Decimal('0.0000001'), rounding=ROUND_DOWN)
    

    pickup_location_lat = serializers.DecimalField(max_digits=16, decimal_places=7, required=True, coerce_to_string=False)
    pickup_location_lng = serializers.DecimalField(max_digits=16, decimal_places=7, required=True, coerce_to_string=False)
    destination_lat = serializers.DecimalField(max_digits=16, decimal_places=7, required=True, coerce_to_string=False)
    destination_lng = serializers.DecimalField(max_digits=16, decimal_places=7, required=True, coerce_to_string=False)

    def to_internal_value(self, data):
        for field in ['pickup_location_lat', 'pickup_location_lng', 'destination_lat', 'destination_lng']:
            if field in data:
                try:
                    data[field] = str(Decimal(data[field]).quantize(Decimal('0.0000001'), rounding=ROUND_DOWN))
                except Exception:
                    pass
        return super().to_internal_value(data)