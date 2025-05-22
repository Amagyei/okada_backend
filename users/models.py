from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils.translation import gettext_lazy as _

class User(AbstractUser):
    USER_TYPE_CHOICES = (
        ('rider', 'Rider'),
        ('driver', 'Driver'),
    )
    
    
    user_type = models.CharField(max_length=10, choices=USER_TYPE_CHOICES, default='rider')
    phone_number = models.CharField(max_length=15, unique=True)
    profile_picture = models.ImageField(upload_to='profile_pictures/', null=True, blank=True)
    ghana_card_number = models.CharField(max_length=20, unique=True, null=True, blank=True)
    ghana_card_image = models.ImageField(upload_to='ghana_cards/', null=True, blank=True)
    is_phone_verified = models.BooleanField(default=False)
    is_email_verified = models.BooleanField(default=False)
    rating = models.DecimalField(max_digits=3, decimal_places=2, default=0.00)
    total_trips = models.IntegerField(default=0)
    
    # Driver-specific fields
    is_online = models.BooleanField(default=False)
    current_location = models.JSONField(null=True, blank=True)
    vehicle_type = models.CharField(max_length=50, null=True, blank=True)
    vehicle_number = models.CharField(max_length=20, null=True, blank=True)
    vehicle_color = models.CharField(max_length=20, null=True, blank=True)
    vehicle_model = models.CharField(max_length=50, null=True, blank=True)
    vehicle_year = models.IntegerField(null=True, blank=True)
    
    # Rider-specific fields (renamed to avoid conflict with reverse relations)
    saved_locations_data = models.JSONField(null=True, blank=True)
    preferred_payment_method = models.CharField(max_length=20, null=True, blank=True)
    
    # Common fields
    emergency_contact = models.CharField(max_length=15, null=True, blank=True)
    emergency_contact_name = models.CharField(max_length=100, null=True, blank=True)
    
    REQUIRED_FIELDS = ['phone_number']

    class Meta:
        verbose_name = _('user')
        verbose_name_plural = _('users')
        unique_together = ('username', 'phone_number')
    
    def __str__(self):
        return f"{self.get_full_name()} ({self.get_user_type_display()})"
    
    def get_user_type_display(self):
        return dict(self.USER_TYPE_CHOICES)[self.user_type]

class DriverDocument(models.Model):
    DOCUMENT_TYPES = (
        ('license', "Driver's License"),
        ('insurance', 'Insurance'),
        ('registration', 'Vehicle Registration'),
        ('other', 'Other'),
    )
    
    driver = models.ForeignKey(User, on_delete=models.CASCADE, related_name='documents')
    document_type = models.CharField(max_length=20, choices=DOCUMENT_TYPES)
    document_file = models.FileField(upload_to='driver_documents/')
    is_verified = models.BooleanField(default=False)
    uploaded_at = models.DateTimeField(auto_now_add=True)
    verified_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        verbose_name = _('driver document')
        verbose_name_plural = _('driver documents')
    
    def __str__(self):
        return f"{self.driver.get_full_name()} - {self.get_document_type_display()}"

class UserVerification(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='verification')
    phone_number = models.CharField(max_length=15, null=True, blank=True)
    phone_verification_code = models.CharField(max_length=6, null=True, blank=True)
    email_verification_code = models.CharField(max_length=6, null=True, blank=True)
    phone_verification_sent_at = models.DateTimeField(null=True, blank=True)
    email_verification_sent_at = models.DateTimeField(null=True, blank=True)
    phone_verified_at = models.DateTimeField(null=True, blank=True)
    email_verified_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        verbose_name = _('user verification')
        verbose_name_plural = _('user verifications')
    
    def __str__(self):
        return f"Verification for {self.user.get_full_name()}"
    
    # set the phone number 
    def set_phone_number(self, phone_number):
        self.phone_number = self.user.phone_number
        self.save()