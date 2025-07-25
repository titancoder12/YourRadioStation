from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth.decorators import login_required
from django.contrib import messages
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials, SpotifyOAuth
from spotipy.client import Spotify
#from spotipy.client import SpotifyAPI
from django.conf import settings
from django.shortcuts import redirect
import urllib.parse
import requests
from .models import UserProfile
from django.http import JsonResponse
from django.utils import timezone
from datetime import timedelta
from django.views.decorators.csrf import csrf_exempt
import json
import requests
from gtts import gTTS
from groq import Groq
import os

def home(request):
    """Home page view - shows different content for logged in vs anonymous users"""
    return render(request, 'station/home.html')

def user_login(request):
    """Handle user login"""
    if request.user.is_authenticated:
        return redirect('station:home')
    
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(username=username, password=password)
            if user is not None:
                login(request, user)
                messages.success(request, f'Welcome back, {username}!')
                return redirect('station:home')
        else:
            messages.error(request, 'Invalid username or password.')
    
    form = AuthenticationForm()
    return render(request, 'station/login.html', {'form': form})

def user_logout(request):
    """Handle user logout"""
    if request.user.is_authenticated:
        messages.success(request, f'Goodbye, {request.user.username}!')
        logout(request)
    return redirect('station:home')

def user_register(request):
    """Handle user registration"""
    if request.user.is_authenticated:
        return redirect('station:home')
    
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            username = form.cleaned_data.get('username')
            messages.success(request, f'Account created for {username}!')
            login(request, user)
            return redirect('station:home')
        else:
            messages.error(request, 'Please correct the errors below.')
    
    form = UserCreationForm()
    return render(request, 'station/register.html', {'form': form})

@login_required
def profile(request):
    """User profile view - shows Spotify connection status"""
    if not request.user.is_authenticated:
        messages.warning(request, 'Please log in to view your profile.')
        return redirect('station:login')
    
    profile = UserProfile.objects.get(user=request.user)

    return render(request, 'station/profile.html', {'profile': profile})

@login_required
def callback(request):
    """Handle Spotify callback after authentication"""
    # Get the authorization code from Spotify
    code = request.GET.get('code')
    error = request.GET.get('error')
    
    if error:
        messages.error(request, f'Spotify authorization failed: {error}')
        return redirect('station:home')
    
    if not code:
        messages.error(request, 'No authorization code received from Spotify')
        return redirect('station:home')
    
    if request.user.is_authenticated:
        # Exchange authorization code for access token
        token_url = 'https://accounts.spotify.com/api/token'
        token_data = {
            'grant_type': 'authorization_code',
            'code': code,
            'redirect_uri': settings.SPOTIFY_REDIRECT_URI,
            'client_id': settings.SPOTIFY_CLIENT_ID,
            'client_secret': settings.SPOTIFY_CLIENT_SECRET,
        }
        
        try:
            response = requests.post(token_url, data=token_data)
            token_info = response.json()
            print(token_info)
            
            if response.status_code == 200:
                # Store the access token and refresh token
                profile = request.user.userprofile
                #profile.spotify_display_name = token_info.get('display_name')
                #profile.spotify_email = token_info.get('email')
                #profile.spotify_subscription = token_info.get('product')
                expires_in_seconds = token_info.get('expires_in', 3600)  # Default to 1 hour
                profile.spotify_token_expires_at = timezone.now() + timedelta(seconds=expires_in_seconds)
                profile.spotify_access_token = token_info.get('access_token')
                profile.spotify_refresh_token = token_info.get('refresh_token')
                profile.connected_to_spotify = True
                profile.save()

                # Get more details from Spotify API
                user_info = make_spotify_request('https://api.spotify.com/v1/me', profile.spotify_access_token)
        
                if user_info:
                    profile.spotify_display_name = user_info.get('display_name')
                    profile.spotify_email = user_info.get('email')
                    profile.spotify_subscription = user_info.get('product')
                    profile.save()
                    messages.success(request, f'Successfully connected to Spotify as {profile.spotify_display_name}!')
                
                print(profile)
            else:
                messages.error(request, f'Failed to get access token: {token_info.get("error_description", "Unknown error")}')
        except Exception as e:
            messages.error(request, f'Error connecting to Spotify: {str(e)}')
    else:
        messages.warning(request, 'Please log in first to connect your Spotify account')
    
    return redirect('station:home')

def make_spotify_request(url, access_token, method='GET'):
    """Helper function to make Spotify API requests"""
    try:
        headers = {'Authorization': f'Bearer {access_token}'}
        if method == 'GET':
            response = requests.get(url, headers=headers)
        else:
            response = requests.post(url, headers=headers)
        
        if response.status_code == 200:
            return response.json()
        else:
            print(f"Spotify API error: {response.status_code}, {response.text}")
            return None
    except Exception as e:
        print(f"Error making Spotify request: {e}")

@login_required
def connect_spotify(request):
    """Redirect user to Spotify authorization"""
    auth_url = 'https://accounts.spotify.com/authorize'
    params = {
        'client_id': settings.SPOTIFY_CLIENT_ID,
        'response_type': 'code',
        'redirect_uri': settings.SPOTIFY_REDIRECT_URI,
        'scope': settings.SPOTIFY_SCOPES,
        'state': 'random_csrf_token',
    }
    url = f"{auth_url}?{urllib.parse.urlencode(params)}"
    return redirect(url)  # send user to Spotify to login

@login_required
def disconnect_spotify(request):
    """Disconnect user from Spotify"""
    if request.user.is_authenticated:
        profile, created = UserProfile.objects.get_or_create(user=request.user)
        profile.connected_to_spotify = False
        profile.spotify_access_token = None
        profile.spotify_refresh_token = None
        profile.spotify_token_expires_at = None
        profile.save()
        
        messages.success(request, 'Successfully disconnected from Spotify!')
    
    return redirect('station:home')

def spotify_player(request):
    """Render the Spotify player"""
    if not request.user.is_authenticated or not request.user.userprofile.connected_to_spotify:
        messages.warning(request, 'You need to connect your Spotify account first.')
        return redirect('station:home')
    
    # Get valid access token
    access_token = get_valid_spotify_token(request.user)
    if not access_token:
        messages.error(request, 'Failed to get valid Spotify token. Please reconnect your account.')
        return redirect('station:home')
    
    # Initialize Spotify client
    sp = spotipy.Spotify(auth=access_token)
    
    try:
        # Get user's current playback state
        playback = sp.current_playback()
        return render(request, 'station/spotify_player.html', {'playback': playback})
    except Exception as e:
        messages.error(request, f'Error accessing Spotify: {str(e)}')
        return redirect('station:home')

def spotify_player_api(request):
    """API endpoint to get Spotify playback state"""
    if not request.user.is_authenticated or not request.user.userprofile.connected_to_spotify:
        return JsonResponse({'error': 'User not authenticated or not connected to Spotify'}, status=403)
    
    # Get valid access token
    access_token = get_valid_spotify_token(request.user)
    if not access_token:
        return JsonResponse({'error': 'Failed to get valid Spotify token'}, status=401)
    
    # Initialize Spotify client
    sp = spotipy.Spotify(auth=access_token)
    
    try:
        # Get user's current playback state
        playback = sp.current_playback()
        
        if playback is None:
            return JsonResponse({'error': 'No active playback found'}, status=404)
        
        return JsonResponse(playback)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

def get_valid_spotify_token(user):
    """Get a valid Spotify access token, refreshing if necessary"""
    try:
        profile = user.userprofile
        if not profile.spotify_access_token:
            print("No access token found")
            return None
        
        # Check if token is expired before making API calls
        if profile.spotify_token_expires_at and profile.spotify_token_expires_at <= timezone.now():
            print("Token expired, attempting refresh...")
            if profile.spotify_refresh_token:
                new_token = refresh_spotify_token(profile.spotify_refresh_token)
                if new_token:
                    # Update token and expiry time
                    profile.spotify_access_token = new_token
                    profile.spotify_token_expires_at = timezone.now() + timedelta(hours=1)
                    profile.save()
                    print("Token refreshed successfully")
                    return new_token
                else:
                    print("Token refresh failed")
                    return None
            else:
                print("No refresh token available")
                return None
        
        # Test the current token
        sp = spotipy.Spotify(auth=profile.spotify_access_token)
        try:
            sp.current_user()
            return profile.spotify_access_token
        except spotipy.exceptions.SpotifyException as e:
            print(f"Token validation failed: {e}")
            # Try to refresh token
            if profile.spotify_refresh_token:
                new_token = refresh_spotify_token(profile.spotify_refresh_token)
                if new_token:
                    profile.spotify_access_token = new_token
                    profile.spotify_token_expires_at = timezone.now() + timedelta(hours=1)
                    profile.save()
                    return new_token
            return None
            
    except Exception as e:
        print(f"Error in get_valid_spotify_token: {e}")
        return None

def refresh_spotify_token(refresh_token):
    """Refresh Spotify access token using refresh token"""
    token_url = 'https://accounts.spotify.com/api/token'
    
    # Use proper authorization header instead of form data
    import base64
    client_credentials = f"{settings.SPOTIFY_CLIENT_ID}:{settings.SPOTIFY_CLIENT_SECRET}"
    client_credentials_b64 = base64.b64encode(client_credentials.encode()).decode()
    
    headers = {
        'Authorization': f'Basic {client_credentials_b64}',
        'Content-Type': 'application/x-www-form-urlencoded'
    }
    
    token_data = {
        'grant_type': 'refresh_token',
        'refresh_token': refresh_token,
    }
    
    try:
        response = requests.post(token_url, headers=headers, data=token_data)
        token_info = response.json()
        
        print(f"Token refresh response: {response.status_code}")
        print(f"Token info: {token_info}")
        
        if response.status_code == 200:
            return token_info.get('access_token')
        else:
            print(f"Token refresh failed: {token_info}")
            return None
    except Exception as e:
        print(f"Error refreshing token: {e}")
        return None

@login_required
def get_recommendations(request):

    auth_manager = SpotifyClientCredentials(client_id=settings.SPOTIFY_CLIENT_ID, client_secret=settings.SPOTIFY_CLIENT_SECRET)
    sp = spotipy.Spotify(auth_manager=auth_manager, auth=get_valid_spotify_token(request.user))

    if not request.user.is_authenticated or not request.user.userprofile.connected_to_spotify:
        return JsonResponse({'error': 'User not connected to Spotify'}, status=403)
    
    #client = spotipy.Spotify(auth=get_valid_spotify_token(request.user))
    if not sp:
        return JsonResponse({'error': 'Failed to get valid Spotify token'}, status=401)

    print("Token:", get_valid_spotify_token(request.user))
    print("Expires at:", request.user.userprofile.spotify_token_expires_at)

    top_tracks = sp.current_user_top_tracks(limit=2, time_range='short_term')
    print("Top Tracks:", top_tracks)
    seed_track_ids = [track['id'] for track in top_tracks['items']]
    print(seed_track_ids)

    top_artists = sp.current_user_top_artists(limit=2, time_range='short_term')
    seed_artist_ids = [artist['id'] for artist in top_artists['items']]
    print(seed_artist_ids)

    #genres = sp.recommendation_genre_seeds()
    #print("Available Genres:", genres['genres'])
    print(f"About to call recommendations with:")
    print(f"  seed_artists: {seed_artist_ids}")
    print(f"  seed_tracks: {seed_track_ids}")
    print(f"  seed_genres: ['pop']")
    print(f"  limit: 20")
    print(f"  market: 'CA'")

    # Check if lists are actually not empty
    if not seed_artist_ids:
        print("WARNING: seed_artist_ids is empty!")
    if not seed_track_ids:
        print("WARNING: seed_track_ids is empty!")

    #print(sp.recommendations(seed_genres=['pop'], limit=1))

    #results = sp.recommendations(
    #    seed_genres=['pop'],          # Put genres first
    #    seed_artists=seed_artist_ids,  
    #    seed_tracks=seed_track_ids,   
    #    limit=20,
    #    country='CA'  # Use single quotes
    #)
    results = sp.current_user_top_tracks(limit=20, time_range='short_term')

    print("Results:", results)
    recommended_track_ids = [track['id'] for track in results["items"]]

    client_id = sp.current_user()['id']

    playlist = sp.user_playlist_create(
        user=client_id,
        name='My Recommended Playlist',
        public=True,
        description='Songs recommended by Spotipy!'
    )

    sp.playlist_add_items(playlist_id=playlist['id'], items=recommended_track_ids)

    print(playlist['external_urls']['spotify'])

    return JsonResponse({
        'playlist_id': playlist['id'],
        'playlist_url': playlist['external_urls']['spotify'],
        'tracks': [{'id': track['id'], 'name': track['name']} for track in results['items']]
    })

@csrf_exempt
def play(request):
    """Start playback on Spotify"""
    if not request.user.is_authenticated or not request.user.userprofile.connected_to_spotify:
        return JsonResponse({'error': 'User not connected to Spotify'}, status=403)
    
    access_token = get_valid_spotify_token(request.user)
    if not access_token:
        return JsonResponse({'error': 'Failed to get valid Spotify token'}, status=401)
    
    sp = spotipy.Spotify(auth=access_token)
    
    try:
        sp.start_playback()
        return JsonResponse({'status': 'Playback started'})
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

@csrf_exempt
def pause(request):
    """Pause playback on Spotify"""
    if not request.user.is_authenticated or not request.user.userprofile.connected_to_spotify:
        return JsonResponse({'error': 'User not connected to Spotify'}, status=403)
    
    access_token = get_valid_spotify_token(request.user)
    if not access_token:
        return JsonResponse({'error': 'Failed to get valid Spotify token'}, status=401)
    
    sp = spotipy.Spotify(auth=access_token)
    print("Pausing playback with access token:", access_token)
    
    try:
        sp.pause_playback()
        return JsonResponse({'status': 'Playback paused'})
    except Exception as e:
        messages.error(request, "Premium required to pause playback on Spotify.")
        return JsonResponse({'error': str(e)}, status=500)

@csrf_exempt
def transfer_playback(request):
    body = json.loads(request.body)
    access_token = request.user.userprofile.spotify_access_token

    headers = {
        'Authorization': f'Bearer {access_token}',
        'Content-Type': 'application/json'
    }

    r = requests.put(
        'https://api.spotify.com/v1/me/player',
        headers=headers,
        json={"device_ids": body['device_ids'], "play": body.get('play', True)}
    )

    return JsonResponse({'status': r.status_code})

def get_voice(request, just_played, next_song):
    """Example Groq API call"""
    groq = Groq(api_key=settings.GROQ_API_KEY)
    
    chat_completion = groq.chat.completions.create(
        messages=[
            {
                "role": "user",
                "content": f"You just played the song '{just_played}'. Next up is {next_song}. Say what a Disc Jockey would say about the song, the artist, and the album.",
            },
            {
                "role": "system", 
                "content": "You are a experienced radio disk jockey. You will be given a song and you will tell the user about the song, the artist, and the album. You will also give a brief description of the song. Your station is called YourRadioStation.",
            },
        ],
        model="llama3-8b-8192",
        temperature=0.7
    )
    response_text = chat_completion.choices[0].message.content
    print(response_text)
    
    # Use MEDIA_ROOT for user-generated content
    media_dir = os.path.join(settings.MEDIA_ROOT, 'audio')
    os.makedirs(media_dir, exist_ok=True)
    
    # Create unique filename
    import time
    timestamp = int(time.time())
    filename = f"voice_response_{timestamp}.mp3"
    file_path = os.path.join(media_dir, filename)
    
    tts = gTTS(text=response_text, lang='en')
    tts.save(file_path)
    
    if not os.path.exists(file_path):
        raise Exception(f"Failed to save voice response to {file_path}")

    # Return the proper media URL
    return JsonResponse({
        'status': 'success', 
        'audio_url': f'{settings.MEDIA_URL}audio/{filename}'
    })

def get_playing_track(request):
    """Get currently playing track"""
    if not request.user.is_authenticated or not request.user.userprofile.connected_to_spotify:
        return JsonResponse({'error': 'User not connected to Spotify'}, status=403)
    
    access_token = get_valid_spotify_token(request.user)
    if not access_token:
        return JsonResponse({'error': 'Failed to get valid Spotify token'}, status=401)
    
    sp = spotipy.Spotify(auth=access_token)
    
    try:
        playback = sp.current_playback()
        if playback and playback['item']:
            track = playback['item']
            return JsonResponse({
                'track_id': track['id'],
                'track_name': track['name'],
                'artist_name': ', '.join(artist['name'] for artist in track['artists']),
                'album_name': track['album']['name'],
                'is_playing': playback.get('is_playing', False),
                'progress_ms': playback.get('progress_ms', 0),  # Add progress
                'duration_ms': track.get('duration_ms', 0)      # Add duration
            })
        else:
            return JsonResponse({'error': 'No track currently playing'}, status=200)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

def get_next_track(request):
    """Get the next track in queue or playlist"""
    if not request.user.is_authenticated or not request.user.userprofile.connected_to_spotify:
        return JsonResponse({'error': 'User not connected to Spotify'}, status=403)
    
    access_token = get_valid_spotify_token(request.user)
    if not access_token:
        return JsonResponse({'error': 'Failed to get valid Spotify token'}, status=401)
    
    sp = spotipy.Spotify(auth=access_token)
    
    try:
        # First try to get next track from queue
        next_track = None
        next_track_name = "Coming up next"
        next_artist_name = ""
        
        try:
            queue = sp.queue()
            if queue and queue.get('queue') and len(queue['queue']) > 0:
                next_track = queue['queue'][0]
                next_track_name = next_track['name']
                next_artist_name = ', '.join(artist['name'] for artist in next_track['artists'])
        except Exception as queue_error:
            print(f"Could not get queue: {queue_error}")
            
            # Fallback: Try to get next track from current context (playlist/album)
            try:
                playback = sp.current_playback()
                if playback and playback.get('context'):
                    context = playback['context']
                    context_uri = context['uri']
                    current_track_id = playback['item']['id']
                    
                    # If playing from a playlist
                    if 'playlist' in context_uri:
                        playlist_id = context_uri.split(':')[-1]
                        playlist_tracks = sp.playlist_tracks(playlist_id)
                        
                        # Find current track position and get next one
                        for i, item in enumerate(playlist_tracks['items']):
                            if item['track']['id'] == current_track_id:
                                # Get next track if it exists
                                if i + 1 < len(playlist_tracks['items']):
                                    next_track = playlist_tracks['items'][i + 1]['track']
                                    next_track_name = next_track['name']
                                    next_artist_name = ', '.join(artist['name'] for artist in next_track['artists'])
                                break
                    
                    # If playing from an album
                    elif 'album' in context_uri:
                        album_id = context_uri.split(':')[-1]
                        album_tracks = sp.album_tracks(album_id)
                        
                        # Find current track and get next one
                        for i, track in enumerate(album_tracks['items']):
                            if track['id'] == current_track_id:
                                if i + 1 < len(album_tracks['items']):
                                    next_track = album_tracks['items'][i + 1]
                                    next_track_name = next_track['name']
                                    next_artist_name = ', '.join(artist['name'] for artist in next_track['artists'])
                                break
                        
            except Exception as context_error:
                print(f"Could not get next track from context: {context_error}")
        
        return JsonResponse({
            'next_track_id': next_track['id'] if next_track else None,
            'next_track_name': next_track_name,
            'next_artist_name': next_artist_name,
            'has_next_track': next_track is not None
        })
        
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

@login_required
def next(request):
    # Logic to get the next track
    if not request.user.is_authenticated or not request.user.userprofile.connected_to_spotify:
        return JsonResponse({'error': 'User not connected to Spotify'}, status=403)

    try:
        access_token = get_valid_spotify_token(request.user)
        if not access_token:
            return JsonResponse({'error': 'Failed to get valid Spotify token'}, status=401)
        sp = spotipy.Spotify(auth=access_token)
        current_track = sp.current_playback()
        if not current_track:
            return JsonResponse({'error': 'No track is currently playing'}, status=400)

        # Get the next track from the Spotify API
        next_track = sp.next_track()
        if not next_track:
            return JsonResponse({'error': 'No next track available'}, status=404)

        return JsonResponse({
            'next_track_id': next_track['id'],
            'next_track_name': next_track['name'],
            'next_artist_name': ', '.join(artist['name'] for artist in next_track['artists']),
            'has_next_track': True
        })

    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)
    
@login_required
def finished_song(request):
    """Handle the end of a song"""
    if not request.user.is_authenticated or not request.user.userprofile.connected_to_spotify:
        return JsonResponse({'error': 'User not connected to Spotify'}, status=403)

    try:
        access_token = get_valid_spotify_token(request.user)
        if not access_token:
            return JsonResponse({'error': 'Failed to get valid Spotify token'}, status=401)
        
        sp = spotipy.Spotify(auth=access_token)
        playback = sp.current_playback()
        if playback and playback['item']:
            progress_ms = playback.get('progress_ms', 0)
            duration_ms = playback['item'].get('duration_ms', 0)
            if duration_ms > 0 and progress_ms >= duration_ms - 1000:  # within 1 second of end
                sp.pause()
            else:
                return JsonResponse({'status': 'not_finished', 'message': 'Song is still playing'})
        else:
            return JsonResponse({'error': 'No track currently playing'}, status=400)
        
        return JsonResponse({'status': 'success', 'message': 'Skipped to next track'})
    
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)
