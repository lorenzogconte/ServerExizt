from django.utils import timezone
from django.db.models import Q
from django.contrib.auth import get_user_model
from .models import Competition, Participant, CompetitionInvitation
from friendships.services import FriendshipService

User = get_user_model()

class CompetitionService:
    
    @staticmethod
    def get_competitions_for_user(user):
        """Get all competitions where the user participates"""
        return Competition.objects.filter(
            participant__user=user
        ).distinct().order_by('-created_at')
    
    @staticmethod
    def get_future_competitions_for_user(user):
        """Get active and upcoming competitions for user"""
        now = timezone.now()
        return Competition.objects.filter(
            participant__user=user,
            end_date__gt=now,
            status__in=['active', 'upcoming']
        ).distinct().order_by('start_date')
    
    @staticmethod
    def get_user_competition_invitations(user):
        """Get all pending invitations for user"""
        return CompetitionInvitation.objects.filter(
            receiver=user,
            status='pending'
        ).order_by('-created_at')
    
    @staticmethod
    def get_user_sent_invitations(user):
        """Get invitations sent by user"""
        return CompetitionInvitation.objects.filter(
            sender=user
        ).order_by('-created_at')
    
    @staticmethod
    def create_competition(title, description, start_date, end_date, creator):
        """Create a new competition"""
        competition = Competition.objects.create(
            title=title,
            description=description,
            start_date=start_date,
            end_date=end_date,
            creator=creator
        )
        
        # Add creator as a participant
        Participant.objects.create(
            user=creator,
            competition=competition
        )
        
        return competition
        
    @staticmethod
    def send_competition_invitation(competition_id, sender, username):
        """Send invitation to join competition"""
        try:
            competition = Competition.objects.get(id=competition_id)
            
            if competition.creator != sender:
                return None, "Only the creator of the competition can send invitations"
            
            receiver = User.objects.get(username=username)
            if not FriendshipService.are_friends(sender, receiver):
                return None, "You can only invite friends to competitions"
        
            if CompetitionInvitation.objects.filter(
                competition=competition,
                receiver=receiver,
                status='pending'
            ).exists():
                return None, "User already invited"
            
            if Participant.objects.filter(
                competition=competition,
                user=receiver
            ).exists():
                return None, "User already participating"
            
            invitation = CompetitionInvitation.objects.create(
                competition=competition,
                sender=sender,
                receiver=receiver
            )
            
            return invitation, None
        except Competition.DoesNotExist:
            return None, "Competition not found"
        except User.DoesNotExist:
            return None, "User not found"
            
    @staticmethod
    def handle_invitation_response(invitation_id, user, action):
        """Accept or decline invitation based on action parameter"""
        try:
            invitation = CompetitionInvitation.objects.get(
                id=invitation_id,
                receiver=user,
                status='pending'
            )
            
            if action == 'accept':
                # Create participant
                Participant.objects.create(
                    user=user,
                    competition=invitation.competition
                )
                invitation.status = 'accepted'
            elif action == 'decline':
                invitation.status = 'declined'
            else:
                return None, "Action must be 'accept' or 'decline'"
            
            invitation.save()
            return invitation, None
        except CompetitionInvitation.DoesNotExist:
            return None, "Invitation not found or already handled"