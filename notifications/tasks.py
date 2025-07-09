# notifications/tasks.py
from celery import shared_task
from threading import Lock
from django.conf import settings
from django.contrib.auth import get_user_model
import firebase_admin.messaging
from datetime import timedelta
from django.utils import timezone
from rides.models import Ride
from firebase_admin import messaging
from firebase_admin.exceptions import FirebaseError
import logging

User = get_user_model()

_sent_notifications = set()
_sent_lock = Lock()

logger = logging.getLogger(__name__)

@shared_task(bind=True, max_retries=3, default_retry_delay=60) # bind=True to access self for retries
def send_fcm_notification_task(self, user_id, title, body, data_payload=None):
    """
    Celery task to send an FCM notification to a specific user.
    :param user_id: ID of the User to send the notification to.
    :param title: Title of the notification.
    :param body: Body text of the notification.
    :param data_payload: Optional dictionary for custom data.
    """
    dedupe_key = f"{user_id}:{data_payload.get('ride_id','')}-{data_payload.get('type','')}"
    with _sent_lock:
        if dedupe_key in _sent_notifications:
            print(f"[FCM Task] Duplicate notification {dedupe_key}, skipping.")
            return
        _sent_notifications.add(dedupe_key)

    try:
        user = User.objects.get(id=user_id)
        if not user.fcm_token:
            print(f"[FCM Task] User {user_id} has no FCM token. Notification not sent.")
            return f"User {user_id} has no FCM token."

        message_data = {
            'click_action': 'FLUTTER_NOTIFICATION_CLICK', # Standard for Flutter
            'status': 'done', # Example custom data
            # Add any other key-value pairs your app needs to handle the notification
        }
        if data_payload:
            message_data.update(data_payload)
        
        print(f"[FCM Task] Preparing to send to token: {user.fcm_token[:20]}... for user {user_id}")
        print(f"[FCM Task] Title: {title}, Body: {body}, Data: {message_data}")

        # Common fields for both Android and APNS
        common_notification = firebase_admin.messaging.Notification(title=title, body=body)

        message = firebase_admin.messaging.Message(
            notification=common_notification,
            token=user.fcm_token,
            data=message_data,
            # --- Android Specific Configuration (Optional) ---
            # android=firebase_admin.messaging.AndroidConfig(
            #     priority='high', # 'normal' or 'high'
            #     notification=firebase_admin.messaging.AndroidNotification(
            #         sound='default', # or custom sound
            #         # channel_id='your_channel_id' # For Android 8.0+ notification channels
            #     ),
            # ),
            # --- APNS (iOS) Specific Configuration (Optional) ---
            # apns=firebase_admin.messaging.APNSConfig(
            #     payload=firebase_admin.messaging.APNSPayload(
            #         aps=firebase_admin.messaging.Aps(
            #             sound='default', # or custom sound
            #             badge=1, # Example badge count
            #             # 'content-available': True # For background updates
            #         ),
            #     ),
            # ),
        )

        response = firebase_admin.messaging.send(message)
        print(f"[FCM Task] Successfully sent message to user {user_id}: {response}")
        return f"Message sent to user {user_id}: {response}"

    except User.DoesNotExist:
        print(f"[FCM Task] User with id {user_id} not found. Notification not sent.")
        return f"User {user_id} not found."
    except FirebaseError as e:
        # Handle Firebase-specific errors
        if "registration-token-not-registered" in str(e):
            print(f"[FCM Task] FCM token is no longer valid: {user.fcm_token}")
            # You might want to remove this token from your database
            User.objects.filter(id=user_id).update(fcm_token=None)
            print(f"[FCM Task] Cleared invalid FCM token for user {user_id}.")
            return f"Cleared invalid FCM token for user {user_id} due to error: {e.code}"
        elif "invalid-argument" in str(e):
            print(f"[FCM Task] Invalid FCM token: {user.fcm_token}")
            User.objects.filter(id=user_id).update(fcm_token=None)
            print(f"[FCM Task] Cleared invalid FCM token for user {user_id}.")
            return f"Cleared invalid FCM token for user {user_id} due to error: {e.code}"
        else:
            print(f"[FCM Task] Firebase error sending to user {user_id}: {e}")
            try:
                # Retry for other Firebase errors (e.g., temporary server issues)
                raise self.retry(exc=e)
            except self.MaxRetriesExceededError:
                print(f"[FCM Task] Max retries exceeded for user {user_id}. Error: {e}")
                return f"Max retries exceeded sending to user {user_id}."
    except Exception as e:
        print(f"[FCM Task] Unexpected error sending to user {user_id}: {e}")
        try:
            # Retry for other unexpected errors
            raise self.retry(exc=e)
        except self.MaxRetriesExceededError:
            print(f"[FCM Task] Max retries exceeded for user {user_id} after unexpected error: {e}")
            return f"Max retries exceeded for user {user_id} after unexpected error."


@shared_task
def expire_old_ride_requests():
    """
    Finds ride requests older than settings.RIDE_REQUEST_EXPIRY_MINUTES 
    that are still in 'REQUESTED' state and marks them as 'NO_DRIVER_FOUND'.
    """
    expiry_time_delta = timedelta(minutes=getattr(settings, 'RIDE_REQUEST_EXPIRY_MINUTES', 10))
    cutoff_time = timezone.now() - expiry_time_delta

    print(f"[Task:expire_old_ride_requests] Running. Cutoff time for expiry: {cutoff_time}")

    expired_rides = Ride.objects.filter(
        status=Ride.StatusChoices.REQUESTED,
        requested_at__lt=cutoff_time,
        driver__isnull=True  # Ensure no driver has been assigned
    )

    count = 0
    for ride in expired_rides:
        ride.status = Ride.StatusChoices.NO_DRIVER_FOUND
        ride.save(update_fields=['status'])
        count += 1
        print(f"[Task:expire_old_ride_requests] Ride {ride.id} expired, status set to NO_DRIVER_FOUND.")
        
        # *** Notify Rider that their request expired ***
        if ride.rider and ride.rider.fcm_token:
            send_fcm_notification_task.delay(
                ride.rider.id,
                title="Ride Request Expired",
                body="We couldn't find a driver for your ride request. Please try again.",
                data_payload={'ride_id': str(ride.id), 'type': 'RIDE_REQUEST_EXPIRED'}
            )

    if count > 0:
        print(f"[Task:expire_old_ride_requests] Successfully expired {count} ride requests.")
        return f"Expired {count} ride requests."
    else:
        print("[Task:expire_old_ride_requests] No ride requests to expire.")
        return "No ride requests to expire."

# TODO: Add other tasks here if needed, e.g., for periodic cleanup, analytics aggregation, etc.

# Example: If you wanted to notify drivers about surge pricing in an area (hypothetical)
# @shared_task
# def notify_drivers_of_surge(area_id, surge_multiplier):
#     drivers_in_area = User.objects.filter(user_type=User.UserTypeChoices.DRIVER, current_area_id=area_id, is_online=True)
#     for driver in drivers_in_area:
#         if driver.fcm_token:
#             send_fcm_notification_task.delay(
#                 driver.id,
#                 title="Surge Alert!",
#                 body=f"Demand is high in your current area! Fares are now {surge_multiplier}x.",
#                 data_payload={'area_id': str(area_id), 'type': 'SURGE_ALERT', 'multiplier': str(surge_multiplier)}
#             )
#     return f"Sent surge alerts for area {area_id}."
