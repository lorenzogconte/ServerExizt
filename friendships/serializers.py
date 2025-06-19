from rest_framework import serializers
from .models import FriendRequest, FriendList
from users.serializers import UserSerializer

class FriendRequestSenderSerializer(serializers.ModelSerializer):
    sender = UserSerializer(read_only=True)
    
    class Meta:
        model = FriendRequest
        fields = ['id', 'sender', 'status', 'created_at']

class FriendRequestReceiverSerializer(serializers.ModelSerializer):
    receiver = UserSerializer(read_only=True)
    
    class Meta:
        model = FriendRequest
        fields = ['id', 'receiver', 'status', 'created_at']

class FriendRequestsSerializer(serializers.Serializer):
    sent_requests = FriendRequestReceiverSerializer(many=True)
    received_requests = FriendRequestSenderSerializer(many=True)