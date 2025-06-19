from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APITestCase, APIClient
from rest_framework.authtoken.models import Token
from rest_framework import status
from django.contrib.auth import get_user_model
from .models import FriendList, FriendRequest
from .services import FriendshipService

User = get_user_model()

class FriendshipModelsTest(TestCase):
    """Tests for friendship models"""
    
    def setUp(self):
        self.user1 = User.objects.create_user(
            username='testuser1',
            email='test1@example.com',
            password='testpassword123'
        )
        self.user2 = User.objects.create_user(
            username='testuser2',
            email='test2@example.com',
            password='testpassword123'
        )
    
    def test_friend_list_creation(self):
        """Test creating a friend list"""
        friend_list = FriendList.objects.create(user=self.user1)
        self.assertEqual(friend_list.user, self.user1)
        self.assertEqual(friend_list.friends.count(), 0)
        
        # Add a friend
        friend_list.friends.add(self.user2)
        self.assertEqual(friend_list.friends.count(), 1)
        self.assertTrue(friend_list.friends.filter(id=self.user2.id).exists())
    
    def test_friend_list_string_representation(self):
        """Test the string representation of FriendList"""
        friend_list = FriendList.objects.create(user=self.user1)
        self.assertEqual(str(friend_list), f"{self.user1}'s friends")
        
    def test_friend_request_creation(self):
        """Test creating a friend request"""
        request = FriendRequest.objects.create(
            sender=self.user1,
            receiver=self.user2
        )
        self.assertEqual(request.sender, self.user1)
        self.assertEqual(request.receiver, self.user2)
        self.assertEqual(request.status, 'pending')
        
    def test_friend_request_string_representation(self):
        """Test the string representation of FriendRequest"""
        request = FriendRequest.objects.create(
            sender=self.user1,
            receiver=self.user2
        )
        self.assertEqual(str(request), f"{self.user1} to {self.user2} - pending")
        
    def test_unique_together_constraint(self):
        """Test that a duplicate friend request raises an error"""
        FriendRequest.objects.create(sender=self.user1, receiver=self.user2)
        
        # Attempt to create a duplicate request should raise an IntegrityError
        with self.assertRaises(Exception):
            FriendRequest.objects.create(sender=self.user1, receiver=self.user2)


class FriendshipServiceTest(TestCase):
    """Tests for the FriendshipService"""
    
    def setUp(self):
        self.user1 = User.objects.create_user(
            username='testuser1',
            email='test1@example.com',
            password='testpassword123'
        )
        self.user2 = User.objects.create_user(
            username='testuser2',
            email='test2@example.com',
            password='testpassword123'
        )
        self.user3 = User.objects.create_user(
            username='testuser3',
            email='test3@example.com',
            password='testpassword123'
        )
        
    def test_check_existing_request(self):
        """Test checking for existing friend requests"""
        # No request exists yet
        self.assertIsNone(FriendshipService.check_existing_request(self.user1, self.user2))
        
        # Create a request
        FriendRequest.objects.create(sender=self.user1, receiver=self.user2)
        
        # Check for request from sender to receiver
        request = FriendshipService.check_existing_request(self.user1, self.user2)
        self.assertIsNotNone(request)
        self.assertEqual(request.sender, self.user1)
        self.assertEqual(request.receiver, self.user2)
        
        # Check for request from receiver to sender (should find the same request)
        request = FriendshipService.check_existing_request(self.user2, self.user1)
        self.assertIsNotNone(request)
        
    def test_create_friend_request(self):
        """Test creating a friend request"""
        request = FriendshipService.create_friend_request(self.user1, self.user2)
        self.assertEqual(request.sender, self.user1)
        self.assertEqual(request.receiver, self.user2)
        self.assertEqual(request.status, 'pending')
        
        # Verify it's in the database
        self.assertTrue(FriendRequest.objects.filter(sender=self.user1, receiver=self.user2).exists())
        
    def test_get_or_create_friendslist(self):
        """Test getting or creating a friend list"""
        # No friend list exists yet
        friends = FriendshipService.get_or_create_friendslist(self.user1)
        self.assertEqual(friends.count(), 0)
        
        # Friend list should have been created
        self.assertTrue(FriendList.objects.filter(user=self.user1).exists())
        
    def test_are_friends(self):
        """Test checking if users are friends"""
        # Not friends initially
        self.assertFalse(FriendshipService.are_friends(self.user1, self.user2))
        
        # Make them friends
        friend_list1 = FriendList.objects.create(user=self.user1)
        friend_list1.friends.add(self.user2)
        
        # Now they should be friends
        self.assertTrue(FriendshipService.are_friends(self.user1, self.user2))
        
        # But user3 is not friends with user1
        self.assertFalse(FriendshipService.are_friends(self.user1, self.user3))
        
    def test_get_received_pending_requests(self):
        """Test getting pending received requests"""
        # Create requests
        FriendRequest.objects.create(sender=self.user1, receiver=self.user3)
        FriendRequest.objects.create(sender=self.user2, receiver=self.user3)
        
        # Get received requests for user3
        requests = FriendshipService.get_received_pending_requests(self.user3)
        self.assertEqual(requests.count(), 2)
        
        # Get received requests for user1 (should be none)
        requests = FriendshipService.get_received_pending_requests(self.user1)
        self.assertEqual(requests.count(), 0)
        
    def test_get_sent_pending_requests(self):
        """Test getting pending sent requests"""
        # Create requests
        FriendRequest.objects.create(sender=self.user1, receiver=self.user2)
        FriendRequest.objects.create(sender=self.user1, receiver=self.user3)
        
        # Get sent requests for user1
        requests = FriendshipService.get_sent_pending_requests(self.user1)
        self.assertEqual(requests.count(), 2)
        
        # Get sent requests for user2 (should be none)
        requests = FriendshipService.get_sent_pending_requests(self.user2)
        self.assertEqual(requests.count(), 0)
        
    def test_delete_friendship(self):
        """Test deleting a friendship"""
        # Create friend lists and add friends
        friend_list1 = FriendList.objects.create(user=self.user1)
        friend_list2 = FriendList.objects.create(user=self.user2)
        
        friend_list1.friends.add(self.user2)
        friend_list2.friends.add(self.user1)
        
        # Verify they are friends
        self.assertTrue(FriendshipService.are_friends(self.user1, self.user2))
        
        # Delete friendship
        deleted, friend = FriendshipService.delete_friendship(self.user1, self.user2.id)
        
        # Check result
        self.assertTrue(deleted)
        self.assertEqual(friend, self.user2)
        
        # Verify they are no longer friends
        self.assertFalse(FriendshipService.are_friends(self.user1, self.user2))
        self.assertFalse(FriendshipService.are_friends(self.user2, self.user1))
        
        # Test deleting nonexistent friendship
        deleted, friend = FriendshipService.delete_friendship(self.user1, 999)
        self.assertFalse(deleted)
        self.assertIsNone(friend)


class FriendshipAPITest(APITestCase):
    """Tests for the friendship API endpoints"""
    
    def setUp(self):
        self.client = APIClient()
        
        # Create users
        self.user1 = User.objects.create_user(
            username='testuser1',
            email='test1@example.com',
            password='testpassword123'
        )
        self.user2 = User.objects.create_user(
            username='testuser2',
            email='test2@example.com',
            password='testpassword123'
        )
        self.user3 = User.objects.create_user(
            username='testuser3',
            email='test3@example.com',
            password='testpassword123'
        )
        
        # Create authentication tokens
        self.token1 = Token.objects.create(user=self.user1)
        self.token2 = Token.objects.create(user=self.user2)
        self.token3 = Token.objects.create(user=self.user3)
        
        # Define URLs
        self.send_request_url = reverse('send_friend_request')
        self.handle_request_url = reverse('handle_friend_request')
        self.get_requests_url = reverse('friend_requests') 
        self.get_friends_url = reverse('friendships')
        self.delete_friend_url = reverse('delete_friend') 
        
    def test_send_friend_request(self):
        """Test sending a friend request"""
        # Authenticate as user1
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.token1.key}')
        
        # Send request to user2 by username
        data = {'username': 'testuser2'}
        response = self.client.post(self.send_request_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        # Verify request exists in database
        self.assertTrue(FriendRequest.objects.filter(sender=self.user1, receiver=self.user2).exists())
        
        # Test sending duplicate request
        response = self.client.post(self.send_request_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        
        # Test sending to non-existent user
        data = {'username': 'nonexistentuser'}
        response = self.client.post(self.send_request_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        
        # Test sending to self
        data = {'username': 'testuser1'}
        response = self.client.post(self.send_request_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        
    def test_handle_friend_request(self):
        """Test accepting/rejecting a friend request"""
        # Create a request from user2 to user1
        request = FriendRequest.objects.create(sender=self.user2, receiver=self.user1)
        
        # Authenticate as user1
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.token1.key}')
        
        # Accept the request
        data = {'request_id': request.id, 'action': 'accept'}
        response = self.client.post(self.handle_request_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Create another request from user3 to user1
        request = FriendRequest.objects.create(sender=self.user3, receiver=self.user1)
        
        # Reject this request
        data = {'request_id': request.id, 'action': 'reject'}
        response = self.client.post(self.handle_request_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Test handling non-existent request
        data = {'request_id': 999, 'action': 'accept'}
        response = self.client.post(self.handle_request_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        
        # Test invalid action
        data = {'request_id': 1, 'action': 'invalid'}
        response = self.client.post(self.handle_request_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        
    def test_get_friend_requests(self):
        """Test getting friend requests"""
        # Create requests
        FriendRequest.objects.create(sender=self.user2, receiver=self.user1)
        FriendRequest.objects.create(sender=self.user3, receiver=self.user1)
        FriendRequest.objects.create(sender=self.user1, receiver=self.user3)
        
        # Authenticate as user1
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.token1.key}')
        
        # Get requests
        response = self.client.get(self.get_requests_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Check response structure
        self.assertIn('received_requests', response.data)
        self.assertIn('sent_requests', response.data)
        
        # Check counts
        self.assertEqual(len(response.data['received_requests']), 2)
        self.assertEqual(len(response.data['sent_requests']), 1)
        
    def test_get_friends(self):
        """Test getting user's friends"""
        # Create friend relationship
        friend_list1 = FriendList.objects.create(user=self.user1)
        friend_list2 = FriendList.objects.create(user=self.user2)
        
        friend_list1.friends.add(self.user2)
        friend_list2.friends.add(self.user1)
        
        # Authenticate as user1
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.token1.key}')
        
        # Get friends
        response = self.client.get(self.get_friends_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
    def test_delete_friend(self):
        """Test deleting a friend"""
        # Create friend relationship
        friend_list1 = FriendList.objects.create(user=self.user1)
        friend_list2 = FriendList.objects.create(user=self.user2)
        
        friend_list1.friends.add(self.user2)
        friend_list2.friends.add(self.user1)
        
        # Authenticate as user1
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.token1.key}')
        
        # Delete friendship
        data = {'friend_id': self.user2.id}
        response = self.client.post(self.delete_friend_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Verify they are no longer friends
        self.assertFalse(FriendshipService.are_friends(self.user1, self.user2))
        
        # Test deleting non-existent friendship
        data = {'friend_id': 999}
        response = self.client.post(self.delete_friend_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        
        # Test missing friend_id
        data = {}
        response = self.client.post(self.delete_friend_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)