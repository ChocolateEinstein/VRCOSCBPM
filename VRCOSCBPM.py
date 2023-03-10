import configparser
from os.path import exists
import time
import datetime
import tekore as tk
from pythonosc.udp_client import SimpleUDPClient

# =======================
# Load Spotify credentials

spotify_credentials = configparser.ConfigParser()
spotify_credentials.read('spotify_credentials.cfg')

client_id = str(spotify_credentials['spotify_credentials']['client_id'])
client_secret = str(spotify_credentials['spotify_credentials']['client_secret'])

# =======================
# Load Configuration

config = configparser.ConfigParser()
config.read('vrcoscbpm.cfg')

ip = str(config['VRCOSCBPM']['ip'])
port = int(config['VRCOSCBPM']['port'])
redirect_uri = 'https://github.com/ChocolateEinstein/VRCOSCBPM#spotify-authorization'

animation_bpm = int(config['VRCOSCBPM']['animation_bpm'])
avatar_param_path = str(config['VRCOSCBPM']['avatar_parameter_path'])

refresh_rate = int(config['VRCOSCBPM']['refresh_rate'])

# =======================
# Tekore Setup

app_token = tk.request_client_token(client_id, client_secret)

spotify = tk.Spotify(app_token) 

# =======================
# Authorization

tekore_cfg = 'tekore.cfg'
scope = tk.scope.user_read_playback_state

if exists(tekore_cfg) == False:   # Generate User Token
    print('User needs to allow VRCOSCBPM to access their Spotify account in order to get current song BPM')
    input('Press any button to continue')
    print('\n' * 3)
    
    conf = (client_id, client_secret, redirect_uri)
    token = tk.prompt_for_user_token(*conf, scope)
    print('\n' * 3)
    
    input('Press any button to build tekore.cfg')
    tk.config_to_file(tekore_cfg, conf + (token.refresh_token,))
    input('Built tekore.cfg. Press any button to continue')
    print('\n' * 3)

conf = tk.config_from_file(tekore_cfg, return_refresh=True)
user_token = tk.refresh_user_token(*conf[:2], conf[3])   
    
spotify.token = user_token

# =======================
# Functions

def send_osc(ip, port, path, variable):
    client = SimpleUDPClient(ip, port)  # Create client
    
    client.send_message(path, variable)   # Send float message
    
    print('Sent ' + str(variable) + ' to ' + path + ' at ' + str(ip) + ':' + str(port))

def get_track(): # Get the User's currently playing Spotify track
    track = spotify.playback()
    if is_playing(track) is False:
        return False
    return track.item

def is_playing(playback): # Check if 'playback' is a valid track
    if playback is None:
        return False
    if playback.item.type != 'track':
        return False
    return True

def track_tempo(track): # Get The tempo of a track
    track_tempo = spotify.track_audio_features(track.id).tempo
    return track_tempo

def divide_bpm(raw_bpm): # Turn a Tempo into a fraction of 'animation_bpm'
    while raw_bpm >= animation_bpm:
        raw_bpm /= 2
    
    divided_bpm = raw_bpm / animation_bpm
    
    return divided_bpm

def main():
    current_track = get_track()
    
    print(datetime.datetime.now())
    if current_track is False:
        print('N/a (User Not Playing)')
        send_osc(ip, port, avatar_param_path, 0.0)
        
    else:
        try:
            current_track_tempo = track_tempo(current_track)
        
            osc_bpm = divide_bpm(current_track_tempo)
        
            print('now playing: ' + current_track.name)
            print('BPM: ' + str(current_track_tempo))
            send_osc(ip, port, avatar_param_path, osc_bpm)

        except:
            print('SOME ERROR OCCOURED!')
    
    time.sleep(refresh_rate)
    print('\n' * 3)

if __name__ == "__main__":
    while True:
        main() 