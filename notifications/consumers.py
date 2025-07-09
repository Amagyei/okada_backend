# notifications/consumers.py
import json
from channels.generic.websocket import AsyncJsonWebsocketConsumer
from channels.db import database_sync_to_async
from rides.models import Ride
from users.models import User


class NotificationConsumer(AsyncJsonWebsocketConsumer):
    async def connect(self):
        print("[🔌 NotificationConsumer] ===== WEBSOCKET CONNECTION ATTEMPT =====")
        print("[🔌 NotificationConsumer] connect() scope.user=", self.scope.get("user"))
        self.user = self.scope.get("user")
        if self.user is None or self.user.is_anonymous:
            print("[🔌 NotificationConsumer] ERROR: User is anonymous or None, closing connection")
            await self.close()
            return
        
        print("[🔌 NotificationConsumer] User authenticated: ${self.user.id} (${self.user.user_type})")
        
        # if this is a driver, add to the global drivers group:
        if self.user.user_type == 'driver':
            print("[🔌 NotificationConsumer] Adding driver ${self.user.id} to 'drivers' group")
            await self.channel_layer.group_add("drivers", self.channel_name)
            print("[🔌 NotificationConsumer] Driver ${self.user.id} added to 'drivers' group successfully")
        else:
            print("[🔌 NotificationConsumer] User ${self.user.id} is not a driver (${self.user.user_type})")

        self.group_name = f"user_{self.user.id}"
        print("[🔌 NotificationConsumer] Adding user to personal group: ${self.group_name}")
        await self.channel_layer.group_add(self.group_name, self.channel_name)
        await self.accept()
        print("[🔌 NotificationConsumer] ===== WEBSOCKET CONNECTION ACCEPTED =====")

    async def disconnect(self, close_code):
        # Remove the user from their group if they were added
        if hasattr(self, 'group_name') and self.group_name:
            await self.channel_layer.group_discard(self.group_name, self.channel_name)
        
        if self.user.is_authenticated and self.user.user_type == 'driver':
            await self.channel_layer.group_discard("drivers", self.channel_name)

    async def receive_json(self, content):
        message_type = content.get("type")
        if message_type == "update_location":
            await self.handle_location_update(content)
        else:
            print(f"[🔌 NotificationConsumer] Unknown message type: {message_type}")

    async def handle_location_update(self, event):
        """
        Handles receiving a location update from a driver during an active ride.
        Updates the driver's location in the DB and forwards it to the rider.
        """
        if not self.user.is_authenticated or self.user.user_type != 'driver':
            return

        location = event.get("location")
        if not location or "lat" not in location or "lng" not in location:
            return

        # Update driver's location in the database asynchronously
        await self.update_driver_location(self.user, location)

        # Find the active ride for this driver to notify the correct rider
        ride = await self.get_active_ride_for_driver(self.user)

        if ride and ride.rider:
            # Forward the location to the rider's specific group
            rider_group_name = f"user_{ride.rider.id}"
            await self.channel_layer.group_send(
                rider_group_name,
                {
                    "type": "send_notification",  # This calls the method below
                    "payload": {
                        "type": "driver_location_update",
                        "location": {
                            "lat": location["lat"],
                            "lng": location["lng"],
                        },
                        "ride_id": str(ride.id),
                    },
                },
            )

    @database_sync_to_async
    def update_driver_location(self, driver, location):
        driver.current_location = location
        driver.save(update_fields=['current_location'])

    @database_sync_to_async
    def get_active_ride_for_driver(self, driver):
        # Assumes Ride model has a StatusChoices enum with these values
        return Ride.objects.filter(
            driver=driver,
            status__in=[Ride.StatusChoices.ACCEPTED, Ride.StatusChoices.IN_PROGRESS]
        ).select_related('rider').first()

    async def send_notification(self, event):
        print("[📨 NotificationConsumer] send_notification payload=", event.get("payload"))
        await self.send_json(event.get("payload", {}))
