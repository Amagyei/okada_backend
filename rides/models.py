# rides/models.py

from django.db import models
from django.conf import settings # Use settings.AUTH_USER_MODEL
from django.utils.translation import gettext_lazy as _
from django.core.validators import MinValueValidator, MaxValueValidator
from django.contrib.gis.db import models as gis_models

# Ensure users.models is correctly imported if needed elsewhere,
# but prefer settings.AUTH_USER_MODEL for foreign keys.
# from users.models import User # Less preferred than settings.AUTH_USER_MODEL

class Ride(models.Model):
    # Using TextChoices for better integration and readability
    class StatusChoices(models.TextChoices):
        REQUESTED = 'REQUESTED', _('Requested')
        ACCEPTED = 'ACCEPTED', _('Accepted')
        ON_ROUTE_TO_PICKUP = 'ON_ROUTE_TO_PICKUP', _('On Route to Pickup')
        ARRIVED_AT_PICKUP = 'ARRIVED_AT_PICKUP', _('Arrived at Pickup')
        ON_TRIP = 'ON_TRIP', _('On Trip')
        COMPLETED = 'COMPLETED', _('Completed')
        CANCELLED_BY_RIDER = 'CANCELLED_BY_RIDER', _('Cancelled by Rider')
        CANCELLED_BY_DRIVER = 'CANCELLED_BY_DRIVER', _('Cancelled by Driver')
        NO_DRIVER_FOUND = 'NO_DRIVER_FOUND', _('No Driver Found')

    class PaymentStatusChoices(models.TextChoices):
        PENDING = 'PENDING', _('Pending')
        PROCESSING = 'PROCESSING', _('Processing')
        COMPLETED = 'COMPLETED', _('Completed')
        FAILED = 'FAILED', _('Failed')
        REFUNDED = 'REFUNDED', _('Refunded')

    # === Relationships ===
    rider = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name='rides_as_rider',
        limit_choices_to={'user_type': 'rider'},
        null=True
    )
    driver = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name='rides_as_driver',
        limit_choices_to={'user_type': 'driver'},
        null=True,
        blank=True
    )

    # === Location ===
    pickup_location_lat = models.DecimalField(max_digits=16, decimal_places=7, help_text="Latitude of pickup location")
    pickup_location_lng = models.DecimalField(max_digits=16, decimal_places=7, help_text="Longitude of pickup location")
    pickup_address = models.TextField(blank=True, null=True, help_text="Textual address or description of pickup")

    destination_lat = models.DecimalField(max_digits=16, decimal_places=7, help_text="Latitude of destination")
    destination_lng = models.DecimalField(max_digits=16, decimal_places=7, help_text="Longitude of destination")
    destination_address = models.TextField(blank=True, null=True, help_text="Textual address or description of destination")

    # === Status & Timestamps ===
    status = models.CharField(
        max_length=25,
        choices=StatusChoices.choices,
        default=StatusChoices.REQUESTED,
        db_index=True
    )
    payment_status = models.CharField(
        max_length=20,
        choices=PaymentStatusChoices.choices,
        default=PaymentStatusChoices.PENDING,
        db_index=True # Index for filtering payments
    )
    requested_at = models.DateTimeField(auto_now_add=True)
    accepted_at = models.DateTimeField(null=True, blank=True)
    arrived_at_pickup_at = models.DateTimeField(null=True, blank=True) # Added for clarity
    trip_started_at = models.DateTimeField(null=True, blank=True) # Renamed from started_at
    completed_at = models.DateTimeField(null=True, blank=True)
    cancelled_at = models.DateTimeField(null=True, blank=True)

    # === Ride & Fare Details ===
    # Store distance in meters or km, be consistent
    distance_km = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    # Store duration in seconds for precision, convert to minutes for display
    duration_seconds = models.PositiveIntegerField(null=True, blank=True)

    # Optional: Store currency (important for multi-currency apps)
    # currency = models.CharField(max_length=3, default='GHS') # Example for Ghana Cedi

    # Fares can be null if ride cancelled before calculation etc.
    estimated_fare = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    base_fare = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    distance_fare = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    duration_fare = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True) # Optional fare component
    # Add other potential fare components (surge, tolls, etc.)
    total_fare = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    cancellation_fee = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    # === Cancellation Info ===
    cancellation_reason = models.TextField(null=True, blank=True)

    class Meta:
        verbose_name = _('Ride')
        verbose_name_plural = _('Rides')
        ordering = ['-requested_at'] # Order by request time descending

    def __str__(self):
        rider_info = self.rider.username if self.rider else 'N/A'
        return f"Ride {self.id} ({rider_info} - Status: {self.get_status_display()})"


# --- RideLocation model removed ---
# If path tracking is needed, create a new model like RidePathCoordinate:
# class RidePathCoordinate(models.Model):
#     ride = models.ForeignKey(Ride, on_delete=models.CASCADE, related_name='path_coordinates')
#     latitude = models.DecimalField(max_digits=10, decimal_places=7)
#     longitude = models.DecimalField(max_digits=10, decimal_places=7)
#     timestamp = models.DateTimeField()
#     class Meta:
#         ordering = ['timestamp']


class RideRating(models.Model):
    ride = models.OneToOneField(
        Ride,
        on_delete=models.CASCADE,
        related_name='rating'
    )
    # --- Added rater and rated_user ---
    rater = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL, # Keep rating even if rater account deleted
        related_name='given_ratings',
        null=True
    )
    rated_user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE, # Delete rating if rated user is deleted
        related_name='received_ratings',
        null=True # Should not be null in practice, but handle deletion
    )
    # --- End Added fields ---
    rating = models.PositiveSmallIntegerField( # Use PositiveSmallIntegerField for 1-5
        validators=[MinValueValidator(1), MaxValueValidator(5)] # Use validators
    )
    comment = models.TextField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = _('Ride Rating')
        verbose_name_plural = _('Ride Ratings')
        ordering = ['-created_at']
        # Prevent duplicate ratings for the same ride by the same user
        unique_together = ('ride', 'rater')

    def __str__(self):
        rater_name = self.rater.username if self.rater else 'N/A'
        return f"Rating {self.rating}* for Ride {self.ride_id} by {rater_name}"


class SavedLocation(models.Model):
    class LocationTypes(models.TextChoices): # Use TextChoices
        HOME = 'HOME', _('Home')
        WORK = 'WORK', _('Work')
        OTHER = 'OTHER', _('Other')

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='saved_location_entries' # Ensure unique related_name
    )
    name = models.CharField(max_length=100)
    location_type = models.CharField(max_length=10, choices=LocationTypes.choices)

    # --- Replaced JSONField with specific coordinate fields ---
    latitude = models.DecimalField(max_digits=10, decimal_places=7)
    longitude = models.DecimalField(max_digits=10, decimal_places=7)
    # --- End Replaced field ---

    address = models.TextField(blank=True, null=True) # Address can be optional
    is_default = models.BooleanField(default=False) # For setting a default home/work etc.
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = _('Saved Location')
        verbose_name_plural = _('Saved Locations')
        # Ensure a user doesn't save two locations with the same name
        unique_together = ('user', 'name')
        ordering = ['location_type', 'name']

    def __str__(self):
        user_info = self.user.username if self.user else 'N/A'
        return f"{self.name} ({self.get_location_type_display()}) - {user_info}"


class RidePathCoordinate(models.Model):
    ride = models.ForeignKey(Ride, on_delete=models.CASCADE, related_name='path_coordinates')
    latitude = models.DecimalField(max_digits=10, decimal_places=7)
    longitude = models.DecimalField(max_digits=10, decimal_places=7)
    timestamp = models.DateTimeField()
    class Meta:
        ordering = ['timestamp']


class DriverAvailability(models.Model):
    """
    Model to track driver availability, planned routes, and current status
    for efficient ride matching and dispatch.
    """
    
    class AvailabilityStatus(models.TextChoices):
        ONLINE = 'ONLINE', _('Online - Available for rides')
        OFFLINE = 'OFFLINE', _('Offline - Not available')
        BUSY = 'BUSY', _('Busy - Currently on a ride')
        BREAK = 'BREAK', _('On break')
        MAINTENANCE = 'MAINTENANCE', _('Vehicle maintenance')
        UNAVAILABLE = 'UNAVAILABLE', _('Temporarily unavailable')

    class ServiceArea(models.TextChoices):
        ACCRA_CENTRAL = 'ACCRA_CENTRAL', _('Accra Central')
        ACCRA_NORTH = 'ACCRA_NORTH', _('Accra North')
        ACCRA_WEST = 'ACCRA_WEST', _('Accra West')
        ACCRA_EAST = 'ACCRA_EAST', _('Accra East')
        GREATER_ACCRA = 'GREATER_ACCRA', _('Greater Accra')
        CUSTOM = 'CUSTOM', _('Custom area')

    # === Driver Relationship ===
    driver = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='availability',
        limit_choices_to={'user_type': 'driver'}
    )

    # === Current Status ===
    status = models.CharField(
        max_length=20,
        choices=AvailabilityStatus.choices,
        default=AvailabilityStatus.OFFLINE,
        db_index=True
    )
    
    # === Location Information ===
    current_location = gis_models.PointField(
        null=True, 
        blank=True, 
        srid=4326,
        help_text="Current GPS location (longitude, latitude)"
    )
    current_address = models.TextField(blank=True, null=True)
    last_location_update = models.DateTimeField(auto_now=True)
    
    # === Service Area & Preferences ===
    service_area = models.CharField(
        max_length=20,
        choices=ServiceArea.choices,
        default=ServiceArea.ACCRA_CENTRAL
    )
    custom_service_area = gis_models.PolygonField(
        null=True, 
        blank=True, 
        srid=4326,
        help_text="Custom service area polygon (if service_area is CUSTOM)"
    )
    max_distance_km = models.DecimalField(
        max_digits=5, 
        decimal_places=2, 
        default=10.00,
        help_text="Maximum distance driver is willing to travel for pickup"
    )
    
    # === Planned Route (for drivers heading to a destination) ===
    planned_destination_lat = models.DecimalField(
        max_digits=16, 
        decimal_places=7, 
        null=True, 
        blank=True,
        help_text="Latitude of driver's planned destination"
    )
    planned_destination_lng = models.DecimalField(
        max_digits=16, 
        decimal_places=7, 
        null=True, 
        blank=True,
        help_text="Longitude of driver's planned destination"
    )
    planned_destination_address = models.TextField(blank=True, null=True)
    planned_departure_time = models.DateTimeField(null=True, blank=True)
    planned_arrival_time = models.DateTimeField(null=True, blank=True)
    
    # === Availability Schedule ===
    is_available_24_7 = models.BooleanField(default=False)
    preferred_start_time = models.TimeField(null=True, blank=True)
    preferred_end_time = models.TimeField(null=True, blank=True)
    
    # === Performance & Preferences ===
    average_rating = models.DecimalField(
        max_digits=3, 
        decimal_places=2, 
        default=0.00
    )
    total_rides_completed = models.PositiveIntegerField(default=0)
    preferred_ride_types = models.JSONField(
        default=list,
        blank=True,
        help_text="List of preferred ride types: ['short', 'long', 'airport', etc.]"
    )
    minimum_fare_preference = models.DecimalField(
        max_digits=10, 
        decimal_places=2, 
        null=True, 
        blank=True,
        help_text="Minimum fare driver prefers to accept"
    )
    
    # === Timestamps ===
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    last_online_at = models.DateTimeField(null=True, blank=True)
    last_offline_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        verbose_name = _('Driver Availability')
        verbose_name_plural = _('Driver Availabilities')
        ordering = ['-last_location_update']
        indexes = [
            models.Index(fields=['status', 'last_location_update']),
            models.Index(fields=['service_area', 'status']),
            models.Index(fields=['average_rating', 'status']),
        ]

    def __str__(self):
        return f"{self.driver.get_full_name()} - {self.get_status_display()}"

    def is_available_for_rides(self):
        """Check if driver is currently available for new rides"""
        return self.status == self.AvailabilityStatus.ONLINE

    def is_within_service_area(self, lat, lng):
        """Check if given coordinates are within driver's service area"""
        if not self.current_location:
            return False
            
        # Simple distance-based check (can be enhanced with polygon checks)
        from django.contrib.gis.geos import Point
        from django.contrib.gis.db.models.functions import Distance
        
        point = Point(lng, lat, srid=4326)
        distance_km = self.current_location.distance(point) * 111  # Rough conversion to km
        
        return distance_km <= float(self.max_distance_km)

    def update_location(self, lat, lng, address=None):
        """Update driver's current location"""
        from django.contrib.gis.geos import Point
        
        self.current_location = Point(lng, lat, srid=4326)
        if address:
            self.current_address = address
        self.last_location_update = models.timezone.now()
        self.save(update_fields=['current_location', 'current_address', 'last_location_update'])

    def go_online(self):
        """Set driver status to online"""
        from django.utils import timezone
        
        self.status = self.AvailabilityStatus.ONLINE
        self.last_online_at = timezone.now()
        self.save(update_fields=['status', 'last_online_at'])

    def go_offline(self):
        """Set driver status to offline"""
        from django.utils import timezone
        
        self.status = self.AvailabilityStatus.OFFLINE
        self.last_offline_at = timezone.now()
        self.save(update_fields=['status', 'last_offline_at'])

    def set_busy(self):
        """Set driver status to busy (on a ride)"""
        self.status = self.AvailabilityStatus.BUSY
        self.save(update_fields=['status'])

    def get_estimated_arrival_time(self, pickup_lat, pickup_lng):
        """Estimate arrival time to pickup location"""
        if not self.current_location:
            return None
            
        from django.contrib.gis.geos import Point
        from django.contrib.gis.db.models.functions import Distance
        
        pickup_point = Point(pickup_lng, pickup_lat, srid=4326)
        distance_km = self.current_location.distance(pickup_point) * 111
        
        # Rough estimation: 30 km/h average speed in city
        estimated_minutes = (distance_km / 30) * 60
        
        from django.utils import timezone
        return timezone.now() + timezone.timedelta(minutes=estimated_minutes)

    @property
    def is_planned_route_active(self):
        """Check if driver has an active planned route"""
        if not self.planned_destination_lat or not self.planned_departure_time:
            return False
            
        from django.utils import timezone
        now = timezone.now()
        
        # Check if current time is within planned route timeframe
        if self.planned_arrival_time:
            return self.planned_departure_time <= now <= self.planned_arrival_time
        else:
            # If no arrival time, assume route is active for 2 hours after departure
            route_end = self.planned_departure_time + timezone.timedelta(hours=2)
            return self.planned_departure_time <= now <= route_end