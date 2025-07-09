from django.contrib import admin
from .models import Ride,  RideRating, SavedLocation, DriverAvailability

@admin.register(Ride)
class RideAdmin(admin.ModelAdmin):
    list_display = ('id', 'rider', 'driver', 'status', 'payment_status', 'total_fare')
    search_fields = ('rider__username', 'driver__username')
    list_filter = ('status', 'payment_status')


@admin.register(RideRating)
class RideRatingAdmin(admin.ModelAdmin):
    list_display = ('ride', 'rating', 'created_at')
    search_fields = ('ride__id',)

@admin.register(SavedLocation)
class SavedLocationAdmin(admin.ModelAdmin):
    list_display = ('name', 'user', 'location_type', 'is_default', 'created_at')
    search_fields = ('user__username', 'name')


@admin.register(DriverAvailability)
class DriverAvailabilityAdmin(admin.ModelAdmin):
    list_display = ('driver', 'status', 'service_area', 'average_rating', 'total_rides_completed', 'last_location_update')
    list_filter = ('status', 'service_area', 'is_available_24_7')
    search_fields = ('driver__username', 'driver__first_name', 'driver__last_name')
    readonly_fields = ('last_location_update', 'last_online_at', 'last_offline_at', 'created_at', 'updated_at')
    
    fieldsets = (
        ('Driver Information', {
            'fields': ('driver', 'status', 'average_rating', 'total_rides_completed')
        }),
        ('Location & Service Area', {
            'fields': ('current_location', 'current_address', 'service_area', 'custom_service_area', 'max_distance_km')
        }),
        ('Planned Route', {
            'fields': ('planned_destination_lat', 'planned_destination_lng', 'planned_destination_address', 
                      'planned_departure_time', 'planned_arrival_time'),
            'classes': ('collapse',)
        }),
        ('Preferences', {
            'fields': ('is_available_24_7', 'preferred_start_time', 'preferred_end_time', 
                      'preferred_ride_types', 'minimum_fare_preference'),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('last_location_update', 'last_online_at', 'last_offline_at', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def get_queryset(self, request):
        """Optimize queryset with select_related for better performance."""
        return super().get_queryset(request).select_related('driver')
