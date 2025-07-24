from django.urls import path
from . import views

app_name = 'station'

urlpatterns = [
    path('', views.home, name='home'),
    path('login/', views.user_login, name='login'),
    path('logout/', views.user_logout, name='logout'),
    path('register/', views.user_register, name='register'),
    path('profile/', views.profile, name='profile'),
    path('callback', views.callback, name='callback'), 
    path('connect-spotify/', views.connect_spotify, name='connect_spotify'),
    path('disconnect-spotify/', views.disconnect_spotify, name='disconnect_spotify'),
    path('spotify-player-api/', views.spotify_player_api, name='spotify_player_api'),
    #path('api/create-playlist/', views.create_playlist, name='create_playlist'),
    path('api/get-recommendations/', views.get_recommendations, name='get_recommendations'),
    path('api/play/', views.play, name='play'),
    path('api/pause/', views.pause, name='pause'),
    path('api/get-playing-track/', views.get_playing_track, name='get_playing_track'),
    path('api/get-voice/<str:just_played>/<str:next_song>/', views.get_voice, name='get_voice'),
    path('api/get-next-track/', views.get_next_track, name='get_next_track'),
]
