from django.contrib import admin
from .models import User, DriverDocument, UserVerification

@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ('username', 'email', 'phone_number', 'user_type', 'is_phone_verified', 'is_email_verified')
    search_fields = ('username', 'email', 'phone_number')
    list_filter = ('user_type', 'is_phone_verified', 'is_email_verified')

@admin.register(DriverDocument)
class DriverDocumentAdmin(admin.ModelAdmin):
    list_display = ('driver', 'document_type', 'is_verified', 'uploaded_at')
    search_fields = ('driver__username', 'document_type')

@admin.register(UserVerification)
class UserVerificationAdmin(admin.ModelAdmin):
    list_display = ('user', 'phone_verification_code', 'email_verification_code', 'phone_verified_at', 'email_verified_at')
    search_fields = ('user__username',)