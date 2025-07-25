document.addEventListener('DOMContentLoaded', function() {
    console.log('DOM loaded');
    
    // Declare all variables at the top
    let currentTrackInfo = {
        id: null,
        name: null,
        artist: null,
        progress: null
    };
    
    let previousTrackInfo = null;
    let refreshInterval = null; // Declare this variable
    let checkInterval = null;   // Declare this variable
    let currentAudio = null;    // Declare for audio management

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

    function next() {
        fetch('/api/next/', {
            method: 'GET',
            headers: {
                'Content-Type': 'application/json',
            }
        })
        .then(response => response.json())
        .then(data => {
            console.log('Next response:', data);
            getCurrentTrack(); // Refresh track info after next
        })
        .catch(error => {
            console.error('Error:', error);
        });
    }

    function getVoice(previousTrackName, currentTrackName) {
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
                
                currentAudio = new Audio(data.audio_url);
                
                currentAudio.addEventListener('ended', function() {
                    console.log('Voice finished, resuming music...');
                    play();
                    currentAudio = null;
                });
                
                currentAudio.addEventListener('error', function() {
                    console.error('Audio playback error');
                    play();
                    currentAudio = null;
                });
                
                currentAudio.play().catch(err => {
                    console.error('Error playing audio:', err);
                    play();
                    currentAudio = null;
                });
            } else {
                console.log('No voice URL returned.');
                play(); // Resume music anyway
            }
        })
        .catch(error => {
            console.error('Error generating voice:', error);
            play(); // Resume music on error
        });
    }

    function onTrackChange(currentTrack, previousTrack) {
        console.log('🎵 Track changed!');
        pause();
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

        // Only call getVoice if we have a valid previous track
        if (previousTrack && previousTrack.name) {
            const prevName = `${previousTrack.name} by ${previousTrack.artist}`;
            const currName = `${currentTrack.name} by ${currentTrack.artist}`;

            console.log(`Generating voice: "${prevName}" to "${currName}"`);
            getVoice(prevName, currName);
        } else {
            console.log('No previous track - skipping voice generation');
            play(); // Resume music if no voice needed
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
                    progress: data.progress_ms
                };

                console.log('Currently playing:', newTrackInfo.name, 'by', newTrackInfo.artist);

                // Check for track change BEFORE updating currentTrackInfo
                if (currentTrackInfo.id && currentTrackInfo.id !== newTrackInfo.id) {
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
        }, 2000); // Check every 2 seconds
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