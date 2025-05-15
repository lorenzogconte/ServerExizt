from django.db.models import Q
from django.contrib.auth import get_user_model
from .models import FriendRequest

User = get_user_model()

class FriendshipService:

    @staticmethod
    def check_existing_request(sender, receiver):
        """Check if there's an existing request between users"""
        return FriendRequest.objects.filter(
            Q(sender=sender, receiver=receiver) | 
            Q(sender=receiver, receiver=sender)
        ).first()
        
    @staticmethod
    def create_friend_request(sender, receiver):
        """Create a new friend request"""
        return FriendRequest.objects.create(sender=sender, receiver=receiver)
        
    @staticmethod
    def get_friend_request(request_id, receiver, status='pending'):
        """Get a friend request by ID for a specific receiver"""
        try:
            return FriendRequest.objects.get(id=request_id, receiver=receiver, status=status)
        except FriendRequest.DoesNotExist:
            return None
            
    @staticmethod
    def update_request_status(friend_request, status):
        """Update the status of a friend request"""
        friend_request.status = status
        friend_request.save()
        return friend_request
        
    @staticmethod
    def get_user_requests(user):
        """Get all requests for a user"""
        sent_requests = FriendRequest.objects.filter(sender=user)
        received_requests = FriendRequest.objects.filter(receiver=user)
        return sent_requests, received_requests
        
    @staticmethod
    def get_user_friends(user):
        """Get all accepted friends for a user"""
        accepted_as_sender = FriendRequest.objects.filter(sender=user, status='accepted')
        accepted_as_receiver = FriendRequest.objects.filter(receiver=user, status='accepted')
        return accepted_as_sender, accepted_as_receiver
        
    @staticmethod
    def delete_friendship(user, friend_id):
        """Delete a friendship between two users"""
        try:
            friend = User.objects.get(id=friend_id)
            deleted_count = FriendRequest.objects.filter(
                (Q(sender=user, receiver=friend) | Q(sender=friend, receiver=user)),
                status='accepted'
            ).delete()[0]
            return (deleted_count > 0), friend
        except User.DoesNotExist:
            return False, None