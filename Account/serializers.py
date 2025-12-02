from rest_framework import serializers
from .utils import generate_otp
from .models import Profile
from django.core.mail import send_mail, EmailMessage
from rest_framework_simplejwt.tokens import RefreshToken
from google.oauth2 import id_token
from google.auth.transport import requests as google_requests
from rest_framework import serializers
from .models import User, Profile, User
from django.contrib.auth import get_user_model
from django.contrib.auth import password_validation
from django.template.loader import render_to_string
from django.conf import settings
User = get_user_model()

""" ----------------User Serializer------------------- """
class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'Fullname', 'email', 'date_joined', 'is_active']
        extra_kwargs = {
            'Fullname': {'required': False},
            'email': {'required': False}
        }
    
    def update(self, instance, validated_data):
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        return instance



""" ----------------Google Auth Serializer------------------- """



from rest_framework import serializers
import requests
from django.conf import settings
from .models import User, Profile

class GoogleAuthSerializer(serializers.Serializer):
    access_token = serializers.CharField()  # Changed from id_token

    def validate(self, attrs):
        token = attrs.get("access_token")
        print("Validating Google access token:", token[:50] + "...")
        
        try:
            # Use access token to get user info
            response = requests.get(
                "https://www.googleapis.com/oauth2/v2/userinfo",
                headers={"Authorization": f"Bearer {token}"}
            )
            
            if response.status_code != 200:
                raise serializers.ValidationError("Invalid Google token")
            
            user_info = response.json()
            
            if "email" not in user_info:
                raise serializers.ValidationError("Email not found in token")

            attrs["email"] = user_info["email"]
            attrs["name"] = user_info.get("name", "")
            attrs["picture"] = user_info.get("picture", "")
            return attrs

        except requests.RequestException as e:
            print(f"Token validation error: {e}")
            raise serializers.ValidationError("Failed to validate Google token")

    def create_or_login_user(self):
        email = self.validated_data["email"]
        name = self.validated_data["name"]

        user, created = User.objects.get_or_create(
            email=email,
            defaults={
                "Fullname": name,
                "social_auth_provider": "google",
                "is_active": True,
            }
        )

        Profile.objects.get_or_create(
            user=user,
            defaults={
                "social_auth_provider": "google",
                "is_verified": True,
            }
        )

        return user

""" ----------------registration Serializer------------------- """

class RegistrationSerializer(serializers.ModelSerializer):
    confirm_password = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = ['email', 'password', 'confirm_password', 'date_joined']
        extra_kwargs = {
            'password': {'write_only': True},
        }

    def validate(self, data):
        if data['password'] != data['confirm_password']:
            raise serializers.ValidationError("Passwords do not match")
        return data

    def create(self, validated_data):
        validated_data.pop('confirm_password')
        user = User.objects.create_user(**validated_data)
        user.is_active = False 
        user.save()

        # Create Profile with OTP
        otp_code = generate_otp()
        Profile.objects.create(user=user, otp=otp_code)
        
        # Send HTML email with OTP
        html_content = render_to_string('send_code.html', {
            'otp': otp_code, 
            'user': user
        })
        
        try:
            msg = EmailMessage(
                subject='Your OTP Code - Verify Your Account',
                body=html_content,
                from_email=settings.DEFAULT_FROM_EMAIL,
                to=[user.email],
            )
            msg.content_subtype = "html"
            msg.send()
        except Exception as e:
            print(f"Failed to send OTP email: {e}")
            # Optional: এখানে user delete করতে পারেন যদি email fail হয়
            # user.delete()
            # raise serializers.ValidationError("Failed to send verification email")

        return user




""" ----------------Login view------------------- """


class LoginSerializer(serializers.Serializer):
    email = serializers.CharField(required=True)
    password = serializers.CharField(required=True, write_only=True)


""" ----------------User Login view------------------- """
class UserLoginSerializer(serializers.ModelSerializer):
    tokens = serializers.SerializerMethodField()

    def get_tokens(self, user):
        refresh = RefreshToken.for_user(user)
        return {
            'refresh': str(refresh),
            'access': str(refresh.access_token),
        }

    class Meta:
        model = User
        fields = ['email', 'tokens']


""" ----------------Reset password Serializer------------------- """

class ResetPasswordSerializer(serializers.Serializer):
    email = serializers.EmailField()  # ✅ Add this
    password = serializers.CharField(write_only=True, min_length=8)
    confirm_password = serializers.CharField(write_only=True, min_length=8)

    def validate(self, data):
        if data['password'] != data['confirm_password']:
            raise serializers.ValidationError("Passwords do not match")
        return data

""" ----------------Profile Serializer------------------- """
class ProfileSerializer(serializers.ModelSerializer):
    fullname = serializers.SerializerMethodField()
    email = serializers.SerializerMethodField()
    class Meta:
        model = Profile
        fields = [ 'fullname','email', 'profile_picture', 'Country', 'City', 'Province', 'Gender', 'Bio']
    
    def get_fullname(self, obj):
        return obj.user.Fullname
    def get_email(self, obj):
        return obj.user.email


""" ----------------Profile Update Serializer------------------- """


class ProfileUpdateSerializer(serializers.ModelSerializer):
    fullname = serializers.CharField(source='user.Fullname', required=False)

    class Meta:
        model = Profile
        fields = ['fullname', 'profile_picture', 'Country','City','Province','Gender','Bio']

    def update(self, instance, validated_data):
        # Update User Fullname
        user_data = validated_data.pop('user', {})
        if 'Fullname' in user_data:
            instance.user.Fullname = user_data['Fullname']
            instance.user.save()
        
        # Update Profile fields
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        return instance



""" ----------------Change Password Serializer------------------- """


class ChangePasswordSerializer(serializers.Serializer):
    old_password = serializers.CharField(required=True, write_only=True)
    new_password = serializers.CharField(required=True, write_only=True)
    confirm_password = serializers.CharField(required=True, write_only=True)

    def validate_new_password(self, value):
        password_validation.validate_password(value, self.context['request'].user)
        return value

    def validate(self, data):
        if data["new_password"] != data["confirm_password"]:
            raise serializers.ValidationError({"confirm_password": "New password and confirm password do not match."})
        return data