# rides/models.py

from django.db import models
from django.conf import settings # Use settings.AUTH_USER_MODEL
from django.utils.translation import gettext_lazy as _
from django.core.validators import MinValueValidator, MaxValueValidator

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
        max_length=25, # Increased length for new choices
        choices=StatusChoices.choices,
        default=StatusChoices.REQUESTED,
        db_index=True # Index status for faster filtering
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