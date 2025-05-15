from rest_framework.decorators import api_view, authentication_classes, permission_classes
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.authentication import TokenAuthentication
from .services import FriendshipService
from users.services import UserService

@api_view(['POST'])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated])
def send_friend_request(request):
    """Send a friend request to another user"""
    # Parse request data
    receiver_identifier = request.data.get('username') or request.data.get('user_id')
    if not receiver_identifier:
        return Response({'error': 'Username or user ID is required'}, status=status.HTTP_400_BAD_REQUEST)
    # Use service to find the receiver
    is_username = bool(request.data.get('username'))
    receiver = UserService.get_user_by_identifier(receiver_identifier, is_username)
    if not receiver:
        return Response({'error': 'User not found'}, status=status.HTTP_404_NOT_FOUND)
    # Prevent sending to self
    if request.user.id == receiver.id:
        return Response({'error': 'Cannot send friend request to yourself'}, status=status.HTTP_400_BAD_REQUEST)
    # Check for existing requests
    existing_request = FriendshipService.check_existing_request(request.user, receiver)
    
    if existing_request:
        if existing_request.sender == request.user:
            return Response({'error': 'Friend request already sent'}, status=status.HTTP_400_BAD_REQUEST)
        else:
            # Accept existing request from the other user
            updated_request = FriendshipService.update_request_status(existing_request, 'accepted')
            return Response({'success': f'Friend request from {receiver.username} was accepted'}, status=status.HTTP_200_OK)
    
    # Create new request
    FriendshipService.create_friend_request(request.user, receiver)
    return Response({'success': f'Friend request sent to {receiver.username}'}, status=status.HTTP_201_CREATED)


@api_view(['POST'])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated])
def handle_friend_request(request):
    """Accept or reject a friend request"""
    # Parse request data
    request_id = request.data.get('request_id')
    action = request.data.get('action')
    
    if not request_id:
        return Response({'error': 'Request ID is required'}, status=status.HTTP_400_BAD_REQUEST)
    
    if action not in ['accept', 'reject']:
        return Response({'error': 'Action must be either "accept" or "reject"'}, status=status.HTTP_400_BAD_REQUEST)
    
    # Use service to get and update request
    friend_request = FriendshipService.get_friend_request(request_id, request.user)
    
    if not friend_request:
        return Response({'error': 'Friend request not found'}, status=status.HTTP_404_NOT_FOUND)
    
    updated_request = FriendshipService.update_request_status(friend_request, action)
    
    return Response({
        'success': f'Friend request from {updated_request.sender.username} {action}ed'
    }, status=status.HTTP_200_OK)


@api_view(['GET'])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated])
def get_friend_requests(request):
    """Get a list of pending friend requests"""
    # Use service to get requests
    sent_requests, received_requests = FriendshipService.get_user_requests(request.user)
    
    # Format data for API response
    sent_data = [{
        'id': req.id,
        'receiver': {
            'id': req.receiver.id,
            'username': req.receiver.username
        },
        'status': req.status,
        'created_at': req.created_at
    } for req in sent_requests]
    
    received_data = [{
        'id': req.id,
        'sender': {
            'id': req.sender.id,
            'username': req.sender.username
        },
        'status': req.status,
        'created_at': req.created_at
    } for req in received_requests]
    
    return Response({
        'sent_requests': sent_data,
        'received_requests': received_data
    }, status=status.HTTP_200_OK)


@api_view(['GET'])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated])
def get_friends(request):
    """Get a list of the current user's accepted friends"""
    # Use service to get friend data
    accepted_as_sender, accepted_as_receiver = FriendshipService.get_user_friends(request.user)
    
    friends = []
    
    # Format data for API response
    for fr in accepted_as_sender:
        friends.append({
            'id': fr.receiver.id,
            'username': fr.receiver.username,
            'email': fr.receiver.email,
            'request_id': fr.id,
            'since': fr.updated_at
        })
    
    for fr in accepted_as_receiver:
        friends.append({
            'id': fr.sender.id,
            'username': fr.sender.username,
            'email': fr.sender.email,
            'request_id': fr.id,
            'since': fr.updated_at
        })
    
    return Response(friends, status=status.HTTP_200_OK)


@api_view(['DELETE'])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated])
def delete_friend(request):
    """Delete a friendship connection"""
    # Parse request data
    friend_id = request.data.get('friend_id')
    
    if not friend_id:
        return Response({'error': 'Friend ID is required'}, status=status.HTTP_400_BAD_REQUEST)
    
    # Use service to handle deletion
    deleted, friend = FriendshipService.delete_friendship(request.user, friend_id)
    
    if not deleted:
        return Response({'error': 'Friendship not found'}, status=status.HTTP_404_NOT_FOUND)
    
    return Response({'success': f'Removed {friend.username} from friends'}, status=status.HTTP_200_OK)