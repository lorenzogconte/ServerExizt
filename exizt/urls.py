from django.contrib import admin
from django.urls import path
from users import views as user_views
from friendships import views as friendship_views
from competitions import views as competition_views

import os

print(f"ALLOWED_HOSTS from env: {os.environ.get('ALLOWED_HOSTS')}")

urlpatterns = [
    path('admin/', admin.site.urls),
    # User URLs
    path('signup/', user_views.signup, name='signup'),
    path('login/', user_views.login, name='login'),
    path('isauth/', user_views.is_authenticated, name='is_authenticated'),
    path('profile/', user_views.profile, name='profile'),
    path('profile/update/', user_views.update_profile, name='update_profile'),
    path('profile/delete/', user_views.delete_user, name='delete_user'),
    # Friendship URLs
    path('send-request/', friendship_views.send_friend_request, name='send_friend_request'),
    path('handle-request/', friendship_views.handle_friend_request, name='handle_friend_request'),
    path('requests/', friendship_views.get_friend_requests, name='get_friend_requests'),
    path('delete-friend/', friendship_views.delete_friend, name='delete_friend'),
    path('friendships/', friendship_views.get_friends, name='friendships'),
    path('friend-requests/', friendship_views.get_friend_requests, name='friend_requests'),
    # Competition URLs
    path('competitions/', competition_views.get_competitions, name='get_competitions'),
    path('competitions/create/', competition_views.create_competition, name='create_competition'),
    path('competitions/active/', competition_views.get_active_competitions, name='get_active_competitions'),
    path('competitions/future/', competition_views.get_future_competitions, name='get_future_competitions'),
    path('competitions/<int:competition_id>/', competition_views.get_competition_detail, name='get_competition_detail'),
    path('competitions/<int:competition_id>/leave/', competition_views.leave_competition, name='leave_competition'),
    path('competitions/invitations/', competition_views.get_invitations, name='get_competition_invitations'),
    path('competitions/invitations/send/', competition_views.send_invitation, name='send_competition_invitation'),
    path('competitions/invitations/handle/', competition_views.handle_invitation, name='handle_competition_invitation'),
    path('competitions/screen-time/update/', competition_views.update_screen_time, name='update_screen_time'),
]