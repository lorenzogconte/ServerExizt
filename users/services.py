from django.contrib.auth import authenticate
from rest_framework.authtoken.models import Token
from .models import User, Profile

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
            avatarUrl=avatar_url
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