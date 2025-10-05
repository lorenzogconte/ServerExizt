from django.test import TestCase, TransactionTestCase
from django.urls import reverse
from django.utils import timezone
from rest_framework.test import APITestCase, APIClient
from rest_framework.authtoken.models import Token
from rest_framework import status
from django.contrib.auth import get_user_model
from datetime import timedelta
from .models import Competition, Participant, CompetitionInvitation
from .services import CompetitionService
from .serializers import CompetitionListSerializer, CompetitionDetailSerializer
from friendships.models import FriendList

User = get_user_model()

class CompetitionModelsTest(TransactionTestCase):
    """Tests for competition models"""
    
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
        self.now = timezone.now()
        self.competition = Competition.objects.create(
            title='Test Competition',
            description='Test Description',
            creator=self.user1,
            start_date=self.now + timedelta(days=1),
            end_date=self.now + timedelta(days=8)
        )
    
    def test_competition_creation(self):
        """Test creating a competition"""
        self.assertEqual(self.competition.title, 'Test Competition')
        self.assertEqual(self.competition.description, 'Test Description')
        self.assertEqual(self.competition.creator, self.user1)
        self.assertEqual(self.competition.status, 'upcoming')
        self.assertIsNone(self.competition.winner)
        
    def test_competition_string_representation(self):
        """Test the string representation of Competition"""
        self.assertEqual(str(self.competition), 'Test Competition')
        
    def test_participant_creation(self):
        """Test creating a participant"""
        participant = Participant.objects.create(
            user=self.user1,
            competition=self.competition
        )
        self.assertEqual(participant.user, self.user1)
        self.assertEqual(participant.competition, self.competition)
        self.assertIsNone(participant.position)
        self.assertIsNone(participant.average_daily_usage)
        
    def test_participant_string_representation(self):
        """Test the string representation of Participant"""
        participant = Participant.objects.create(
            user=self.user1,
            competition=self.competition
        )
        self.assertEqual(str(participant), f"{self.user1} in Test Competition")
        
    def test_invitation_creation(self):
        """Test creating a competition invitation"""
        invitation = CompetitionInvitation.objects.create(
            competition=self.competition,
            sender=self.user1,
            receiver=self.user2
        )
        self.assertEqual(invitation.competition, self.competition)
        self.assertEqual(invitation.sender, self.user1)
        self.assertEqual(invitation.receiver, self.user2)
        self.assertEqual(invitation.status, 'pending')
        
    def test_invitation_string_representation(self):
        """Test the string representation of CompetitionInvitation"""
        invitation = CompetitionInvitation.objects.create(
            competition=self.competition,
            sender=self.user1,
            receiver=self.user2
        )
        self.assertEqual(str(invitation), f"Invitation to Test Competition for {self.user2.username}")
        
    def test_unique_constraints(self):
        """Test unique constraints on models"""
        # Test unique together for participant (user, competition)
        Participant.objects.create(user=self.user1, competition=self.competition)
        with self.assertRaises(Exception):
            Participant.objects.create(user=self.user1, competition=self.competition)
            
        # Test unique together for invitation (competition, receiver)
        CompetitionInvitation.objects.create(
            competition=self.competition,
            sender=self.user1,
            receiver=self.user2
        )
        with self.assertRaises(Exception):
            CompetitionInvitation.objects.create(
                competition=self.competition,
                sender=self.user1,
                receiver=self.user2
            )


class CompetitionServiceTest(TestCase):
    """Tests for the CompetitionService class"""
    
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
        
        self.now = timezone.now()
        
        # Create competitions with different statuses
        self.active_competition = Competition.objects.create(
            title='Active Competition',
            description='Active competition description',
            creator=self.user1,
            start_date=self.now - timedelta(days=1),
            end_date=self.now + timedelta(days=7),
            status='active'
        )
        
        self.upcoming_competition = Competition.objects.create(
            title='Upcoming Competition',
            description='Upcoming competition description',
            creator=self.user1,
            start_date=self.now + timedelta(days=1),
            end_date=self.now + timedelta(days=8),
            status='upcoming'
        )
        
        self.completed_competition = Competition.objects.create(
            title='Completed Competition',
            description='Completed competition description',
            creator=self.user1,
            start_date=self.now - timedelta(days=10),
            end_date=self.now - timedelta(days=3),
            status='completed'
        )
        
        # Add participants
        Participant.objects.create(user=self.user1, competition=self.active_competition)
        Participant.objects.create(user=self.user2, competition=self.active_competition)
        Participant.objects.create(user=self.user1, competition=self.upcoming_competition)
        Participant.objects.create(user=self.user1, competition=self.completed_competition)
        
        # Set up friendships for invitation tests
        self.friend_list1 = FriendList.objects.create(user=self.user1)
        self.friend_list2 = FriendList.objects.create(user=self.user2)
        self.friend_list1.friends.add(self.user2)
        self.friend_list2.friends.add(self.user1)
        
    def test_get_competitions_for_user(self):
        """Test getting all competitions for a user"""
        # User1 has 3 competitions
        competitions = CompetitionService.get_competitions_for_user(self.user1)
        self.assertEqual(competitions.count(), 3)
        
        # User2 has 1 competition
        competitions = CompetitionService.get_competitions_for_user(self.user2)
        self.assertEqual(competitions.count(), 1)
        
        # User3 has 0 competitions
        competitions = CompetitionService.get_competitions_for_user(self.user3)
        self.assertEqual(competitions.count(), 0)
        
    def test_get_future_competitions_for_user(self):
        """Test getting future competitions for a user"""
        # User1 has 2 future competitions (active and upcoming)
        competitions = CompetitionService.get_future_competitions_for_user(self.user1)
        self.assertEqual(competitions.count(), 2)
        
        # User2 has 1 future competition (active)
        competitions = CompetitionService.get_future_competitions_for_user(self.user2)
        self.assertEqual(competitions.count(), 1)
        
    def test_create_competition(self):
        """Test creating a competition"""
        title = "New Competition"
        description = "New competition description"
        start_date = self.now + timedelta(days=2)
        end_date = self.now + timedelta(days=9)
        
        competition = CompetitionService.create_competition(
            title=title,
            description=description,
            start_date=start_date,
            end_date=end_date,
            creator=self.user3
        )
        
        # Verify competition data
        self.assertEqual(competition.title, title)
        self.assertEqual(competition.description, description)
        self.assertEqual(competition.creator, self.user3)
        self.assertEqual(competition.status, 'upcoming')
        
        # Verify creator is added as participant
        self.assertTrue(Participant.objects.filter(
            user=self.user3, 
            competition=competition
        ).exists())
        
    def test_send_competition_invitation(self):
        """Test sending a competition invitation"""
        # Test successful invitation
        invitation, error = CompetitionService.send_competition_invitation(
            competition_id=self.active_competition.id,
            sender=self.user1,
            username=self.user2.username
        )
        
        # Should fail because user2 is already participating
        self.assertIsNone(invitation)
        self.assertIsNotNone(error)
        
        # Try inviting a non-participant who is a friend
        invitation, error = CompetitionService.send_competition_invitation(
            competition_id=self.upcoming_competition.id,
            sender=self.user1,
            username=self.user2.username
        )
        
        # Should succeed
        self.assertIsNotNone(invitation)
        self.assertIsNone(error)
        self.assertEqual(invitation.competition, self.upcoming_competition)
        self.assertEqual(invitation.sender, self.user1)
        self.assertEqual(invitation.receiver, self.user2)
        
        # Try inviting a non-friend
        invitation, error = CompetitionService.send_competition_invitation(
            competition_id=self.upcoming_competition.id,
            sender=self.user1,
            username=self.user3.username
        )
        
        # Should fail
        self.assertIsNone(invitation)
        self.assertIsNotNone(error)
        
        # Try inviting as non-creator
        invitation, error = CompetitionService.send_competition_invitation(
            competition_id=self.active_competition.id,
            sender=self.user2,
            username=self.user3.username
        )
        
        # Should fail
        self.assertIsNone(invitation)
        self.assertIsNotNone(error)
        
    def test_handle_invitation_response(self):
        """Test handling invitation responses"""
        # Create an invitation
        invitation = CompetitionInvitation.objects.create(
            competition=self.upcoming_competition,
            sender=self.user1,
            receiver=self.user3
        )
        
        # Test accepting invitation
        updated_invitation, error = CompetitionService.handle_invitation_response(
            invitation_id=invitation.id,
            user=self.user3,
            action='accept'
        )
        
        # Should succeed
        self.assertIsNotNone(updated_invitation)
        self.assertIsNone(error)
        self.assertEqual(updated_invitation.status, 'accepted')
        
        # Verify user is now a participant
        self.assertTrue(Participant.objects.filter(
            user=self.user3, 
            competition=self.upcoming_competition
        ).exists())
        
        # Create another invitation
        invitation = CompetitionInvitation.objects.create(
            competition=self.active_competition,
            sender=self.user1,
            receiver=self.user3
        )
        
        # Test declining invitation
        updated_invitation, error = CompetitionService.handle_invitation_response(
            invitation_id=invitation.id,
            user=self.user3,
            action='decline'
        )
        
        # Should succeed
        self.assertIsNotNone(updated_invitation)
        self.assertIsNone(error)
        self.assertEqual(updated_invitation.status, 'declined')
        
        # Verify user is NOT a participant
        self.assertFalse(Participant.objects.filter(
            user=self.user3, 
            competition=self.active_competition
        ).exists())
        
        # Test invalid action
        updated_invitation, error = CompetitionService.handle_invitation_response(
            invitation_id=invitation.id,
            user=self.user3,
            action='invalid'
        )
        
        # Should fail
        self.assertIsNone(updated_invitation)
        self.assertIsNotNone(error)
        
    def test_get_competition_leaderboard(self):
        """Test getting competition leaderboard"""
        # Create participants with different screen times
        participant1 = Participant.objects.get(user=self.user1, competition=self.active_competition)
        participant2 = Participant.objects.get(user=self.user2, competition=self.active_competition)
        
        participant1.average_daily_usage = 30.0
        participant1.position = 1
        participant1.save()
        
        participant2.average_daily_usage = 60.0
        participant2.position = 2
        participant2.save()
        
        # Add a participant with no screen time
        participant3 = Participant.objects.create(
            user=self.user3, 
            competition=self.active_competition
        )
        
        # Get leaderboard
        ranked, unranked = CompetitionService.get_competition_leaderboard(self.active_competition)
        
        # Should have 2 ranked participants
        self.assertEqual(ranked.count(), 2)
        
        # Should have 1 unranked participant
        self.assertEqual(unranked.count(), 1)
        
        # First ranked should be user1 (less screen time)
        self.assertEqual(ranked.first().user, self.user1)
        
    def test_update_user_screen_time(self):
        """Test updating user screen time"""
        # Initial state - no screen time
        participant = Participant.objects.get(user=self.user1, competition=self.active_competition)
        self.assertIsNone(participant.average_daily_usage)
        self.assertIsNone(participant.position)
        
        # Update screen time
        updated_competitions = CompetitionService.update_user_screen_time(
            user=self.user1,
            date=self.now.date(),
            screen_time_minutes=30.0
        )
        
        # Should update 1 competition (active)
        self.assertEqual(len(updated_competitions), 1)
        self.assertEqual(updated_competitions[0], self.active_competition)
        
        # Check participant data is updated
        participant.refresh_from_db()
        self.assertEqual(participant.average_daily_usage, 30.0)
        self.assertEqual(participant.position, 1)
        
        # Update screen time for user2
        CompetitionService.update_user_screen_time(
            user=self.user2,
            date=self.now.date(),
            screen_time_minutes=20.0
        )
        
        # Check rankings are updated - user2 should be position 1 now (less screen time)
        participant1 = Participant.objects.get(user=self.user1, competition=self.active_competition)
        participant2 = Participant.objects.get(user=self.user2, competition=self.active_competition)
        
        self.assertEqual(participant2.position, 1)
        self.assertEqual(participant1.position, 2)
        
    def test_recalculate_competition_rankings(self):
        """Test recalculating competition rankings"""
        # Set up participants with screen time
        participant1 = Participant.objects.get(user=self.user1, competition=self.active_competition)
        participant2 = Participant.objects.get(user=self.user2, competition=self.active_competition)
        participant3 = Participant.objects.create(
            user=self.user3, 
            competition=self.active_competition
        )
        
        participant1.average_daily_usage = 45.0
        participant1.save()
        
        participant2.average_daily_usage = 30.0
        participant2.save()
        
        # Recalculate rankings
        CompetitionService.recalculate_competition_rankings(self.active_competition)
        
        # Refresh from database
        participant1.refresh_from_db()
        participant2.refresh_from_db()
        participant3.refresh_from_db()
        
        # Check positions
        self.assertEqual(participant2.position, 1)  # Less screen time = better position
        self.assertEqual(participant1.position, 2)
        self.assertEqual(participant3.position, 3)  # No screen time = last position


class CompetitionAPITest(APITestCase):
    """Tests for the competition API endpoints"""
    
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
        
        # Create tokens
        self.token1 = Token.objects.create(user=self.user1)
        self.token2 = Token.objects.create(user=self.user2)
        self.token3 = Token.objects.create(user=self.user3)
        
        # Set up friendships
        self.friend_list1 = FriendList.objects.create(user=self.user1)
        self.friend_list2 = FriendList.objects.create(user=self.user2)
        
        self.friend_list1.friends.add(self.user2)
        self.friend_list2.friends.add(self.user1)
        
        # Set up time references
        self.now = timezone.now()
        
        # Create competitions
        self.active_competition = Competition.objects.create(
            title='Active Competition',
            description='Active competition description',
            creator=self.user1,
            start_date=self.now - timedelta(days=1),
            end_date=self.now + timedelta(days=7),
            status='active'
        )
        
        self.upcoming_competition = Competition.objects.create(
            title='Upcoming Competition',
            description='Upcoming competition description',
            creator=self.user1,
            start_date=self.now + timedelta(days=1),
            end_date=self.now + timedelta(days=8),
            status='upcoming'
        )
        
        # Add participants
        Participant.objects.create(user=self.user1, competition=self.active_competition)
        Participant.objects.create(user=self.user2, competition=self.active_competition)
        Participant.objects.create(user=self.user1, competition=self.upcoming_competition)
        
        # Define URLs
        self.competitions_url = reverse('get_competitions')
        self.future_competitions_url = reverse('get_future_competitions')
        self.active_competitions_url = reverse('get_active_competitions')
        self.create_competition_url = reverse('create_competition')
        self.invitations_url = reverse('get_competition_invitations')
        self.send_invitation_url = reverse('send_competition_invitation')
        self.handle_invitation_url = reverse('handle_competition_invitation')
        self.screen_time_url = reverse('update_screen_time')
        
    def get_competition_detail_url(self, competition_id):
        return reverse('get_competition_detail', args=[competition_id])
        
    def leave_competition_url(self, competition_id):
        return reverse('leave_competition', args=[competition_id])
        
    def test_get_competitions(self):
        """Test getting all competitions for a user"""
        # Authenticate as user1
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.token1.key}')
        
        # Get competitions
        response = self.client.get(self.competitions_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Should have 2 competitions
        self.assertEqual(len(response.data), 2)
        
        # Authenticate as user2
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.token2.key}')
        
        # Get competitions
        response = self.client.get(self.competitions_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Should have 1 competition
        self.assertEqual(len(response.data), 1)
        
    def test_get_future_competitions(self):
        """Test getting future competitions for a user"""
        # Authenticate as user1
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.token1.key}')
        
        # Get future competitions
        response = self.client.get(self.future_competitions_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Should have 2 competitions (active and upcoming)
        self.assertEqual(len(response.data), 2)
        
        # Authenticate as user2
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.token2.key}')
        
        # Get future competitions
        response = self.client.get(self.future_competitions_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Should have 1 competition (active)
        self.assertEqual(len(response.data), 1)
        
    def test_get_competition_detail(self):
        """Test getting competition details"""
        # Authenticate as user1
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.token1.key}')
        
        # Get competition detail
        url = self.get_competition_detail_url(self.active_competition.id)
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Check response structure
        self.assertEqual(response.data['title'], 'Active Competition')
        self.assertTrue('leaderboard' in response.data)
        self.assertTrue('total_participants' in response.data)
        
        # Authenticate as user3 (not a participant)
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.token3.key}')
        
        # Try to get competition detail
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        
        # Try nonexistent competition
        url = self.get_competition_detail_url(999)
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        
    def test_create_competition(self):
        """Test creating a competition"""
        # Authenticate as user1
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.token1.key}')
        
        # Create competition data
        data = {
            'title': 'New Test Competition',
            'description': 'New test competition description',
            'start_date': (self.now + timedelta(days=2)).isoformat(),
            'end_date': (self.now + timedelta(days=9)).isoformat()
        }
        
        # Create competition
        response = self.client.post(self.create_competition_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        # Check response data
        self.assertEqual(response.data['title'], 'New Test Competition')
        
        # Verify competition exists in database
        competition_id = response.data['id']
        self.assertTrue(Competition.objects.filter(id=competition_id).exists())
        
        # Verify user is a participant
        self.assertTrue(Participant.objects.filter(
            user=self.user1,
            competition_id=competition_id
        ).exists())
        
    def test_send_invitation(self):
        """Test sending a competition invitation"""
        # Authenticate as user1
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.token1.key}')
        
        # Send invitation to user2 for upcoming competition
        data = {
            'competition_id': self.upcoming_competition.id,
            'username': 'testuser2'
        }
        
        response = self.client.post(self.send_invitation_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        # Verify invitation exists
        invitation_id = response.data['id']
        self.assertTrue(CompetitionInvitation.objects.filter(id=invitation_id).exists())
        
        # Try sending again (should fail - already invited)
        response = self.client.post(self.send_invitation_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        
        # Try sending as non-creator
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.token2.key}')
        response = self.client.post(self.send_invitation_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        
    def test_handle_invitation(self):
        """Test handling a competition invitation"""
        # Create invitation
        invitation = CompetitionInvitation.objects.create(
            competition=self.upcoming_competition,
            sender=self.user1,
            receiver=self.user2
        )
        
        # Authenticate as user2
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.token2.key}')
        
        # Accept invitation
        data = {
            'invitation_id': invitation.id,
            'action': 'accept'
        }
        
        response = self.client.post(self.handle_invitation_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Verify user is now a participant
        self.assertTrue(Participant.objects.filter(
            user=self.user2,
            competition=self.upcoming_competition
        ).exists())
        
        # Try handling again (should fail - already handled)
        response = self.client.post(self.handle_invitation_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        
        # Create another invitation
        invitation = CompetitionInvitation.objects.create(
            competition=self.active_competition,
            sender=self.user1,
            receiver=self.user3
        )
        
        # Authenticate as user3
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.token3.key}')
        
        # Decline invitation
        data = {
            'invitation_id': invitation.id,
            'action': 'decline'
        }
        
        response = self.client.post(self.handle_invitation_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Verify user is NOT a participant
        self.assertFalse(Participant.objects.filter(
            user=self.user3,
            competition=self.active_competition
        ).exists())
        
    def test_leave_competition(self):
        """Test leaving a competition"""
        # Authenticate as user2
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.token2.key}')
        
        # Leave competition
        url = self.leave_competition_url(self.active_competition.id)
        response = self.client.post(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Verify user is no longer a participant
        self.assertFalse(Participant.objects.filter(
            user=self.user2,
            competition=self.active_competition
        ).exists())
        
        # Try leaving as creator (should fail)
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.token1.key}')
        response = self.client.post(url)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        
        # Try leaving a nonexistent competition
        url = self.leave_competition_url(999)
        response = self.client.post(url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        
    def test_update_screen_time(self):
        """Test updating screen time"""
        # Authenticate as user1
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.token1.key}')
        
        # Initial state - no screen time
        participant = Participant.objects.get(
            user=self.user1,
            competition=self.active_competition
        )
        self.assertIsNone(participant.average_daily_usage)
        
        # Update screen time
        data = {
            'screen_time_minutes': 45.0,
            'date': self.now.date().isoformat()
        }
        
        response = self.client.post(self.screen_time_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Check response
        self.assertEqual(len(response.data['updated_competitions']), 1)
        
        # Verify participant data is updated
        participant.refresh_from_db()
        self.assertEqual(participant.average_daily_usage, 45.0)
        self.assertEqual(participant.position, 1)
        
        # Try with invalid data
        data = {
            'screen_time_minutes': -10.0
        }
        
        response = self.client.post(self.screen_time_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)