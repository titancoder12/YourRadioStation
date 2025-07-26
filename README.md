# YourRadioStation 🎵

A Django-powered web application that creates an AI-powered radio station experience using your Spotify account. Listen to music with intelligent DJ voice transitions powered by AI.

## Features

### Spotify Integration
- **Spotify OAuth Authentication** - Secure login with your Spotify account
- **Real-time Playback Control** - Play, pause, and control your Spotify music
- **Now Playing Display** - See current track, artist, and album information
- **Automatic Track Detection** - Real-time monitoring of track changes
- **Token Management** - Automatic refresh of expired Spotify tokens

### AI-Powered DJ Experience
- **Smart Voice Transitions** - AI-generated DJ commentary between tracks
- **Groq AI Integration** - Uses Groq's LLaMA models for natural DJ speech
- **Text-to-Speech** - Converts AI text to audio using Google Text-to-Speech (gTTS)
- **Contextual Commentary** - DJ talks about the previous song and introduces the next one
- **Seamless Audio Flow** - Automatic music pause/resume during voice segments

### Web Interface
- **Responsive Design** - Works on desktop and mobile devices
- **Real-time Updates** - Live track information without page refresh
- **User Authentication** - Secure login/logout functionality
- **Clean UI** - Modern, intuitive interface for music control

### Technical Features
- **Django Framework** - Robust Python web framework
- **SQLite Database** - User profiles and connection status storage
- **Environment Variables** - Secure API key management
- **Error Handling** - Graceful handling of API failures and token expiration
- **Media File Management** - Automatic cleanup of generated audio files

## Tech Stack

- **Backend**: Django 4.0.5, Python
- **Frontend**: HTML, CSS, JavaScript (Vanilla)
- **Database**: SQLite
- **APIs**: 
  - Spotify Web API
  - Groq AI (LLaMA models)
  - Google Text-to-Speech (gTTS)
- **Authentication**: Spotify OAuth 2.0

## Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/titancoder12/YourRadioStation.git
   cd YourRadioStation
   ```

2. **Install dependencies**
   ```bash
   pip install django spotipy python-dotenv gtts groq requests
   ```

3. **Set up environment variables**
   Create a `.env` file in the project root:
   ```env
   SPOTIFY_CLIENT_SECRET=your_spotify_client_secret
   GROQ_API_KEY=your_groq_api_key
   ```

4. **Run migrations**
   ```bash
   python manage.py migrate
   ```

5. **Start the development server**
   ```bash
   python manage.py runserver
   ```

6. **Visit the application**
   Open your browser to `http://127.0.0.1:8000`

## Configuration

### Spotify App Setup
1. Create a Spotify app at https://developer.spotify.com/dashboard
2. Set redirect URI to: `http://127.0.0.1:8000/callback`
3. Copy your Client ID and Client Secret to the `.env` file

### Groq API Setup
1. Get an API key from https://console.groq.com
2. Add your API key to the `.env` file

## Usage

1. **Connect to Spotify**: Click "Connect to Spotify" and authorize the application
2. **Start Listening**: Play music through your Spotify app or the web interface
3. **Enjoy AI DJ**: The system automatically detects track changes and plays AI-generated DJ commentary
4. **Get Recommendations**: Use the recommendations feature to discover new music based on your listening habits

## API Endpoints

- `/api/get-playing-track/` - Get current track information
- `/api/play/` - Resume Spotify playback
- `/api/pause/` - Pause Spotify playback
- `/api/get-recommendations/` - Generate music recommendations
- `/api/get-voice/<previous>/<current>/` - Generate DJ voice transition
- `/api/get-next-track/` - Get upcoming track information

## Contributing

This project is currently in development. Feel free to submit issues and feature requests.

## License

This project is open source and available under the MIT License.