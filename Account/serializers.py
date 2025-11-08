from rest_framework import serializers
from .utils import generate_otp
from .models import Profile
from django.core.mail import send_mail
from rest_framework_simplejwt.tokens import RefreshToken
# from google.oauth2 import id_token
# from google.auth.transport import requests as google_requests
from rest_framework import serializers
from .models import User, Profile
from django.contrib.auth import get_user_model
from django.contrib.auth import password_validation
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



# """ ----------------Google Auth Serializer------------------- """

# class GoogleAuthSerializer(serializers.Serializer):
#     id_token = serializers.CharField()

#     def validate(self, attrs):
#         token = attrs.get("id_token")
#         try:
#             idinfo = id_token.verify_oauth2_token(token, google_requests.Request())

#             if "email" not in idinfo:
#                 raise serializers.ValidationError("Email not found in token")

#             attrs["email"] = idinfo["email"]
#             attrs["name"] = idinfo.get("name", "")
#             attrs["picture"] = idinfo.get("picture", "")
#             return attrs
#         except ValueError:
#             raise serializers.ValidationError("Invalid Google token")

#     def create_or_login_user(self):
#         email = self.validated_data["email"]
#         name = self.validated_data["name"]
#         picture = self.validated_data["picture"]

#         user, created = User.objects.get_or_create(email=email, defaults={
#             "Fullname": name,
#             "social_auth_provider": "google",
#             "is_active": True,  # Optional, usually Google-authenticated users are active
#         })

#         if created:
#             # Create user profile
#             Profile.objects.create(user=user, profile_picture=picture, is_verified=True)

#             # Automatically create Bank Account
#             Account.objects.create(user=user)

#         else:
#             # Optional: update profile picture if not already set
#             if not user.profile.profile_picture:
#                 user.profile.profile_picture = picture
#                 user.profile.save()

#         return user


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

        # Create Profile and send OTP as before
        otp_code = generate_otp()
        Profile.objects.create(user=user, otp=otp_code)
        email_subject = 'Your OTP Code : '
        email_body = f'Your OTP Code Is : {otp_code}'
        send_mail(
            email_subject,
            email_body,
            'mdmamun340921@gmail.com', 
            [user.email]
        )

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