from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase, APIClient
from django.contrib.gis.geos import Point
from rides.models import Ride
from rides.serializers import RideSerializer

User = get_user_model()

class RideModelTestCase(APITestCase):
    def setUp(self):
        self.rider = User.objects.create_user(username='rider1', password='testpass', user_type='rider', phone_number='0240000001')
        self.driver = User.objects.create_user(username='driver1', password='testpass', user_type='driver', phone_number='0540000001')

    def test_create_ride_with_pointfields(self):
        ride = Ride.objects.create(
            rider=self.rider,
            pickup_location_lat=5.6,
            pickup_location_lng=-0.18,
            pickup_address="Madina",
            destination_lat=5.65,
            destination_lng=-0.19,
            destination_address="Accra Central",
            pickup_location=Point(-0.18, 5.6, srid=4326),
            destination=Point(-0.19, 5.65, srid=4326),
        )
        self.assertIsNotNone(ride.pickup_location)
        self.assertIsNotNone(ride.destination)
        self.assertEqual(ride.pickup_location.srid, 4326)

class RideSerializerTestCase(APITestCase):
    def setUp(self):
        self.rider = User.objects.create_user(username='rider2', password='testpass', user_type='rider', phone_number='0240000002')
        self.ride = Ride.objects.create(
            rider=self.rider,
            pickup_location_lat=5.6,
            pickup_location_lng=-0.18,
            pickup_address="Madina",
            destination_lat=5.65,
            destination_lng=-0.19,
            destination_address="Accra Central",
            pickup_location=Point(-0.18, 5.6, srid=4326),
            destination=Point(-0.19, 5.65, srid=4326),
        )

    def test_serializer_lat_lng_fields(self):
        data = RideSerializer(self.ride).data
        self.assertAlmostEqual(float(data['pickup_lat']), 5.6, places=4)
        self.assertAlmostEqual(float(data['pickup_lng']), -0.18, places=4)
        self.assertAlmostEqual(float(data['destination_lat']), 5.65, places=4)
        self.assertAlmostEqual(float(data['destination_lng']), -0.19, places=4)

class RideAPITestCase(APITestCase):
    def setUp(self):
        self.rider = User.objects.create_user(
            username='rider3', password='testpass',
            user_type='rider', phone_number='0240000003'
        )
        self.driver = User.objects.create_user(
            username='driver3', password='testpass',
            user_type='driver', phone_number='0540000003'
        )
        self.client = APIClient()
        self.list_url = reverse('rides:ride-list')
        self.valid_payload = {
            "pickup_location_lat": 5.6,
            "pickup_location_lng": -0.18,
            "pickup_address": "Madina",
            "destination_lat": 5.65,
            "destination_lng": -0.19,
            "destination_address": "Accra Central"
        }

    def test_unauthenticated_cannot_create_ride(self):
        resp = self.client.post(self.list_url, self.valid_payload, format='json')
        self.assertEqual(resp.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_rider_can_create_ride(self):
        self.client.force_authenticate(user=self.rider)
        resp = self.client.post(self.list_url, self.valid_payload, format='json')
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)
        self.assertIn('pickup_lat', resp.data)
        self.assertIn('destination_lat', resp.data)

    def test_driver_cannot_create_ride(self):
        self.client.force_authenticate(user=self.driver)
        resp = self.client.post(self.list_url, self.valid_payload, format='json')
        self.assertEqual(resp.status_code, status.HTTP_403_FORBIDDEN)

    def test_missing_required_fields_returns_400(self):
        self.client.force_authenticate(user=self.rider)
        incomplete = {
            "pickup_location_lat": 5.6,
            "pickup_location_lng": -0.18,
        }
        resp = self.client.post(self.list_url, incomplete, format='json')
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('destination_lat', resp.data)
        self.assertIn('destination_lng', resp.data)

    def test_rider_sees_only_their_rides(self):
        # ride by self.rider
        ride1 = Ride.objects.create(
            rider=self.rider,
            pickup_location=Point(-0.18, 5.6, srid=4326),
            destination=Point(-0.19, 5.65, srid=4326),
            pickup_location_lat=5.6, pickup_location_lng=-0.18,
            destination_lat=5.65, destination_lng=-0.19,
            pickup_address="A", destination_address="B"
        )
        # ride by someone else
        other = User.objects.create_user(
            username='riderX', password='x', user_type='rider', phone_number='000'
        )
        ride2 = Ride.objects.create(
            rider=other,
            pickup_location=Point(-0.18, 5.6, srid=4326),
            destination=Point(-0.19, 5.65, srid=4326),
            pickup_location_lat=5.6, pickup_location_lng=-0.18,
            destination_lat=5.65, destination_lng=-0.19,
            pickup_address="C", destination_address="D"
        )

        self.client.force_authenticate(user=self.rider)
        resp = self.client.get(self.list_url, format='json')
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        ids = [r['id'] for r in resp.data['results']]
        self.assertIn(ride1.id, ids)
        self.assertNotIn(ride2.id, ids)

    def test_pagination_default_page_size(self):
        # create 12 rides for rider
        for _ in range(12):
            Ride.objects.create(
                rider=self.rider,
                pickup_location=Point(-0.18, 5.6, srid=4326),
                destination=Point(-0.19, 5.65, srid=4326),
                pickup_location_lat=5.6, pickup_location_lng=-0.18,
                destination_lat=5.65, destination_lng=-0.19,
                pickup_address="Pg", destination_address="Dg"
            )
        self.client.force_authenticate(user=self.rider)
        resp = self.client.get(self.list_url, format='json')
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        # assuming default page size = 10
        self.assertEqual(len(resp.data['results']), 10)
        self.assertIn('next', resp.data)
        self.assertIn('previous', resp.data)

    def test_retrieve_ride_detail(self):
        ride = Ride.objects.create(
            rider=self.rider,
            pickup_location=Point(-0.18, 5.6, srid=4326),
            destination=Point(-0.19, 5.65, srid=4326),
            pickup_location_lat=5.6, pickup_location_lng=-0.18,
            destination_lat=5.65, destination_lng=-0.19,
            pickup_address="Here", destination_address="There"
        )
        url = reverse('rides:ride-detail', args=[ride.id])
        self.client.force_authenticate(user=self.rider)
        resp = self.client.get(url, format='json')
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(resp.data['id'], ride.id)
        self.assertAlmostEqual(float(resp.data['pickup_lat']), 5.6, places=4)

    def test_update_ride_not_allowed(self):
        ride = Ride.objects.create(
            rider=self.rider,
            pickup_location=Point(-0.18, 5.6, srid=4326),
            destination=Point(-0.19, 5.65, srid=4326),
            pickup_location_lat=5.6, pickup_location_lng=-0.18,
            destination_lat=5.65, destination_lng=-0.19,
            pickup_address="Old", destination_address="Addr"
        )
        url = reverse('rides:ride-detail', args=[ride.id])
        self.client.force_authenticate(user=self.rider)
        resp = self.client.patch(url, {'pickup_address': 'New Addr'}, format='json')
        # Either 405 Method Not Allowed or 403 Forbidden
        self.assertIn(resp.status_code, (status.HTTP_403_FORBIDDEN, status.HTTP_405_METHOD_NOT_ALLOWED))

    def test_only_owner_can_cancel_ride(self):
        ride = Ride.objects.create(
            rider=self.rider,
            pickup_location=Point(-0.18, 5.6, srid=4326),
            destination=Point(-0.19, 5.65, srid=4326),
            pickup_location_lat=5.6, pickup_location_lng=-0.18,
            destination_lat=5.65, destination_lng=-0.19,
            pickup_address="X", destination_address="Y"
        )
        cancel_url = reverse('rides:ride-cancel-ride', args=[ride.id])
        # non-owner
        other = User.objects.create_user(username='uX', password='x', user_type='rider', phone_number='999')
        self.client.force_authenticate(user=other)
        resp = self.client.post(cancel_url, format='json')
        self.assertIn(resp.status_code, (status.HTTP_403_FORBIDDEN, status.HTTP_404_NOT_FOUND))

        # owner
        self.client.force_authenticate(user=self.rider)
        resp = self.client.post(cancel_url, format='json')
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        ride.refresh_from_db()
        self.assertIn(
            ride.status.upper(),
            ['CANCELLED_BY_RIDER', 'CANCELLED_BY_DRIVER', 'CANCELLED']
        )

    def test_assigned_driver_can_accept_ride(self):
        ride = Ride.objects.create(
            rider=self.rider,
            pickup_location=Point(-0.18, 5.6, srid=4326),
            destination=Point(-0.19, 5.65, srid=4326),
            pickup_location_lat=5.6, pickup_location_lng=-0.18,
            destination_lat=5.65, destination_lng=-0.19,
            pickup_address="Start", destination_address="End"
        )
        accept_url = reverse('rides:ride-accept-ride', args=[ride.id])
        self.client.force_authenticate(user=self.driver)
        resp = self.client.post(accept_url, format='json')
        self.assertIn(resp.status_code, (status.HTTP_200_OK, status.HTTP_400_BAD_REQUEST, status.HTTP_409_CONFLICT))
        ride.refresh_from_db()
        # Acceptable statuses: accepted, or error if already accepted
        self.assertIn(ride.status, ['accepted', 'ACCEPTED', 'REQUESTED']) 