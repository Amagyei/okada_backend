# rides/signals.py
from django.db.models.signals import pre_save, post_save
from django.dispatch import receiver
from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer

from rides.models import Ride

# 1) Capture old status pre‐save
@receiver(pre_save, sender=Ride)
def ride_pre_save(sender, instance, **kwargs):
    if instance.pk:
        try:
            previous = Ride.objects.get(pk=instance.pk)
            instance._old_status = previous.status
        except Ride.DoesNotExist:
            instance._old_status = None
    else:
        instance._old_status = None


# 2) After save, fire notifications for each transition
@receiver(post_save, sender=Ride)
def ride_post_save(sender, instance: Ride, created, **kwargs):
    print(f"[🚨 ride_post_save] created={created} old={getattr(instance,'_old_status',None)} new={instance.status}")
    channel_layer = get_channel_layer()
    group_name    = f"user_{instance.rider_id}"
    send_to_group = lambda payload: async_to_sync(channel_layer.group_send)(
        group_name,
        {"type": "send_notification", "payload": payload}
    )

    # A) NEW REQUEST
    if created:
        send_to_group({
            "title":   "🚗 Ride Requested",
            "body":    f"Your ride #{instance.id} is now REQUESTED.",
            "ride_id": instance.id,
            "type":    "RIDE_REQUESTED",
        })
        return

    old, new = instance._old_status, instance.status

    # B) RIDE ACCEPTED
    if old != new and new == Ride.StatusChoices.ACCEPTED:
        send_to_group({
            "title":   "✅ Driver Assigned",
            "body":    f"Driver {instance.driver.get_full_name()} is on the way!",
            "ride_id": instance.id,
            "type":    "RIDE_ASSIGNED",
        })

    #C ON ROUTE TO PICKUP
    if old != new and new == Ride.StatusChoices.ON_ROUTE_TO_PICKUP:
        send_to_group({
            "title":   "🚗 Driver on the way",
            "body":    f"Driver {instance.driver.get_full_name()} is on the way to your pickup location.",
            "ride_id": instance.id,
            "type":    "RIDE_ON_ROUTE_TO_PICKUP",
        })

    # C) ARRIVED AT PICKUP
    if old != new and new == Ride.StatusChoices.ARRIVED_AT_PICKUP:
        send_to_group({
            "title":   "📍 Driver Arrived",
            "body":    "Your driver has arrived at pickup location.",
            "ride_id": instance.id,
            "type":    "DRIVER_ARRIVED",
        })

    # D) RIDE IN PROGRESS
    if old != new and new == Ride.StatusChoices.ON_TRIP:
        send_to_group({
            "title":   "🏁 Ride Started",
            "body":    "Enjoy your trip!",
            "ride_id": instance.id,
            "type":    "RIDE_STARTED",
        })

    # E) RIDE COMPLETED
    if old != new and new == Ride.StatusChoices.COMPLETED:
        send_to_group({
            "title":   "🎉 Ride Completed",
            "body":    f"Your ride #{instance.id} is complete. Thanks for riding!",
            "ride_id": instance.id,
            "type":    "RIDE_COMPLETED",
        })

    # F) CANCELLED BY RIDER
    if old != new and new == Ride.StatusChoices.CANCELLED_BY_RIDER:
        send_to_group({
            "title":   "❌ Ride Cancelled",
            "body":    "You’ve cancelled your ride request.",
            "ride_id": instance.id,
            "type":    "RIDE_CANCELLED_BY_RIDER",
        })

    # G) CANCELLED BY DRIVER
    if old != new and new == Ride.StatusChoices.CANCELLED_BY_DRIVER:
        send_to_group({
            "title":   "⚠️ Ride Cancelled",
            "body":    "Your driver cancelled the ride. Try again?",
            "ride_id": instance.id,
            "type":    "RIDE_CANCELLED_BY_DRIVER",
        })

    # H) NO DRIVER FOUND
    if old != new and new == Ride.StatusChoices.NO_DRIVER_FOUND:
        send_to_group({
            "title":   "⏰ No Driver Found",
            "body":    "Sorry, we couldn't find a driver for your ride.",
            "ride_id": instance.id,
            "type":    "NO_DRIVER_FOUND",
        })

        # H) EXPIRED (no driver found) — you already have a periodic task for this,
    #    but you could mirror it here instead of Celery if you prefer.
    #    but you could mirror it here instead of Celery if you prefer.