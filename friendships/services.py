from django.db.models import Q
from django.contrib.auth import get_user_model
from .models import FriendRequest, FriendList

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
    def get_or_create_friendslist(user):
        """Get or create friend list for user"""
        friend_list, created = FriendList.objects.get_or_create(user=user)
        return friend_list.friends.all()
    
    @staticmethod
    def get_or_create_friend_list(user):
        """Get or create a friend list for a user and return the FriendList object"""
        friend_list, created = FriendList.objects.get_or_create(user=user)
        return friend_list

    @staticmethod
    def get_friend_request(request_id, user):
        """Get a friend request by ID where the user is the receiver"""
        try:
            return FriendRequest.objects.get(id=request_id, receiver=user)
        except FriendRequest.DoesNotExist:
            return None
    
    @staticmethod
    def are_friends(user1, user2):
        """Check if two users are friends"""
        try:
            friend_list = FriendList.objects.get(user=user1)
            return friend_list.friends.filter(id=user2.id).exists()
        except FriendList.DoesNotExist:
            return False
            
    @staticmethod
    def update_request_status(friend_request, action):
        """
        Update the status of a friend request and handle accordingly
        - If accepted, add both users to each other's friend lists and delete the request
        - If rejected, just delete the request
        """
        if action == 'accept':
            # Get or create friend lists
            sender_list = FriendshipService.get_or_create_friend_list(friend_request.sender)
            receiver_list = FriendshipService.get_or_create_friend_list(friend_request.receiver)
            
            # Add users to each other's friend lists
            sender_list.friends.add(friend_request.receiver)
            receiver_list.friends.add(friend_request.sender)
            
            sender_list = FriendshipService.get_or_create_friend_list(friend_request.sender)
            receiver_list = FriendshipService.get_or_create_friend_list(friend_request.receiver)
            print("Sender's Friends:", sender_list.friends.all())
            print("Receiver's Friends:", receiver_list.friends.all())
            # Store information for return value
            sender = friend_request.sender
            receiver = friend_request.receiver
            request_id = friend_request.id
            created_at = friend_request.created_at
            friend_request.delete()
            return {
                'sender': sender, 
                'receiver': receiver, 
                'id': request_id,
                'created_at': created_at
            }
        elif action == 'reject':
            sender = friend_request.sender
            friend_request.delete()
            return {'sender': sender}
        
    @staticmethod
    def get_received_pending_requests(user):
        """Get all received requests for a user"""
        return FriendRequest.objects.filter(receiver=user, status='pending')
    
    @staticmethod
    def get_sent_pending_requests(user):
        """Get all sent requests for a user"""
        return FriendRequest.objects.filter(sender=user, status='pending')
        
    @staticmethod
    def delete_friendship(user, friend_id):
        """Delete a friendship between two users"""
        try:
            friend = User.objects.get(id=friend_id)
            
            removed_from_user = False
            removed_from_friend = False
            
            try:
                user_friend_list = FriendList.objects.get(user=user)
                user_friend_list.friends.remove(friend)
                removed_from_user = True
            except FriendList.DoesNotExist:
                pass
                
            try:
                friend_list = FriendList.objects.get(user=friend)
                friend_list.friends.remove(user)
                removed_from_friend = True
            except FriendList.DoesNotExist:
                pass
                
            return (removed_from_user or removed_from_friend), friend
        except User.DoesNotExist:
            return False, None