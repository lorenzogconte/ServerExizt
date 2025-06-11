from .models import Profile
from .serializers import UserSerializer, ProfileSerializer, LoginSerializer
from rest_framework.decorators import api_view, authentication_classes, permission_classes, parser_classes
from rest_framework.response import Response
from rest_framework import status
from django.shortcuts import get_object_or_404
from rest_framework.permissions import IsAuthenticated
from rest_framework.authentication import TokenAuthentication
from .services import UserService
from rest_framework.parsers import MultiPartParser, FormParser
from django.conf import settings

@api_view(['POST'])
def signup(request):
    serializer = UserSerializer(data=request.data)
    print("Request data: ", request.data)
    
    if serializer.is_valid():
        user = UserService.create_user(
            username=serializer.validated_data['username'],
            email=serializer.validated_data['email'],
            password=serializer.validated_data['password']
        )
        UserService.create_profile(
            user=user,
            name=request.data.name,
        )
        token = UserService.create_auth_token(user)
        return Response(
            {'token': token.key, 'user': UserSerializer(user).data}, 
            status=status.HTTP_201_CREATED
        )
    else:
        print("Validation errors: ", serializer.errors)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['POST'])
def login(request):
    serializer = LoginSerializer(data=request.data)
    if serializer.is_valid():
        user = UserService.authenticate_user(
            username=serializer.validated_data['username'],
            password=serializer.validated_data['password']
        )
        if user:
            token = UserService.get_or_create_auth_token(user)
            profile = UserService.get_user_profile(user)
            return Response(
                {'token': token.key, 'user': ProfileSerializer(profile).data}, 
                status=status.HTTP_200_OK
            )
        return Response({'error': 'Invalid credentials'}, status=status.HTTP_401_UNAUTHORIZED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['GET'])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated])
def is_authenticated(request):
    return Response({"message": "The user is authenticated"}, status=status.HTTP_200_OK)

@api_view(['GET'])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated])
def profile(request):
    print("Request user: ", request.user)
    profile = UserService.get_user_profile(request.user)
    if not profile:
        profile = UserService.create_profile(request.user)
    serializer = ProfileSerializer(profile)
    print("Profile data: ", serializer.data)
    return Response(serializer.data, status=status.HTTP_200_OK)

@api_view(['PUT'])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated])
@parser_classes([MultiPartParser, FormParser])
def update_profile(request):
    profile = UserService.get_user_profile(request.user)
    if not profile:
        profile = UserService.create_profile(request.user)
    
    # Extract fields from request
    username = request.data.get('username')
    name = request.data.get('name')
    avatar = request.FILES.get('avatar')  # Get the uploaded file
    
    success, result = UserService.update_profile(
        user=request.user,
        username=username,
        name=name,
        avatar=avatar  # Pass the file object directly
    )
    
    if success:
        return Response(ProfileSerializer(result).data, status=status.HTTP_200_OK)
    else:
        return Response({'error': result}, status=status.HTTP_400_BAD_REQUEST)

@api_view(['DELETE'])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated])
def delete_user(request):
    UserService.delete_user(request.user)
    return Response(status=status.HTTP_204_NO_CONTENT)