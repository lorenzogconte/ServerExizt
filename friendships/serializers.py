from rest_framework import serializers
from .models import FriendRequest, FriendList
from users.serializers import ProfileSerializer

class FriendRequestSenderSerializer(serializers.ModelSerializer):
    sender = ProfileSerializer(source='sender.profile', read_only=True)
    
    class Meta:
        model = FriendRequest
        fields = ['id', 'sender', 'status', 'created_at']

class FriendRequestReceiverSerializer(serializers.ModelSerializer):
    receiver = ProfileSerializer(source='receiver.profile', read_only=True)
    
    class Meta:
        model = FriendRequest
        fields = ['id', 'receiver', 'status', 'created_at']

class FriendRequestsSerializer(serializers.Serializer):
    sent_requests = FriendRequestReceiverSerializer(many=True)
    received_requests = FriendRequestSenderSerializer(many=True)