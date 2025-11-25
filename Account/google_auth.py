from django.contrib.auth import get_user_model
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework.response import Response
from rest_framework import status
 
 
User = get_user_model()
 
def get_or_create_google_user(google_data):
    """
    google_data: dict returned from Google token verification
    """
    email = google_data.get("email")
 
    # Check if user exists
    user, created = User.objects.get_or_create(
        email=email,
    )
    
 
    return user
 
def generate_jwt_for_user(user):
    refresh = RefreshToken.for_user(user)
    return{
                'user':{
                'user_id': user.id,
                'email': user.email,              
                },
                
                'refresh': str(refresh),
                'access': str(refresh.access_token),
            }
   
 