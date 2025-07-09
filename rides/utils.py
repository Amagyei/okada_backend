# rides/utils.py
import requests
import os
from decimal import Decimal, ROUND_HALF_UP
from math import radians, sin, cos, sqrt, atan2
from django.conf import settings
from django.core.exceptions import ImproperlyConfigured

# --- Fare Calculation Logic ---

def calculate_haversine_distance(lat1, lon1, lat2, lon2):
    """
    Calculates the great-circle distance between two points
    on the earth (specified in decimal degrees) in kilometers.
    """
    # Ensure input are floats
    lat1, lon1, lat2, lon2 = map(float, [lat1, lon1, lat2, lon2])

    # Convert decimal degrees to radians
    lat1_rad, lon1_rad, lat2_rad, lon2_rad = map(radians, [lat1, lon1, lat2, lon2])

    # Haversine formula
    dlon = lon2_rad - lon1_rad
    dlat = lat2_rad - lat1_rad
    a = sin(dlat / 2)**2 + cos(lat1_rad) * cos(lat2_rad) * sin(dlon / 2)**2
    c = 2 * atan2(sqrt(a), sqrt(1 - a))

    # Radius of earth in kilometers. Use 6371 for kilometers.
    R = 6371.0
    distance = R * c
    return distance

def get_estimated_fare(pickup_lat, pickup_lng, dest_lat, dest_lng):
    """
    Calculates the estimated ride fare.
    Attempts to use Google Directions API for distance and duration.
    Falls back to Haversine distance if API fails or key is missing.
    Uses fare parameters defined in Django settings.
    """
    print(f"[Fare Calc] Estimating fare for: Pickup({pickup_lat},{pickup_lng}) -> Dest({dest_lat},{dest_lng})")

    try:
        # Get fare parameters from settings (provide defaults if missing for safety)
        base_fare = getattr(settings, 'RIDE_BASE_FARE', Decimal('5.00'))
        price_per_km = getattr(settings, 'RIDE_PRICE_PER_KM', Decimal('1.50'))
        price_per_minute = getattr(settings, 'RIDE_PRICE_PER_MINUTE', Decimal('0.20')) # Optional per-minute charge
        min_fare = getattr(settings, 'RIDE_MINIMUM_FARE', Decimal('10.00'))
        google_api_key = os.environ.get('GOOGLE_MAPS_API_KEY') # Get key from env

        distance_km = Decimal('0.0')
        duration_minutes = Decimal('0.0') # Initialize duration

        if not google_api_key:
            print("[Fare Calc] WARNING: GOOGLE_MAPS_API_KEY not found in environment. Using Haversine distance only.")
            # Fallback to simple distance calculation
            distance_km = Decimal(str(calculate_haversine_distance(pickup_lat, pickup_lng, dest_lat, dest_lng)))
            print(f"[Fare Calc] Using Haversine distance: {distance_km:.2f} km")
            # Estimate duration based on distance (e.g., average speed of 25 km/h -> 2.4 min/km)
            duration_minutes = distance_km * Decimal('2.4') # Very rough estimate
            print(f"[Fare Calc] Estimated duration (rough): {duration_minutes:.1f} min")

        else:
            # --- Call Google Directions API ---
            print(f"[Fare Calc] Calling Directions API...")
            # Consider 'mode=bicycling' or 'mode=driving' based on Okada behavior
            # Driving mode often gives better time estimates including traffic
            directions_url = (
                f"https://maps.googleapis.com/maps/api/directions/json?"
                f"origin={pickup_lat},{pickup_lng}"
                f"&destination={dest_lat},{dest_lng}"
                f"&key={google_api_key}"
                f"&mode=driving" # Or bicycling
                # Optional: Add traffic_model=best_guess for better time estimates
                # Optional: Add departure_time=now
            )

            try:
                response = requests.get(directions_url, timeout=10) # 10 second timeout
                response.raise_for_status() # Raise HTTPError for bad responses (4xx or 5xx)
                data = response.json()

                if data['status'] == 'OK' and data.get('routes'):
                    # Use the first route suggested
                    route = data['routes'][0]
                    if route.get('legs'):
                        leg = route['legs'][0]
                        distance_meters = leg.get('distance', {}).get('value', 0)
                        duration_seconds = leg.get('duration', {}).get('value', 0) # Duration in seconds

                        distance_km = Decimal(str(distance_meters / 1000.0))
                        duration_minutes = Decimal(str(duration_seconds / 60.0))

                        print(f"[Fare Calc] Directions API distance: {distance_km:.2f} km, duration: {duration_minutes:.1f} min")
                    else:
                         print("[Fare Calc] Directions API OK but no legs found in route. Falling back.")
                         raise ValueError("No route legs found") # Trigger fallback

                else:
                    print(f"[Fare Calc] Directions API Error: {data.get('status')} - {data.get('error_message', '')}. Falling back.")
                    raise ValueError(f"Directions API status: {data.get('status')}") # Trigger fallback

            except (requests.exceptions.RequestException, ValueError, Exception) as e:
                print(f"[Fare Calc] Error calling/parsing Directions API: {e}. Falling back to Haversine.")
                # Fallback to simple distance calculation on API error
                distance_km = Decimal(str(calculate_haversine_distance(pickup_lat, pickup_lng, dest_lat, dest_lng)))
                duration_minutes = distance_km * Decimal('2.4') # Rough estimate
                print(f"[Fare Calc] Using Haversine distance: {distance_km:.2f} km, Est. duration: {duration_minutes:.1f} min")
            # --- End Google Directions API Call ---

        # Calculate fare based on distance and duration
        # Ensure components are Decimal
        distance_fare = distance_km * price_per_km
        duration_fare = duration_minutes * price_per_minute # Use this if charging per minute

        # Choose formula: Base + Distance + Duration OR Base + Distance only
        estimated_fare = base_fare + distance_fare + duration_fare
        # Or if only distance based: estimated_fare = base_fare + distance_fare

        print(f"[Fare Calc] Calculated Fare Components: Base={base_fare}, Dist={distance_fare:.2f}, Dur={duration_fare:.2f} -> Est.={estimated_fare:.2f}")

        # Apply minimum fare
        final_fare = max(estimated_fare, min_fare)

        # Quantize to 2 decimal places (like currency)
        quantized_fare = final_fare.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        print(f"[Fare Calc] Min Fare Applied ({min_fare}): {final_fare > estimated_fare}, Final Quantized Fare: {quantized_fare}")
        return quantized_fare

    except AttributeError as e:
        # This happens if settings are missing
        print(f"ERROR: Missing fare parameter in Django settings: {e}")
        raise ImproperlyConfigured(f"Missing ride fare parameter in settings: {e}")
    except Exception as e:
        print(f"Unexpected error during fare calculation: {e}")
        # Return None or a default value like minimum fare in case of unexpected errors
        return getattr(settings, 'RIDE_MINIMUM_FARE', Decimal('10.00'))

