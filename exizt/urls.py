"""
URL configuration for exizt project.
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path
from users import views as user_views
from friendships import views as friendship_views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('signup/', user_views.signup, name='signup'),
    path('login/', user_views.login, name='login'),
    path('isauth/', user_views.is_authenticated, name='is_authenticated'),
    path('profile/', user_views.profile, name='profile'),
    path('send-request/', friendship_views.send_friend_request, name='send_friend_request'),
    path('handle-request/', friendship_views.handle_friend_request, name='handle_friend_request'),
    path('requests/', friendship_views.get_friend_requests, name='get_friend_requests'),
    path('delete-friend/', friendship_views.delete_friend, name='delete_friend'),
    path('friendships/', friendship_views.get_friends, name='friendships'),
]