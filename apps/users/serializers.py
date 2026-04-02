"""
User Serializers

Handles serialization and validation for:
  - User registration (public)
  - User profile (read)
  - User update (admin)
  - Login (returns JWT tokens)
  - Password change
"""
from rest_framework import serializers
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import authenticate
from .models import User


class UserRegistrationSerializer(serializers.ModelSerializer):
    """
    Used by Admin to create new users.
    Password is write-only and never returned in responses.
    """
    password  = serializers.CharField(write_only=True, min_length=8, style={'input_type': 'password'})
    password2 = serializers.CharField(write_only=True, label="Confirm Password", style={'input_type': 'password'})

    class Meta:
        model  = User
        fields = ['id', 'email', 'first_name', 'last_name', 'role', 'password', 'password2']
        read_only_fields = ['id']

    def validate(self, attrs):
        if attrs['password'] != attrs.pop('password2'):
            raise serializers.ValidationError({"password": "Passwords do not match."})
        return attrs

    def validate_role(self, value):
        # Only valid roles accepted
        valid_roles = [r.value for r in User.Role]
        if value not in valid_roles:
            raise serializers.ValidationError(f"Role must be one of: {', '.join(valid_roles)}.")
        return value

    def create(self, validated_data):
        return User.objects.create_user(**validated_data)


class UserProfileSerializer(serializers.ModelSerializer):
    """Read-only user profile — safe to return in responses."""
    full_name = serializers.CharField(read_only=True)

    class Meta:
        model  = User
        fields = ['id', 'email', 'first_name', 'last_name', 'full_name', 'role', 'is_active', 'created_at']
        read_only_fields = fields


class UserUpdateSerializer(serializers.ModelSerializer):
    """
    Admin-only: update any user's profile or role.
    Password is excluded here — use ChangePasswordSerializer for that.
    """
    class Meta:
        model  = User
        fields = ['first_name', 'last_name', 'role', 'is_active']

    def validate_role(self, value):
        valid_roles = [r.value for r in User.Role]
        if value not in valid_roles:
            raise serializers.ValidationError(f"Role must be one of: {', '.join(valid_roles)}.")
        return value


class LoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField()
    def validate(self, attrs):
        user = authenticate(username=attrs['email'], password=attrs['password'])
        if not user:
            raise serializers.ValidationError("Invalid email or password.")
        if not user.is_active:
            raise serializers.ValidationError("This account has been deactivated.")

        # Generate JWT token pair
        refresh = RefreshToken.for_user(user)
        return {
            'user': UserProfileSerializer(user).data,
            'tokens': {
                'access':  str(refresh.access_token),
                'refresh': str(refresh),
            }
        }


class ChangePasswordSerializer(serializers.Serializer):
    """Allows authenticated users to change their own password."""
    current_password = serializers.CharField(write_only=True, style={'input_type': 'password'})
    new_password     = serializers.CharField(write_only=True, min_length=8, style={'input_type': 'password'})
    confirm_password = serializers.CharField(write_only=True, style={'input_type': 'password'})

    def validate_current_password(self, value):
        user = self.context['request'].user
        if not user.check_password(value):
            raise serializers.ValidationError("Current password is incorrect.")
        return value

    def validate(self, attrs):
        if attrs['new_password'] != attrs['confirm_password']:
            raise serializers.ValidationError({"new_password": "New passwords do not match."})
        return attrs

    def save(self):
        user = self.context['request'].user
        user.set_password(self.validated_data['new_password'])
        user.save()
        return user
