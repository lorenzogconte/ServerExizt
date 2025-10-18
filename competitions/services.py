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
        
    @staticmethod
    def get_competition_leaderboard(competition):
        """
        Get pre-ordered participants for a competition's leaderboard
        This doesn't recalculate rankings - just returns current state
        """
        # Get participants with screen time, ordered by position
        ranked = Participant.objects.filter(
            competition=competition,
            average_daily_usage__isnull=False,
            position__isnull=False
        ).select_related('user').order_by('position')
        
        # Get participants without screen time
        unranked = Participant.objects.filter(
            competition=competition
        ).filter(
            Q(average_daily_usage__isnull=True) | Q(position__isnull=True)
        ).select_related('user')
        
        # Use iterator instead of list for better memory efficiency
        return ranked, unranked
        
    @staticmethod
    def update_user_screen_time(user, date, screen_time_minutes):
        """
        Update a user's screen time and recalculate rankings in all active competitions
        
        Args:
            user: The user whose screen time is being updated
            date: The date for this screen time data
            screen_time_minutes: Screen time in minutes
        
        Returns:
            List of competitions where ranking was updated
        """
        # Get all active competitions where the user is a participant (use only date range, not DB status)
        now = timezone.now()
        active_competitions = Competition.objects.filter(
            participant__user=user,
            start_date__lte=now,
            end_date__gte=now
        ).distinct()
        updated_competitions = []
        for competition in active_competitions:
            # Get participant record for this user in this competition
            participant = Participant.objects.get(user=user, competition=competition)
            old_usage = participant.average_daily_usage
            # Update average daily usage (you might want a more sophisticated algorithm here)
            if participant.average_daily_usage is None:
                participant.average_daily_usage = screen_time_minutes
            else:
                # Simple moving average (could be improved with more historical data)
                participant.average_daily_usage = (participant.average_daily_usage + screen_time_minutes) / 2
            participant.save()
            updated_competitions.append(competition)
            # Recalculate rankings for all participants in this competition
            CompetitionService.recalculate_competition_rankings(competition)
        return updated_competitions

    @staticmethod
    def recalculate_competition_rankings(competition):
        """
        Recalculate rankings for all participants in a competition.
        Lower screen time means better ranking (lower position number).
        
        Args:
            competition: The competition to recalculate rankings for
        """
        # Get all participants ordered by average_daily_usage (ascending - less is better)
        participants = Participant.objects.filter(
            competition=competition,
            average_daily_usage__isnull=False
        ).order_by('average_daily_usage')
        
        # Update positions
        for i, participant in enumerate(participants, 1):
            participant.position = i
            participant.save()
        
        # Handle participants with no data yet (place them at the end)
        participants_no_data = Participant.objects.filter(
            competition=competition,
            average_daily_usage__isnull=True
        )
        
        last_position = participants.count() + 1
        
        for participant in participants_no_data:
            participant.position = last_position
            participant.save()