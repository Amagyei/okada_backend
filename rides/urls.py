# rides/urls.py

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views # Import views from the current directory

# Create a router and register our viewsets with it.
router = DefaultRouter()
router.register(r'', views.RideViewSet, basename='ride')
router.register(r'saved-locations', views.SavedLocationViewSet, basename='savedlocation')
router.register(r'driver-availability', views.DriverAvailabilityViewSet, basename='driveravailability')
router.register(r'driver-search', views.DriverSearchViewSet, basename='driversearch')
# Note: RideRatingViewSet is not registered as its functionality is in RideViewSet actions

app_name = 'rides'

# The API URLs are now determined automatically by the router.
urlpatterns = [
    path('', include(router.urls)),
]

# The router automatically generates URLs like:
# /api/rides/                           (GET: list, POST: create)
# /api/rides/{pk}/                        (GET: retrieve)
# /api/rides/{pk}/accept_ride/          (POST: accept_ride action)
# /api/rides/{pk}/update_ride_status/   (POST: update_ride_status action)
# /api/rides/{pk}/complete_trip/      (POST: complete_trip action)
# /api/rides/{pk}/cancel_ride/          (POST: cancel_ride action)
# /api/rides/{pk}/rate_ride/            (POST: rate_ride action)
#
# /api/saved-locations/                 (GET: list, POST: create)
# /api/saved-locations/{pk}/            (GET: retrieve, PUT: update, PATCH: partial_update, DELETE: destroy)
#
# /api/driver-availability/             (GET: list, POST: create)
# /api/driver-availability/{pk}/        (GET: retrieve, PUT: update, PATCH: partial_update, DELETE: destroy)
# /api/driver-availability/go_online/   (POST: go_online action)
# /api/driver-availability/go_offline/  (POST: go_offline action)
# /api/driver-availability/update_location/ (POST: update_location action)
# /api/driver-availability/set_planned_route/ (POST: set_planned_route action)
#
# /api/driver-search/find_nearby_drivers/ (POST: find_nearby_drivers action)
# /api/driver-search/find_drivers_on_route/ (POST: find_drivers_on_route action)