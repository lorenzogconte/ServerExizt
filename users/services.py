from django.contrib.auth import authenticate
from rest_framework.authtoken.models import Token
from .models import User, Profile
from django.conf import settings

class UserService:
    @staticmethod
    def create_user(username, email, password):
        """Create a new user with proper password hashing"""
        user = User(
            username=username,
            email=email
        )
        user.set_password(password)  # Properly hashes the password
        user.save()
        return user
    
    @staticmethod
    def create_profile(user, name=None, avatar_url=''):
        """Create a profile for a user"""
        name = name or user.username
        return Profile.objects.create(
            user=user,
            name=name,
        )
    
    @staticmethod
    def create_auth_token(user):
        """Create authentication token for user"""
        return Token.objects.create(user=user)
    
    @staticmethod
    def authenticate_user(username, password):
        """Authenticate a user with username/email and password"""
        return authenticate(username=username, password=password)
    
    @staticmethod
    def get_or_create_auth_token(user):
        """Get existing token or create a new one"""
        token, created = Token.objects.get_or_create(user=user)
        return token
    
    @staticmethod
    def get_user_profile(user):
        """Get the profile for a user, or None if it doesn't exist"""
        try:
            return Profile.objects.get(user=user)
        except Profile.DoesNotExist:
            return None
        
    @staticmethod
    def get_user_by_identifier(identifier, is_username=False):
        """Find a user by username or ID"""
        try:
            if is_username:
                return User.objects.get(username=identifier)
            return User.objects.get(id=identifier)
        except User.DoesNotExist:
            return None
    
    @staticmethod
    def update_profile(user, name=None, avatar=None, username=None):
        # Update username if provided
        if username and username != user.username:
            # Check if username is already taken
            if User.objects.filter(username=username).exclude(id=user.id).exists():
                return False, "Username already taken"
            user.username = username
            user.save()
        
        # Get or create the user's profile
        profile, created = Profile.objects.get_or_create(user=user, defaults={'name': user.username})
        
        # Update profile fields if provided
        if name:
            profile.name = name
        if avatar is not None:  # Check if a file was uploaded
            profile.avatar = avatar
            
        profile.save()
        return True, profile
    
    @staticmethod
    def delete_user(user):
        # Profile will be automatically deleted due to CASCADE
        user.delete()
        return True