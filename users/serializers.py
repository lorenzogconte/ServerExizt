from rest_framework import serializers
from .models import User, Profile
from django.contrib.auth import authenticate

class UserSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'password']

    def create(self, validated_data):
        user = User(
            username=validated_data['username'],
            email=validated_data['email']
        )
        user.set_password(validated_data['password'])  # hashes password
        user.save()
        return user

class ProfileSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)  # Nested serializer for the related user

    class Meta:
        model = Profile
        fields = ['id', 'user', 'name', 'avatarUrl']

class LoginSerializer(serializers.Serializer):
    username = serializers.CharField()
    password = serializers.CharField()