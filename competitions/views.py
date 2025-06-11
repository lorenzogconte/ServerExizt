from rest_framework.decorators import api_view, authentication_classes, permission_classes
from rest_framework.authentication import TokenAuthentication
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from .models import Competition, Participant, CompetitionInvitation
from .serializers import CompetitionListSerializer, CompetitionDetailSerializer, ParticipantSerializer, CompetitionInvitationSerializer
from .services import CompetitionService
from django.utils import timezone

@api_view(['GET'])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated])
def get_competitions(request):
    """Get all competitions for the authenticated user"""
    competitions = CompetitionService.get_competitions_for_user(request.user)
    serializer = CompetitionListSerializer(competitions, many=True)
    return Response(serializer.data, status=status.HTTP_200_OK)

@api_view(['GET'])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated])
def get_future_competitions(request):
    """Get all active and upcoming competitions for the authenticated user"""
    competitions = CompetitionService.get_future_competitions_for_user(request.user)
    serializer = CompetitionListSerializer(competitions, many=True)
    return Response(serializer.data, status=status.HTTP_200_OK)

@api_view(['GET'])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated])
def get_competition_detail(request, competition_id):
    """Get detailed information about a specific competition"""
    try:
        competition = Competition.objects.get(id=competition_id)
        
        # Check if user is a participant
        if not Participant.objects.filter(competition=competition, user=request.user).exists():
            return Response({"error": "You don't have access to this competition"}, 
                           status=status.HTTP_403_FORBIDDEN)
        
        # Get competition data
        comp_serializer = CompetitionDetailSerializer(competition)
        
        # Get participants data
        participants = Participant.objects.filter(competition=competition).order_by('position')
        part_serializer = ParticipantSerializer(participants, many=True)
        
        # Combine data
        response_data = comp_serializer.data
        response_data['participants'] = part_serializer.data
        
        return Response(response_data, status=status.HTTP_200_OK)
    except Competition.DoesNotExist:
        return Response({"error": "Competition not found"}, status=status.HTTP_404_NOT_FOUND)

@api_view(['GET'])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated])
def get_active_competitions(request):
    """Get all active competitions for the user"""
    competitions = CompetitionService.get_future_competitions_for_user(request.user)
    serializer = CompetitionListSerializer(competitions, many=True)
    return Response(serializer.data, status=status.HTTP_200_OK)

@api_view(['POST'])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated])
def create_competition(request):
    """Create a new competition"""
    serializer = CompetitionDetailSerializer(data=request.data)
    
    if serializer.is_valid():
        # Create competition using service
        competition = CompetitionService.create_competition(
            title=serializer.validated_data['title'],
            description=serializer.validated_data.get('description', ''),
            start_date=serializer.validated_data['start_date'],
            end_date=serializer.validated_data['end_date'],
            creator=request.user
        )
        
        # Return the created competition
        result = CompetitionDetailSerializer(competition)
        return Response(result.data, status=status.HTTP_201_CREATED)
    
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['GET'])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated])
def get_invitations(request):
    """Get all pending invitations for the user"""
    invitations = CompetitionService.get_user_competition_invitations(request.user)
    serializer = CompetitionInvitationSerializer(invitations, many=True)
    return Response(serializer.data, status=status.HTTP_200_OK)

@api_view(['POST'])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated])
def send_invitation(request):
    """Send invitation to join competition"""
    print("Request Data:", request.data)
    competition_id = request.data.get('competition_id')
    username = request.data.get('username')
    
    if not competition_id or not username:
        return Response(
            {"error": "Competition ID and receiver ID are required"}, 
            status=status.HTTP_400_BAD_REQUEST
        )
    
    invitation, error = CompetitionService.send_competition_invitation(
        competition_id=competition_id,
        sender=request.user,
        username=username
    )
    
    if error:
        return Response({"error": error}, status=status.HTTP_400_BAD_REQUEST)
    
    serializer = CompetitionInvitationSerializer(invitation)
    return Response(serializer.data, status=status.HTTP_201_CREATED)

@api_view(['POST'])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated])
def handle_invitation(request):
    """Accept or decline an invitation"""
    invitation_id = request.data.get('invitation_id')
    action = request.data.get('action')
    
    if not invitation_id:
        return Response({"error": "Invitation ID is required"}, status=status.HTTP_400_BAD_REQUEST)
    
    if action not in ['accept', 'decline']:
        return Response({"error": "Action must be 'accept' or 'decline'"}, status=status.HTTP_400_BAD_REQUEST)
    
    invitation, error = CompetitionService.handle_invitation_response(
        invitation_id=invitation_id,
        user=request.user,
        action=action
    )
    
    if error:
        return Response({"error": error}, status=status.HTTP_400_BAD_REQUEST)
    
    serializer = CompetitionInvitationSerializer(invitation)
    return Response({
        "success": f"Invitation {action}ed",
        "invitation": serializer.data
    }, status=status.HTTP_200_OK)

@api_view(['POST'])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated])
def leave_competition(request, competition_id):
    """Leave a competition"""
    try:
        # Check if competition exists
        competition = Competition.objects.get(id=competition_id)
        
        # Can't leave if you're the creator
        if competition.creator == request.user:
            return Response(
                {"error": "Competition creator cannot leave the competition"}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Check if user is a participant
        participant = Participant.objects.filter(competition=competition, user=request.user).first()
        if not participant:
            return Response(
                {"error": "You are not participating in this competition"}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Delete participant entry
        participant.delete()
        
        return Response(
            {"success": f"You have left the competition '{competition.title}'"}, 
            status=status.HTTP_200_OK
        )
    except Competition.DoesNotExist:
        return Response({"error": "Competition not found"}, status=status.HTTP_404_NOT_FOUND)