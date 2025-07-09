# rides/serializers.py

from rest_framework import serializers
from django.utils.translation import gettext_lazy as _
from .models import Ride, RideRating, SavedLocation, DriverAvailability # Added DriverAvailability import
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
    rider = UserPublicSerializer(read_only=True)
    driver = UserPublicSerializer(read_only=True, allow_null=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    payment_status_display = serializers.CharField(source='get_payment_status_display', read_only=True)

    # Expose lat/lng from PointFields for API clients
    pickup_lat = serializers.SerializerMethodField()
    pickup_lng = serializers.SerializerMethodField()
    destination_lat = serializers.SerializerMethodField()
    destination_lng = serializers.SerializerMethodField()

    def get_pickup_lat(self, obj):
        if obj.pickup_location:
            return float(obj.pickup_location.y)
        return None
    def get_pickup_lng(self, obj):
        if obj.pickup_location:
            return float(obj.pickup_location.x)
        return None
    def get_destination_lat(self, obj):
        if obj.destination:
            return float(obj.destination.y)
        return None
    def get_destination_lng(self, obj):
        if obj.destination:
            return float(obj.destination.x)
        return None

    class Meta:
        model = Ride
        fields = (
            'id', 'rider', 'driver', 'status', 'status_display',
            'payment_status', 'payment_status_display',
<<<<<<< HEAD
            'pickup_address', 'destination_address',
            'pickup_lat', 'pickup_lng', 'destination_lat', 'destination_lng',
            'estimated_fare', 'base_fare', 'duration_fare', 'distance_fare', 'total_fare',
            'requested_at', 'completed_at',
=======
            'pickup_address', 'destination_address', # Show addresses for quick view
            'estimated_fare', 'base_fare', 'duration_fare', 'distance_fare', 'total_fare', # Show fares
            'requested_at', 'completed_at', # Key timestamps
>>>>>>> 8bab12e (task)
        )
        read_only_fields = fields


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

    def create(self, validated_data):
        from django.contrib.gis.geos import Point
        pickup_lat = validated_data.get('pickup_location_lat')
        pickup_lng = validated_data.get('pickup_location_lng')
        destination_lat = validated_data.get('destination_lat')
        destination_lng = validated_data.get('destination_lng')
        # Set PointFields
        if pickup_lat is not None and pickup_lng is not None:
            validated_data['pickup_location'] = Point(float(pickup_lng), float(pickup_lat), srid=4326)
        if destination_lat is not None and destination_lng is not None:
            validated_data['destination'] = Point(float(destination_lng), float(destination_lat), srid=4326)
        return super().create(validated_data)

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


# --- DriverAvailability Serializers ---

class DriverAvailabilitySerializer(serializers.ModelSerializer):
    """Basic serializer for displaying driver availability information."""
    driver = UserPublicSerializer(read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    service_area_display = serializers.CharField(source='get_service_area_display', read_only=True)
    
    # Location fields
    current_lat = serializers.SerializerMethodField()
    current_lng = serializers.SerializerMethodField()
    
    class Meta:
        model = DriverAvailability
        fields = (
            'id', 'driver', 'status', 'status_display',
            'current_lat', 'current_lng', 'current_address',
            'service_area', 'service_area_display', 'max_distance_km',
            'average_rating', 'total_rides_completed',
            'last_location_update', 'last_online_at', 'last_offline_at',
            'is_available_for_rides', 'is_planned_route_active'
        )
        read_only_fields = fields

    def get_current_lat(self, obj):
        """Extract latitude from PointField"""
        if obj.current_location:
            return float(obj.current_location.y)
        return None

    def get_current_lng(self, obj):
        """Extract longitude from PointField"""
        if obj.current_location:
            return float(obj.current_location.x)
        return None


class DriverAvailabilityUpdateSerializer(serializers.ModelSerializer):
    """Serializer for updating driver availability status and location."""
    
    # Location update fields
    current_lat = serializers.DecimalField(
        max_digits=16, 
        decimal_places=7, 
        required=False, 
        coerce_to_string=False
    )
    current_lng = serializers.DecimalField(
        max_digits=16, 
        decimal_places=7, 
        required=False, 
        coerce_to_string=False
    )
    current_address = serializers.CharField(required=False, allow_blank=True)
    
    # Status update
    status = serializers.ChoiceField(
        choices=DriverAvailability.AvailabilityStatus.choices,
        required=False
    )
    
    # Planned route fields
    planned_destination_lat = serializers.DecimalField(
        max_digits=16, 
        decimal_places=7, 
        required=False, 
        coerce_to_string=False
    )
    planned_destination_lng = serializers.DecimalField(
        max_digits=16, 
        decimal_places=7, 
        required=False, 
        coerce_to_string=False
    )
    planned_destination_address = serializers.CharField(required=False, allow_blank=True)
    planned_departure_time = serializers.DateTimeField(required=False)
    planned_arrival_time = serializers.DateTimeField(required=False)

    class Meta:
        model = DriverAvailability
        fields = (
            'status', 'current_lat', 'current_lng', 'current_address',
            'planned_destination_lat', 'planned_destination_lng', 
            'planned_destination_address', 'planned_departure_time', 
            'planned_arrival_time'
        )

    def update(self, instance, validated_data):
        """Custom update method to handle location updates properly."""
        from django.contrib.gis.geos import Point
        
        # Handle location update
        if 'current_lat' in validated_data and 'current_lng' in validated_data:
            lat = validated_data.pop('current_lat')
            lng = validated_data.pop('current_lng')
            address = validated_data.pop('current_address', None)
            
            # Update location using the model method
            instance.update_location(float(lat), float(lng), address)
        
        # Handle planned route coordinates
        if 'planned_destination_lat' in validated_data and 'planned_destination_lng' in validated_data:
            # Convert to float for storage
            validated_data['planned_destination_lat'] = float(validated_data['planned_destination_lat'])
            validated_data['planned_destination_lng'] = float(validated_data['planned_destination_lng'])
        
        # Update other fields normally
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        
        instance.save()
        return instance


class DriverAvailabilityCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating driver availability profile."""
    
    # Location fields
    current_lat = serializers.DecimalField(
        max_digits=16, 
        decimal_places=7, 
        required=False, 
        coerce_to_string=False
    )
    current_lng = serializers.DecimalField(
        max_digits=16, 
        decimal_places=7, 
        required=False, 
        coerce_to_string=False
    )
    
    # Planned route fields
    planned_destination_lat = serializers.DecimalField(
        max_digits=16, 
        decimal_places=7, 
        required=False, 
        coerce_to_string=False
    )
    planned_destination_lng = serializers.DecimalField(
        max_digits=16, 
        decimal_places=7, 
        required=False, 
        coerce_to_string=False
    )

    class Meta:
        model = DriverAvailability
        fields = (
            'service_area', 'max_distance_km', 'is_available_24_7',
            'preferred_start_time', 'preferred_end_time',
            'preferred_ride_types', 'minimum_fare_preference',
            'current_lat', 'current_lng', 'current_address',
            'planned_destination_lat', 'planned_destination_lng',
            'planned_destination_address', 'planned_departure_time',
            'planned_arrival_time'
        )
        read_only_fields = ('driver',)  # Driver is set from request.user

    def create(self, validated_data):
        """Custom create method to handle location fields properly."""
        from django.contrib.gis.geos import Point
        
        # Handle current location
        current_lat = validated_data.pop('current_lat', None)
        current_lng = validated_data.pop('current_lng', None)
        
        if current_lat and current_lng:
            validated_data['current_location'] = Point(
                float(current_lng), float(current_lat), srid=4326
            )
        
        # Handle planned destination coordinates
        planned_lat = validated_data.pop('planned_destination_lat', None)
        planned_lng = validated_data.pop('planned_destination_lng', None)
        
        if planned_lat and planned_lng:
            validated_data['planned_destination_lat'] = float(planned_lat)
            validated_data['planned_destination_lng'] = float(planned_lng)
        
        # Set driver from request
        validated_data['driver'] = self.context['request'].user
        
        return super().create(validated_data)


class DriverSearchSerializer(serializers.Serializer):
    """Serializer for searching available drivers near a location."""
    
    pickup_lat = serializers.DecimalField(
        max_digits=16, 
        decimal_places=7, 
        required=True, 
        coerce_to_string=False
    )
    pickup_lng = serializers.DecimalField(
        max_digits=16, 
        decimal_places=7, 
        required=True, 
        coerce_to_string=False
    )
    max_distance_km = serializers.DecimalField(
        max_digits=5, 
        decimal_places=2, 
        default=10.00,
        coerce_to_string=False
    )
    min_rating = serializers.DecimalField(
        max_digits=3, 
        decimal_places=2, 
        required=False,
        coerce_to_string=False
    )
    service_area = serializers.ChoiceField(
        choices=DriverAvailability.ServiceArea.choices,
        required=False
    )
<<<<<<< HEAD
    limit = serializers.IntegerField(default=10, min_value=1, max_value=50)
=======
    limit = serializers.IntegerField(default=10, min_value=1, max_value=50)
>>>>>>> 8bab12e (task)
