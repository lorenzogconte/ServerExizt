from rest_framework import serializers
from .models import User, Profile

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'email',]

class ProfileSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)  # Nested serializer for the related user

    class Meta:
        model = Profile
        fields = ['id', 'user', 'username', 'name', 'avatarUrl', 'dailyScreenTimeGoal', 'totalScreenTime', 'focusMode']