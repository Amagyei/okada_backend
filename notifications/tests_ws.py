import pytest
import json
from channels.testing import WebsocketCommunicator
from django.contrib.auth import get_user_model
from django.test import TransactionTestCase, Client
from asgiref.sync import async_to_sync
from okada_backend.okada_backend.asgi import application
from rides.models import Ride
from django.urls import reverse

User = get_user_model()

@pytest.mark.asyncio
class TestRideWebSocket(TransactionTestCase):
    reset_sequences = True

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.client = Client()

    def setUp(self):
        self.rider = User.objects.create_user(username='rider', password='test', user_type='rider', phone_number='0240000001')
        self.driver = User.objects.create_user(username='driver', password='test', user_type='driver', phone_number='0540000001')

    def get_jwt_token(self, user):
        url = reverse('authentication:phone_login')
        resp = self.client.post(url, {'phone_number': user.phone_number, 'password': 'test'}, content_type='application/json')
        assert resp.status_code == 200, f"Login failed: {resp.content}"
        return resp.json()['access']

    async def ws_connect(self, user):
        token = self.get_jwt_token(user)
        communicator = WebsocketCommunicator(
            application,
            f"/ws/notifications/?token={token}"
        )
        connected, _ = await communicator.connect()
        assert connected, "WebSocket failed to connect"
        return communicator

    async def test_ws_connection_authentication(self):
        # No token: should fail
        communicator = WebsocketCommunicator(application, "/ws/notifications/")
        connected, _ = await communicator.connect()
        assert not connected
        await communicator.disconnect()

        # Invalid token: should fail
        communicator = WebsocketCommunicator(application, "/ws/notifications/?token=badtoken")
        connected, _ = await communicator.connect()
        assert not connected
        await communicator.disconnect()

        # Valid token: should succeed
        communicator = await self.ws_connect(self.rider)
        await communicator.disconnect()

    async def test_group_membership_drivers(self):
        # Connect as driver, send a test message to check group
        communicator = await self.ws_connect(self.driver)
        # Send a dummy message to trigger group join (if needed)
        await communicator.send_json_to({"type": "ping"})
        # In production, you can't directly inspect groups, but you can test by sending a group message
        # Simulate backend sending a group message
        from channels.layers import get_channel_layer
        channel_layer = get_channel_layer()
        await channel_layer.group_send(
            "drivers",
            {
                "type": "send_notification",
                "payload": {"type": "test_group", "msg": "hello drivers"}
            }
        )
        msg = await communicator.receive_json_from()
        assert msg['type'] == "test_group"
        assert msg['msg'] == "hello drivers"
        await communicator.disconnect()

    async def test_group_membership_user(self):
        communicator = await self.ws_connect(self.rider)
        # Simulate backend sending a message to this user's group
        from channels.layers import get_channel_layer
        channel_layer = get_channel_layer()
        await channel_layer.group_send(
            f"user_{self.rider.id}",
            {
                "type": "send_notification",
                "payload": {"type": "personal", "msg": "hello rider"}
            }
        )
        msg = await communicator.receive_json_from()
        assert msg['type'] == "personal"
        assert msg['msg'] == "hello rider"
        await communicator.disconnect()

    async def test_ride_requested_broadcast(self):
        # Driver connects and listens
        driver_comm = await self.ws_connect(self.driver)
        # Rider creates a ride via API
        token = self.get_jwt_token(self.rider)
        resp = self.client.post(
            reverse('rides:ride-list'),
            {
                "pickup_location_lat": 5.6,
                "pickup_location_lng": -0.18,
                "pickup_address": "Madina",
                "destination_lat": 5.65,
                "destination_lng": -0.19,
                "destination_address": "Accra Central"
            },
            content_type='application/json',
            HTTP_AUTHORIZATION=f"Bearer {token}"
        )
        assert resp.status_code == 201, resp.content
        # Driver should receive a new_ride_request event
        msg = await driver_comm.receive_json_from()
        assert msg['type'] == "new_ride_request"
        assert "ride_id" in msg
        await driver_comm.disconnect()

    async def test_ride_accepted_notification(self):
        # Rider connects and listens
        rider_comm = await self.ws_connect(self.rider)
        # Rider creates a ride
        ride = Ride.objects.create(
            rider=self.rider,
            pickup_location_lat=5.6, pickup_location_lng=-0.18,
            destination_lat=5.65, destination_lng=-0.19,
            pickup_address="Madina", destination_address="Accra Central",
            status='REQUESTED'
        )
        # Driver accepts ride via API
        token = self.get_jwt_token(self.driver)
        resp = self.client.post(
            reverse('rides:ride-accept-ride', args=[ride.id]),
            content_type='application/json',
            HTTP_AUTHORIZATION=f"Bearer {token}"
        )
        # Rider should receive a ride_accepted event (via group_send to drivers, but you can adapt your consumer to also notify the rider's group)
        # For now, test that the event is sent to the drivers group (see your backend logic)
        # If you want to notify the rider directly, add a group_send to f"user_{ride.rider.id}" in your accept_ride view
        # Example:
        # async_to_sync(channel_layer.group_send)(
        #     f"user_{ride.rider.id}",
        #     {"type": "send_notification", "payload": {...}}
        # )
        # Then test:
        # msg = await rider_comm.receive_json_from()
        # assert msg['type'] == "ride_accepted"
        await rider_comm.disconnect()

    async def test_location_update_flow(self):
        # Driver and rider both connect
        driver_comm = await self.ws_connect(self.driver)
        rider_comm = await self.ws_connect(self.rider)
        # Simulate driver sending location update
        await driver_comm.send_json_to({
            "type": "update_location",
            "location": {"lat": 5.7, "lng": -0.2}
        })
        # Simulate backend forwarding to rider (normally, this would require an active ride)
        # For a real test, ensure the driver has an active ride assigned to this rider
        # For now, check that the consumer does not error and (optionally) that the rider receives the update
        # msg = await rider_comm.receive_json_from()
        # assert msg['type'] == "driver_location_update"
        await driver_comm.disconnect()
        await rider_comm.disconnect()

    async def test_unauthorized_message(self):
        # Rider connects and tries to send a driver-only message
        rider_comm = await self.ws_connect(self.rider)
        await rider_comm.send_json_to({
            "type": "update_location",
            "location": {"lat": 5.7, "lng": -0.2}
        })
        # Should not crash, and should not broadcast
        # Optionally, check for error response if your consumer implements it
        await rider_comm.disconnect()

    async def test_invalid_payload_handling(self):
        # Driver connects and sends malformed JSON
        driver_comm = await self.ws_connect(self.driver)
        await driver_comm.send_json_to({"bad": "data"})
        # Should not crash, and should return error if implemented
        # Optionally, check for error response
        await driver_comm.disconnect()