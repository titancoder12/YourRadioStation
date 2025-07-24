document.addEventListener('DOMContentLoaded', function() {
    console.log('DOM loaded');
    let currentTrackInfo = {
      id: null,
      name: null,
      artist: null,
      progress: null
    };

    function play() {
        fetch('/api/play/', {
            method: 'GET',
            headers: {
                'Content-Type': 'application/json',
            }
        })
        .then(response => response.json())
        .then(data => {
            console.log('Play response:', data);
            getCurrentTrack(); // Refresh track info after play
        })
        .catch(error => {
            console.error('Error:', error);
        });
    }

    function pause() {
        fetch('/api/pause/', {
            method: 'GET',
            headers: {
                'Content-Type': 'application/json',
            }
        })
        .then(response => response.json())
        .then(data => {
            console.log('Pause response:', data);
            getCurrentTrack(); // Refresh track info after pause
        })
        .catch(error => {
            console.error('Error:', error);
        });
    }
    // Function to handle track change
    previousTrackName = 'No song here. This is the start of the show!';
    function onTrackChange(data, previousTrackInfo) {
        // Pause the current track
        fetch('/api/pause/', {
            method: 'GET',
            headers: {
                'Content-Type': 'application/json',
            }
        })
        .then(response => {
            console.log('Pause response:', response);
        })
        .catch(error => {
            console.error('Error pausing track:', error);
        }).then(() => {
            // Get the next track using the helper function
            fetch('/api/get-next-track/')
                .then(response => response.json())
                .then(nextTrackData => {
                    const previousTrackName = previousTrackInfo && previousTrackInfo.name ? 
                        previousTrackInfo.name : 'No previous song';
                    const nextTrackName = nextTrackData.next_track_name || 'Unknown next song';

                    console.log(`Transitioning from "${previousTrackName}" to "${data.name}" with "${nextTrackName}" coming up next`);

                    // Call voice API with current song and next song
                    fetch(`/api/get-voice/${encodeURIComponent(data.name)}/${encodeURIComponent(nextTrackName)}/`)
                      .then(response => response.json())
                      .then(voiceData => {
                        if (voiceData.error) {
                          console.error('Error fetching voice:', voiceData.error);
                        } else {
                          console.log('Voice data:', voiceData);
                          const audioElement = document.getElementById('voice-audio');
                          if (audioElement) {
                            audioElement.src = voiceData.audio_url;
                            audioElement.type = 'audio/mp3';
                            audioElement.play().catch(err => {
                              console.error('Error playing audio:', err);
                            });
                          }
                        }
                      })
                      .catch(error => {
                        console.error('Error fetching voice:', error);
                      });
                })
                .catch(error => {
                    console.error('Error fetching next track:', error);
                    // Fallback to unknown next song
                    const previousTrackName = previousTrackInfo && previousTrackInfo.name ? 
                        previousTrackInfo.name : 'No previous song';
                    const nextTrackName = 'Unknown next song';

                    fetch(`/api/get-voice/${encodeURIComponent(data.name)}/${encodeURIComponent(nextTrackName)}/`)
                      .then(response => response.json())
                      .then(voiceData => {
                        // Handle voice response...
                      });
                });
        });
    }

    // Auto-refresh every 5 seconds
    function startAutoRefresh() {
        getCurrentTrack(); // Get immediately
        setInterval(getCurrentTrack, 1000); // Then every 1 second
    }

    // Manual refresh button
    const refreshButton = document.getElementById('refresh-track');
    if (refreshButton) {
        refreshButton.addEventListener('click', getCurrentTrack);
    }

    // Pause button
    const pauseButton = document.getElementById('start-stop-button');
    if (pauseButton) {
        pauseButton.addEventListener('click', function() {
            pause();
        });
    }

    // Play button
    const playButton = document.getElementById('play-button');
    if (playButton) {
        playButton.addEventListener('click', function() {
            play();
        });
    }

    // Start auto-refresh if user is connected to Spotify
    const nowPlayingDiv = document.getElementById('now-playing');
    if (nowPlayingDiv) {
        startAutoRefresh();
    }

    function getCurrentTrack() {
        fetch('/api/get-playing-track/')
            .then(response => response.json())
            .then(data => {
                if (data.error) {
                    console.error('Error fetching track:', data.error);
                    return;
                }

                currentTrackInfo.id = data.track_id;
                currentTrackInfo.name = data.track_name;
                currentTrackInfo.artist = data.artist_name;
                currentTrackInfo.progress = data.progress;
                console.log('Currently playing track:', currentTrackInfo.name, 'by', currentTrackInfo.artist);

                // Update UI elements
                document.getElementById('track-name').textContent = currentTrackInfo.name;
                document.getElementById('artist-name').textContent = `by ${currentTrackInfo.artist}`;
            })
            .catch(error => {
                console.error('Error fetching track:', error);
            });
        return currentTrackInfo;
    }

    let last_track_id = null;

    function checkTrackChange() {
        if (currentTrackInfo.id !== last_track_id && currentTrackInfo.id !== null) {
            onTrackChange(currentTrackInfo, last_track_id);
            console.log('Track changed!');
            last_track_id = currentTrackInfo.id;
            
        }
    }

    // Start auto-refresh and check for track changes every second
    startAutoRefresh();
    setInterval(checkTrackChange, 1000);
});

// Spotify SDK callback
window.onSpotifyWebPlaybackSDKReady = () => {
    console.log('Spotify SDK Ready!');
};

