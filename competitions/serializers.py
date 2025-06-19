from rest_framework import serializers
from .models import Competition, Participant, CompetitionInvitation
from users.serializers import UserSerializer

class ParticipantSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    
    class Meta:
        model = Participant
        fields = ['id', 'user', 'joined_at', 'position', 'average_daily_usage']

class CompetitionListSerializer(serializers.ModelSerializer):
    creator = UserSerializer(read_only=True)
    participant_count = serializers.SerializerMethodField()
    is_creator = serializers.SerializerMethodField()
    
    class Meta:
        model = Competition
        fields = [
            'id', 'title', 'description', 'start_date', 'end_date', 
            'status', 'creator', 'participant_count', 'created_at',
            'is_creator'
        ]

    def get_participant_count(self, obj):
        return Participant.objects.filter(competition=obj).count()
    
    def get_is_creator(self, obj):
        request = self.context.get('request')
        if request and hasattr(request, 'user'):
            return obj.creator.id == request.user.id
        return False
    
class CompetitionDetailSerializer(serializers.ModelSerializer):
    creator = UserSerializer(read_only=True)
    winner = UserSerializer(read_only=True)
    participants = serializers.SerializerMethodField()
    is_creator = serializers.SerializerMethodField()
    
    class Meta:
        model = Competition
        fields = [
            'id', 'title', 'description', 'start_date', 'end_date', 
            'status', 'creator', 'winner', 'participants', 'created_at',
            'is_creator'
        ]

    def get_participants(self, obj):
        participants = obj.participant_set.all()
        return ParticipantSerializer(participants, many=True).data
    
    def get_is_creator(self, obj):
        request = self.context.get('request')
        if request and hasattr(request, 'user'):
            return obj.creator.id == request.user.id
        return False
    
class CompetitionInvitationSerializer(serializers.ModelSerializer):
    sender = UserSerializer(read_only=True)
    receiver = UserSerializer(read_only=True)
    competition = CompetitionListSerializer(read_only=True)
    
    class Meta:
        model = CompetitionInvitation
        fields = ['id', 'competition', 'sender', 'receiver', 'status', 'created_at']