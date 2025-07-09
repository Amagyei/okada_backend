from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase, APIClient
from django.contrib.auth import get_user_model
from .models import Driver

User = get_user_model()

class UserTests(APITestCase):
    def setUp(self):
        self.client = APIClient()
        self.user_data = {
            'username': 'testuser',
            'email': 'test@example.com',
            'password': 'testpass123',
            'phone_number': '0241234567',
            'full_name': 'Test User'
        }
        self.user = User.objects.create_user(**self.user_data)
        self.client.force_authenticate(user=self.user)

    def test_user_registration(self):
        url = reverse('user-list')
        data = {
            'username': 'newuser',
            'email': 'new@example.com',
            'password': 'newpass123',
            'phone_number': '0247654321',
            'full_name': 'New User'
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(User.objects.count(), 2)
        self.assertEqual(User.objects.get(username='newuser').email, 'new@example.com')

    def test_user_login(self):
        url = reverse('token_obtain_pair')
        data = {
            'username': 'testuser',
            'password': 'testpass123'
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('access', response.data)
        self.assertIn('refresh', response.data)

    def test_user_profile(self):
        url = reverse('user-me')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['username'], 'testuser')
        self.assertEqual(response.data['email'], 'test@example.com')

    def test_user_update(self):
        url = reverse('user-detail', args=[self.user.id])
        data = {
            'full_name': 'Updated Name',
            'phone_number': '0249876543'
        }
        response = self.client.patch(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.user.refresh_from_db()
        self.assertEqual(self.user.full_name, 'Updated Name')
        self.assertEqual(self.user.phone_number, '0249876543')

class DriverTests(APITestCase):
    def setUp(self):
        self.client = APIClient()
        self.user_data = {
            'username': 'driveruser',
            'email': 'driver@example.com',
            'password': 'driverpass123',
            'phone_number': '0241234567',
            'full_name': 'Driver User',
            'is_driver': True
        }
        self.user = User.objects.create_user(**self.user_data)
        self.driver_data = {
            'user': self.user,
            'vehicle_type': 'motorcycle',
            'license_number': 'DL123456',
            'vehicle_make': 'Honda',
            'vehicle_model': 'CB125F',
            'vehicle_year': '2020',
            'vehicle_color': 'Black',
            'vehicle_registration': 'GR1234AB'
        }
        self.driver = Driver.objects.create(**self.driver_data)
        self.client.force_authenticate(user=self.user)

    def test_driver_registration(self):
        url = reverse('driver-list')
        data = {
            'vehicle_type': 'motorcycle',
            'license_number': 'DL789012',
            'vehicle_make': 'Yamaha',
            'vehicle_model': 'YZF-R3',
            'vehicle_year': '2021',
            'vehicle_color': 'Blue',
            'vehicle_registration': 'GR5678CD'
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Driver.objects.count(), 2)
        self.assertEqual(Driver.objects.get(license_number='DL789012').vehicle_make, 'Yamaha')

    def test_driver_profile(self):
        url = reverse('driver-my_profile')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['license_number'], 'DL123456')
        self.assertEqual(response.data['vehicle_make'], 'Honda')

    def test_driver_update(self):
        url = reverse('driver-detail', args=[self.driver.id])
        data = {
            'vehicle_color': 'Red',
            'vehicle_registration': 'GR9012EF'
        }
        response = self.client.patch(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.driver.refresh_from_db()
        self.assertEqual(self.driver.vehicle_color, 'Red')
        self.assertEqual(self.driver.vehicle_registration, 'GR9012EF')

    def test_driver_verification(self):
        url = reverse('driver-verify', args=[self.driver.id])
        response = self.client.post(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.driver.refresh_from_db()
        self.assertTrue(self.driver.is_verified)

    def test_driver_availability_toggle(self):
        url = reverse('driver-toggle_availability', args=[self.driver.id])
        response = self.client.post(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.driver.refresh_from_db()
        self.assertFalse(self.driver.is_available)

        response = self.client.post(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.driver.refresh_from_db()
        self.assertTrue(self.driver.is_available) 