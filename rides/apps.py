from django.apps import AppConfig

class RidesConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'rides'
    verbose_name = 'Rides Management' 

    def ready(self):
        import rides.signals
    verbose_name = 'Rides Management' 
