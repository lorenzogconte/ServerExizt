from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APITestCase, APIClient
from rest_framework.authtoken.models import Token
from rest_framework import status
from .models import User, Profile
from .services import UserService
import tempfile
from PIL import Image
import io

class UserModelTest(TestCase):
    """Tests for the User model"""
    
    def test_create_user(self):
        user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpassword123'
        )
        self.assertEqual(user.username, 'testuser')
        self.assertEqual(user.email, 'test@example.com')
        self.assertTrue(user.check_password('testpassword123'))
        
    def test_user_str(self):
        user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpassword123'
        )
        self.assertEqual(str(user), 'test@example.com')

class ProfileModelTest(TestCase):
    """Tests for the Profile model"""
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpassword123'
        )
        
    def test_create_profile(self):
        profile = Profile.objects.create(
            user=self.user,
            name='Test User'
        )
        self.assertEqual(profile.user, self.user)
        self.assertEqual(profile.name, 'Test User')
        
    def test_profile_str(self):
        profile = Profile.objects.create(
            user=self.user,
            name='Test User'
        )
        self.assertEqual(str(profile), "Test User's Profile")

class UserServiceTest(TestCase):
    """Tests for the UserService class"""
    
    def test_create_user(self):
        user = UserService.create_user(
            username='testuser',
            email='test@example.com',
            password='testpassword123'
        )
        self.assertEqual(user.username, 'testuser')
        self.assertEqual(user.email, 'test@example.com')
        self.assertTrue(user.check_password('testpassword123'))
        
    def test_create_profile(self):
        user = UserService.create_user(
            username='testuser',
            email='test@example.com',
            password='testpassword123'
        )
        profile = UserService.create_profile(user)
        self.assertEqual(profile.user, user)
        self.assertEqual(profile.name, user.username)
        
        # Test with custom name
        profile2 = UserService.create_profile(user, name='Custom Name')
        self.assertEqual(profile2.name, 'Custom Name')
        
    def test_create_auth_token(self):
        user = UserService.create_user(
            username='testuser',
            email='test@example.com',
            password='testpassword123'
        )
        token = UserService.create_auth_token(user)
        self.assertIsNotNone(token)
        self.assertEqual(token.user, user)
        
    def test_authenticate_user(self):
        user = UserService.create_user(
            username='testuser',
            email='test@example.com',
            password='testpassword123'
        )
        
        # Valid credentials
        authenticated_user = UserService.authenticate_user(
            username='testuser',
            password='testpassword123'
        )
        self.assertEqual(authenticated_user, user)
        
        # Invalid credentials
        authenticated_user = UserService.authenticate_user(
            username='testuser',
            password='wrongpassword'
        )
        self.assertIsNone(authenticated_user)
        
    def test_get_or_create_auth_token(self):
        user = UserService.create_user(
            username='testuser',
            email='test@example.com',
            password='testpassword123'
        )
        
        # First call creates a token
        token1 = UserService.get_or_create_auth_token(user)
        self.assertIsNotNone(token1)
        
        # Second call should return the same token
        token2 = UserService.get_or_create_auth_token(user)
        self.assertEqual(token1, token2)
        
    def test_get_user_profile(self):
        user = UserService.create_user(
            username='testuser',
            email='test@example.com',
            password='testpassword123'
        )
        
        # No profile yet
        profile = UserService.get_user_profile(user)
        self.assertIsNone(profile)
        
        # Create profile
        UserService.create_profile(user)
        profile = UserService.get_user_profile(user)
        self.assertIsNotNone(profile)
        self.assertEqual(profile.user, user)
        
    def test_get_user_by_identifier(self):
        user = UserService.create_user(
            username='testuser',
            email='test@example.com',
            password='testpassword123'
        )
        
        # Get by ID
        found_user = UserService.get_user_by_identifier(user.id)
        self.assertEqual(found_user, user)
        
        # Get by username
        found_user = UserService.get_user_by_identifier('testuser', is_username=True)
        self.assertEqual(found_user, user)
        
        # Nonexistent user
        found_user = UserService.get_user_by_identifier(999)
        self.assertIsNone(found_user)
        
    def test_update_profile(self):
        user = UserService.create_user(
            username='testuser',
            email='test@example.com',
            password='testpassword123'
        )
        
        # Update with new name
        success, profile = UserService.update_profile(user, name='New Name')
        self.assertTrue(success)
        self.assertEqual(profile.name, 'New Name')
        
        # Update with new username
        success, profile = UserService.update_profile(user, username='newusername')
        self.assertTrue(success)
        self.assertEqual(user.username, 'newusername')
        
        # Try to update with an existing username
        user2 = UserService.create_user(
            username='existinguser',
            email='existing@example.com',
            password='testpassword123'
        )
        success, error = UserService.update_profile(user, username='existinguser')
        self.assertFalse(success)
        self.assertEqual(error, "Username already taken")
        
    def test_delete_user(self):
        user = UserService.create_user(
            username='testuser',
            email='test@example.com',
            password='testpassword123'
        )
        UserService.create_profile(user)
        
        # Verify user and profile exist
        self.assertTrue(User.objects.filter(id=user.id).exists())
        self.assertTrue(Profile.objects.filter(user=user).exists())
        
        # Delete user
        UserService.delete_user(user)
        
        # Verify user and profile are deleted
        self.assertFalse(User.objects.filter(id=user.id).exists())
        self.assertFalse(Profile.objects.filter(user=user).exists())

class ViewTests(APITestCase):
    """Tests for the API views"""
    
    def setUp(self):
        self.client = APIClient()
        self.signup_url = reverse('signup')
        self.login_url = reverse('login')
        self.isauth_url = reverse('is_authenticated')
        self.profile_url = reverse('profile')
        self.update_profile_url = reverse('update_profile')
        self.delete_user_url = reverse('delete_user')
        
    def create_temp_image(self):
        # Create a temporary image file for testing avatar upload
        image = Image.new('RGB', (100, 100), color='red')
        temp_file = io.BytesIO()
        image.save(temp_file, format='JPEG')
        temp_file.name = 'test.jpg'
        temp_file.seek(0)
        return temp_file
        
    def test_signup(self):
        # Test successful signup
        data = {
            'username': 'testuser',
            'email': 'test@example.com',
            'password': 'testpassword123'
        }
        response = self.client.post(self.signup_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn('token', response.data)
        self.assertIn('user', response.data)
        
        # Test duplicate username
        data = {
            'username': 'testuser',
            'email': 'another@example.com',
            'password': 'testpassword123'
        }
        response = self.client.post(self.signup_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        
    def test_login(self):
        # Create a user
        user = UserService.create_user(
            username='testuser',
            email='test@example.com',
            password='testpassword123'
        )
        UserService.create_profile(user)
        
        # Test successful login
        data = {
            'username': 'testuser',
            'password': 'testpassword123'
        }
        response = self.client.post(self.login_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('token', response.data)
        self.assertIn('user', response.data)
        
        # Test invalid credentials
        data = {
            'username': 'testuser',
            'password': 'wrongpassword'
        }
        response = self.client.post(self.login_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        
    def test_is_authenticated(self):
        # Create a user and get token
        user = UserService.create_user(
            username='testuser',
            email='test@example.com',
            password='testpassword123'
        )
        token = UserService.create_auth_token(user)
        
        # Test without token
        response = self.client.get(self.isauth_url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        
        # Test with token
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {token.key}')
        response = self.client.get(self.isauth_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
    def test_profile(self):
        # Create a user and get token
        user = UserService.create_user(
            username='testuser',
            email='test@example.com',
            password='testpassword123'
        )
        UserService.create_profile(user, name='Test User')
        token = UserService.create_auth_token(user)
        
        # Set token
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {token.key}')
        
        # Get profile
        response = self.client.get(self.profile_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['name'], 'Test User')
        
    def test_update_profile(self):
        # Create a user and get token
        user = UserService.create_user(
            username='testuser',
            email='test@example.com',
            password='testpassword123'
        )
        UserService.create_profile(user)
        token = UserService.create_auth_token(user)
        
        # Set token
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {token.key}')
        
        # Update name
        data = {'name': 'Updated Name'}
        response = self.client.put(self.update_profile_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['name'], 'Updated Name')
        
        # Update username
        data = {'username': 'updateduser'}
        response = self.client.put(self.update_profile_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Update avatar (multipart form)
        avatar = self.create_temp_image()
        data = {'avatar': avatar}
        response = self.client.put(self.update_profile_url, data, format='multipart')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIsNotNone(response.data['avatar'])
        
    def test_delete_user(self):
        # Create a user and get token
        user = UserService.create_user(
            username='testuser',
            email='test@example.com',
            password='testpassword123'
        )
        token = UserService.create_auth_token(user)
        
        # Set token
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {token.key}')
        
        # Delete user
        response = self.client.delete(self.delete_user_url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        
        # Verify user is deleted
        self.assertFalse(User.objects.filter(id=user.id).exists())