from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import DriverDocument, UserVerification

User = get_user_model()

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = (
            'id', 'username', 'email', 'first_name', 'last_name', 'phone_number',
            'profile_picture', 'user_type', 'rating', 'total_trips', 'is_phone_verified',
        )
        read_only_fields = ('id', 'rating', 'total_trips', 'is_phone_verified', 'is_email_verified')

class UserPublicSerializer(serializers.ModelSerializer):
    """
    Serializer for exposing limited, public-safe user information,
    often used when nesting user details within other objects (like Rides).
    """
    full_name = serializers.CharField(source='get_full_name', read_only=True)

    class Meta:
        model = User
        fields = (
            'id',
            'username',
            'full_name',
            'profile_picture',
            'rating', 
            'user_type', 
            # Add any other fields considered safe to expose publicly here
        )
        read_only_fields = fields 


class UserRegistrationSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, style={'input_type': 'password'})
    

    class Meta:
        model = User
        # Ensure all fields needed at signup are listed
        fields = (
            'phone_number', 'password', 'email', 'first_name', 'last_name', 'user_type'
        )
        
    
    def validate(self, data):
        errors = {}

        if not data.get('phone_number'):
            errors.setdefault('phone_number', []).append("Phone number is required.")
        if not data.get('email'):
            errors.setdefault('email', []).append("Email is required.")
        if not data.get('password'):
            errors.setdefault('password', []).append("Password is required.")   
        if not data.get('first_name') or not data.get('last_name'):
            errors.setdefault('name', []).append("First name and last name are required.")

        

        
        
        
        if data.get('phone_number'):
            # Check if phone number already exists
            if User.objects.filter(phone_number=data['phone_number']).exists():
                raise serializers.ValidationError({"Phone number already exists."})
        # Optionally: Validate that email is valid if provided
        if data.get('email'):
            if User.objects.filter(email=data['email']).exists():
                raise serializers.ValidationError({ "Email already exists."})
        # validate password using django password validation
        from django.contrib.auth.password_validation import validate_password
        from django.core.exceptions import ValidationError as PasswordValidationError
        try:
            validate_password(data['password'])
        except PasswordValidationError as e:
            errors.setdefault('password', []).extend(e.messages)
            
        if errors:
            raise serializers.ValidationError(errors)
        
        # Optionally: Validate that password is strong enough
        return data
        

    def create(self, validated_data):
        # If username isn't provided, generate one from first name and phone number, for example
        if not validated_data.get('username'):
            print("Generating username from first name and phone number")
            validated_data['username'] = (
                validated_data.get('phone_number', '')
            )
        
        if not validated_data.get('user_type'):
            validated_data['user_type'] = 'rider'

        
        
        # Create the user using Django's create_user method
        user = User.objects.create_user(
            username=validated_data['username'],
            email=validated_data.get('email', ''),
            password=validated_data['password'],
            first_name=validated_data.get('first_name', ''),
            last_name=validated_data.get('last_name', ''),
            phone_number=validated_data['phone_number'],
            user_type=validated_data['user_type'],
            emergency_contact=validated_data.get('emergency_contact', ''),
            emergency_contact_name=validated_data.get('emergency_contact_name', '')
        )
        return user

class DriverProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = (
            'id', 'username', 'email', 'first_name', 'last_name', 'phone_number',
            'profile_picture', 'vehicle_type', 'vehicle_number', 'vehicle_color',
            'vehicle_model', 'vehicle_year', 'is_online', 'current_location',
            'rating', 'total_trips', 'emergency_contact', 'emergency_contact_name'
        )
        read_only_fields = ('id', 'rating', 'total_trips')

class RiderProfileSerializer(serializers.ModelSerializer):
    # Map the JSONField in the model (saved_locations_data) to the serializer field 'saved_locations'
    saved_locations = serializers.JSONField(source='saved_locations_data')
    
    class Meta:
        model = User
        fields = (
            'id', 'username', 'email', 'first_name', 'last_name', 'phone_number',
            'profile_picture', 'saved_locations', 'preferred_payment_method',
            'emergency_contact', 'emergency_contact_name'
        )
        read_only_fields = ('id',)

class DriverDocumentSerializer(serializers.ModelSerializer):
    class Meta:
        model = DriverDocument
        fields = (
            'id', 'document_type', 'document_file', 'is_verified', 'uploaded_at', 'verified_at'
        )
        read_only_fields = ('id', 'is_verified', 'uploaded_at', 'verified_at')

class UserVerificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserVerification
        fields = (
            'phone_verification_code', 'email_verification_code', 'phone_verified_at', 'email_verified_at'
        )
        read_only_fields = ('phone_verified_at', 'email_verified_at')

class ChangePasswordSerializer(serializers.Serializer):
    old_password = serializers.CharField(required=True)
    new_password = serializers.CharField(required=True)
    confirm_password = serializers.CharField(required=True)

    def validate(self, data):
        if data['new_password'] != data['confirm_password']:
            raise serializers.ValidationError("The new passwords don't match.")
        return data

class UpdateProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = (
            'first_name', 'last_name', 'email', 'phone_number', 'profile_picture',
            'emergency_contact', 'emergency_contact_name'
        )