from django.contrib import admin
from .models import Ride,  RideRating, SavedLocation

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