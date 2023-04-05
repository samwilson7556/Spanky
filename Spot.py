import spotipy
from spotipy.oauth2 import SpotifyOAuth
import googleapiclient.discovery
import googleapiclient.errors
import datetime
import config
import requests
import vlc
import time

# authenticate with Spotify API
scope = "user-read-playback-state"
sp = spotipy.Spotify(auth_manager=SpotifyOAuth(scope=scope,
                                               client_id=config.SPOTIPY_CLIENT_ID,
                                               client_secret=config.SPOTIPY_CLIENT_SECRET,
                                               redirect_uri=config.SPOTIPY_REDIRECT_URI))

# authenticate with YouTube API
youtube = googleapiclient.discovery.build("youtube", "v3", developerKey=config.YOUTUBE_DEVELOPER_KEY)

# get current song information from Spotify
current_track = sp.current_playback()
song_title = current_track['item']['name']
song_artist = current_track['item']['artists'][0]['name']
output = "Currently playing: {} by {}\n".format(song_title, song_artist)

# search for official music video on YouTube
search_response = youtube.search().list(
    q=song_title + ' ' + song_artist + ' official music video',
    type='video',
    part='id,snippet',
    maxResults=1
).execute()

# check if the search returned any results
if search_response['pageInfo']['totalResults'] == 0:
    output += "Sorry, the official music video for this song is not available on YouTube.\n"
else:
    # extract video ID from YouTube search response
    video_id = search_response['items'][0]['id']['videoId']

    # get duration and start time of video
    video_response = youtube.videos().list(
        id=video_id,
        part='contentDetails'
    ).execute()

    # check if the video duration could be retrieved from YouTube
    if 'items' not in video_response or len(video_response['items']) == 0:
        output += "Sorry, we could not retrieve the video information from YouTube.\n"
    else:
        duration = video_response['items'][0]['contentDetails']['duration']
        duration_parts = duration[2:].split('M')
        minutes = int(duration_parts[0])
        seconds = int(duration_parts[1].strip('S'))
        duration_seconds = datetime.timedelta(minutes=minutes, seconds=seconds).total_seconds()
        start_time = datetime.timedelta(seconds=0)
        output += "Video duration: {}\n".format(duration_seconds)
        # get current time of song from Spotify
        progress_ms = current_track['progress_ms']
        current_time = datetime.timedelta(milliseconds=progress_ms)
        output += "Current time of song: {}\n".format(current_time)
        
        # calculate time difference between start of video and current time of song
        time_difference = current_time - start_time
        output += "Time difference: {}\n".format(time_difference)
        
        # create instance of VLC media player
        instance = vlc.Instance()
        player = instance.media_player_new()
        
        # load the video
        media = instance.media_new("https://www.youtube.com/watch?v={}".format(video_id))
        player.set_media(media)
        
        player.set_time(int(start_time.total_seconds() * 1000))
        
        # play the video
        player.play()
        	  
# write output to file
with open('output.txt', 'w') as f:
    f.write(output)
