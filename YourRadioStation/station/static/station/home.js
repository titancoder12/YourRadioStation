document.addEventListener('DOMContentLoaded', function() {
    console.log('DOM loaded');
    
    // Declare ALL variables at the top level
    let currentTrackInfo = {
        id: null,
        name: null,
        artist: null,
        progress: null,
        duration: null
    };
    
    let previousTrackInfo = null;
    let refreshInterval = null;
    let checkInterval = null;
    let currentAudio = null;    // ← ADD THIS DECLARATION
    let isTransitioning = false;

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
        })
        .catch(error => {
            console.error('Error:', error);
        });
    }

    function getVoice(previousTrackName, currentTrackName) {
        // Prevent multiple voice generations
        if (isTransitioning) {
            console.log('Already transitioning, skipping voice generation');
            return;
        }
        
        isTransitioning = true;
        console.log(`Generating voice for: "${previousTrackName}" to "${currentTrackName}"`);
        
        // URL encode the track names
        const encodedPrev = encodeURIComponent(previousTrackName);
        const encodedCurr = encodeURIComponent(currentTrackName);
        
        fetch(`/api/get-voice/${encodedPrev}/${encodedCurr}/`, {
            method: 'GET',
            headers: {
                'Content-Type': 'application/json',
            }
        })
        .then(response => response.json())
        .then(data => {
            console.log('Voice generation response:', data);
            if (data.audio_url) {
                // Stop any currently playing audio
                if (currentAudio) {
                    currentAudio.pause();
                    currentAudio = null;
                }
                
                // Create new audio element
                currentAudio = new Audio(data.audio_url);
                
                // Handle audio events
                currentAudio.addEventListener('ended', function() {
                    console.log('Voice finished, resuming music...');
                    isTransitioning = false;  // Reset flag
                    play();
                    currentAudio = null;
                });
                
                currentAudio.addEventListener('error', function(e) {
                    console.error('Audio playback error:', e);
                    isTransitioning = false;  // Reset flag
                    play();
                    currentAudio = null;
                });
                
                // Play the audio
                currentAudio.play().catch(err => {
                    console.error('Error playing audio:', err);
                    isTransitioning = false;  // Reset flag
                    play();
                    currentAudio = null;
                });
            } else {
                console.log('No voice URL returned.');
                isTransitioning = false;  // Reset flag
                play(); // Resume music anyway
            }
        })
        .catch(error => {
            console.error('Error generating voice:', error);
            isTransitioning = false;  // Reset flag
            play(); // Resume music on error
        });
    }

    function onTrackChange(currentTrack, previousTrack) {
        console.log('🎵 Track changed!');
        
        // Only pause if not already transitioning
        if (!isTransitioning) {
            pause();
        }
        
        console.log('Current track:', currentTrack?.name || 'Unknown');
        console.log('Previous track:', previousTrack?.name || 'None');
        
        // Update UI with null check
        const nowPlayingDiv = document.getElementById('now-playing');
        if (nowPlayingDiv) {
            nowPlayingDiv.innerHTML = `
                <h2>Now Playing</h2>
                <p id="track-name">${currentTrack.name}</p>
                <p id="artist-name">by ${currentTrack.artist}</p>
            `;
        } else {
            console.warn('now-playing element not found');
        }

        // Only call getVoice if we have a valid previous track and not already transitioning
        if (previousTrack && previousTrack.name && !isTransitioning) {
            const prevName = `${previousTrack.name} by ${previousTrack.artist}`;
            const currName = `${currentTrack.name} by ${currentTrack.artist}`;

            console.log(`Generating voice: "${prevName}" to "${currName}"`);
            getVoice(prevName, currName);
        } else {
            console.log('No previous track or already transitioning - skipping voice generation');
            if (!isTransitioning) {
                play(); // Resume music if no voice needed
            }
        }
    }

    function getCurrentTrack() {
        fetch('/api/get-playing-track/')
            .then(response => response.json())
            .then(data => {
                if (data.error) {
                    console.error('Error fetching track:', data.error);
                    return;
                }

                // Create new track info object
                const newTrackInfo = {
                    id: data.track_id,
                    name: data.track_name,
                    artist: data.artist_name,
                    progress: data.progress_ms,
                    duration: data.duration_ms
                };

                console.log('Currently playing:', newTrackInfo.name, 'by', newTrackInfo.artist);

                // Check for track change BEFORE updating currentTrackInfo
                if (currentTrackInfo.id && currentTrackInfo.id !== newTrackInfo.id && !isTransitioning) {
                    console.log('Track change detected!');
                    onTrackChange(newTrackInfo, currentTrackInfo); // New track, old track
                }

                // Update current track info
                currentTrackInfo = newTrackInfo;

                // Update UI elements with null checks
                const trackNameEl = document.getElementById('track-name');
                const artistNameEl = document.getElementById('artist-name');
                
                if (trackNameEl) trackNameEl.textContent = currentTrackInfo.name;
                if (artistNameEl) artistNameEl.textContent = `by ${currentTrackInfo.artist}`;
            })
            .catch(error => {
                console.error('Error fetching track:', error);
            });
    }

    function startAutoRefresh() {
        // Clear any existing intervals
        if (refreshInterval) clearInterval(refreshInterval);
        if (checkInterval) clearInterval(checkInterval);
        
        console.log('Starting auto-refresh...');
        getCurrentTrack(); // Get immediately
        
        // Single interval that handles both fetching and checking
        refreshInterval = setInterval(() => {
            getCurrentTrack();
        }, 1000); // Check every second for faster detection
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

    // Next button
    const nextButton = document.getElementById('next-button');
    if (nextButton) {
        nextButton.addEventListener('click', function() {
            next();
        });
    }

    // Start auto-refresh
    startAutoRefresh();
});

// Spotify SDK callback
window.onSpotifyWebPlaybackSDKReady = () => {
    console.log('Spotify SDK Ready!');
};