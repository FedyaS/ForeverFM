from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
import threading
import time
import os
from getWavFileDuration import get_wav_duration
from flask_socketio import SocketIO, emit
import groqAudio
import generateContent
import random


# Initialize Flask app and CORS
app = Flask(__name__)
CORS(app)
socketio = SocketIO(app, cors_allowed_origins="*")  # Allow CORS for Next.js frontend

# Some stupid globals
MOCK_NUMBER = 0
MOCKING = False
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MAX_Q_SIZE = 2
should_be_generating_new_data = True

# Shared variables
conv_topic = "Startups and Startup Lifestyle"
scripts = [] # [{speaker_name: '', text: '', is_audio_generated: False}, ...] # Newest last
user_prompts = [] # [{user_name: '', text: ''}, ...] # Newest last
audio = [] # [{speaker_name: '', duration: '', text: '', filename: ''}] # Newest last
current_playback = None  # Global playback state: {'audio': audio_obj, 'start_time': timestamp}
last_sent_file = None


# Locks for thread safety
scripts_lock = threading.Lock()
audio_lock = threading.Lock()
conv_topic_lock = threading.Lock()
user_prompts_lock = threading.Lock()
current_playback_lock = threading.Lock()

# Thread functions
def continousMakeTranscript():
    """Continously generates content (scripts) to be spoken"""
    global MOCK_NUMBER
    while True:
        len_scripts = 0
        with scripts_lock:
            len_scripts = len(scripts)
        
        if len_scripts < MAX_Q_SIZE and should_be_generating_new_data:
            # Send only the last 4 scripts for context
            new_script = generateContent.generateContent(scripts[-4:], conv_topic, mock=MOCKING, mock_number=MOCK_NUMBER)
            new_script['mock_number'] = MOCK_NUMBER
            new_script['is_audio_generated'] = False
            
            if MOCKING:
                MOCK_NUMBER += 1
                if MOCK_NUMBER > 7:
                    MOCK_NUMBER = 0
            
            # new_script = {'speaker_name': 'Chip', 'text': 'blah blah blah', 'mock_number': 1, 'is_audio_generated': False}

            print(f"Generated script for {new_script['speaker_name']} saying: {new_script['text'][:20]}")

            with scripts_lock:
                scripts.append(new_script)
                if len(scripts) >= MAX_Q_SIZE and scripts[0]['is_audio_generated']:
                    scripts.pop(0)

        time.sleep(5)  # not sure if we really need this, but it was working with it so keeping it here
        
def continousMakeAudio():
    """Continously checks the scripts Q and generates new audio, appends the audio to audio var"""
    while True:
        script = None
        script_index = None

        with scripts_lock:
            for i, s in enumerate(scripts):
                if not s['is_audio_generated']: # Grab the first script that doesn't have audio generated
                    script = s
                    script_index = i
                    break
        
        # script = {'speaker_name': 'Aaliyah', 'text': 'blah blah'} # Mock
        
        if script and should_be_generating_new_data:
            # Generate our audio
            new_file_name = f'{round(time.time() * 10)}_audio.wav'
            speaker_name = script['speaker_name']
            
            # Dirty fix as sometimes generateContent() returns a weird speaker name
            if speaker_name not in ['Aaliyah', 'Chip']:
                speaker_name = random.choice(['Aaliyah', 'Chip'])
            
            groqAudio.createAudio(script['text'], f'{speaker_name}-PlayAI', f'audio/{new_file_name}', MOCKING, script['mock_number'])
            
            duration = get_wav_duration(new_file_name)
            new_audio_object = {
                'speaker_name': script['speaker_name'],
                'duration': duration,
                'text': script['text'],
                'filename': new_file_name
            }

            with audio_lock:
                audio.append(new_audio_object)
                if len(audio) > MAX_Q_SIZE:
                    pa = audio.pop(0) # For now... this is a little shady in case audio[0] is the one currently playing
                    
                    # If MOCKING is enabled, delete the corresponding file
                    if MOCKING:
                        file_to_delete = os.path.join("audio", pa['filename'])  # Construct the file path
                        if os.path.exists(file_to_delete):
                            os.remove(file_to_delete)  # Delete the file
                            print(f"Deleted mock audio file: {file_to_delete}")
            
            with scripts_lock:
                scripts[script_index]['is_audio_generated'] = True
                if len(scripts) >= MAX_Q_SIZE:
                    scripts.pop(0)
                print(f"Scripts is {len(scripts)} elements")

            print(f"Generated audio for {script['speaker_name']} duration: {round(duration, 2)} sec saved to: {new_file_name}")

        time.sleep(5)  # not sure if we really need this, but it was working with it so keeping it here
        

def continousManageTopic():
    """Continously check for new user topics, if a new user topic is found handle the transition"""
    # Note this function will quickly jump from topic to topic if there are many user prompts, will need to implement logic to limit topic jumps
    
    global should_be_generating_new_data, conv_topic, scripts, audio
    while True:
        new_up = None
        with user_prompts_lock:
            if user_prompts:
                new_up = user_prompts[0]
                user_prompts.pop(0)
        
        if new_up:
            print(f"Handling new user prompt from {new_up['user_name']} text: {new_up['text']}")
            new_topic = generateContent.determineNewTopic(new_up['text'], MOCKING)
            
            if new_topic:
                should_be_generating_new_data = False # Pauses script / audio generation while the topic is being switched
                
                latest_spoken_scripts = []
                with scripts_lock:
                    if scripts:
                        latest_spoken_scripts.append(scripts[0])
                
                old_topic = ''
                with conv_topic_lock:
                    old_topic = conv_topic
                    
                transition_script = generateContent.generateNewTopicContent(new_up['text'], new_up['user_name'], latest_spoken_scripts, old_topic, new_topic, MOCKING)
                transition_script['is_audio_generated'] = False
                transition_script['mock_number'] = 'transition'

                if transition_script['speaker_name'] != 'System':
                    
                    # Reset all vars lol
                    with conv_topic_lock:
                        conv_topic = new_topic
                        print(f'New Topic is set to: {new_topic}')
                    
                    with scripts_lock:
                        scripts = [transition_script]
                        print(f'Scripts is now {len(scripts)} long')
                    
                    with audio_lock:
                        audio = audio[:1] # Only keep the currently playing audio
                        print(f'Audio is now {len(audio)} long')
                
                should_be_generating_new_data = True
                broadcastNewTopic(new_topic)
        
        time.sleep(3) # may need to adjust

def broadcastNewTopic(new_topic):
    socketio.emit("new_topic", {"new_topic": new_topic})

def broadcastPlaybackState(playback, elapsed):
    """Broadcasts playback updates using a snapshot and precomputed elapsed time."""
    global last_sent_file
    if playback:
        audio_obj = playback['audio']
        filename = audio_obj['filename']

        audio_path = os.path.join(BASE_DIR, "audio", filename)

        # Only broadcast if we haven't already sent this file
        if last_sent_file != filename and os.path.exists(audio_path):
            with open(audio_path, "rb") as f:
                audio_data = f.read()
                socketio.emit("audio", {"data": audio_data, "file": filename})
                print(f'Broadcasted audio {filename} to all clients')
            
            last_sent_file = filename
            socketio.emit("transcript", {"data": audio_obj['text']})

        # Always broadcast position
        socketio.emit("position", {
            "file": filename,
            "elapsed_time": elapsed,
            "duration": audio_obj['duration'],
            "timestamp": int(time.time() * 1000)
        })
        print(f'Broadcasted position {elapsed} of {filename} to all clients')


def playbackManager():
    """Manages continuous audio playback, queuing and playing files seamlessly."""
    global current_playback, last_sent_file
    while True:
        playback_snapshot = None
        elapsed = 0
                
        with current_playback_lock:
            if current_playback:
                elapsed = time.time() - current_playback['start_time']
                duration = current_playback['audio']['duration']
                
                # Audio has ended, pop it and reset state
                if elapsed >= duration:
                    with audio_lock:
                        if audio:
                            audio.pop(0)
                    current_playback = None
                    last_sent_file = None
                    elapsed = 0

            # Set new current_playback
            if not current_playback and audio:
                with audio_lock:
                    if audio:
                        current_playback = {'audio': audio[0], 'start_time': time.time()}
                        print(f"Starting playback: {current_playback['audio']['filename']}")
            
            # Use this to exit the current_playback_lock so it doesn't have to keep waiting
            playback_snapshot = current_playback

        # Broadcast state even if no playback (to keep clients updated)
        broadcastPlaybackState(playback_snapshot, elapsed)

        # Dynamic sleep to minimize gaps between audio files
        if playback_snapshot:
            remaining = current_playback['audio']['duration'] - elapsed
            # Sleep for remaining time or 1 second, whichever is shorter
            sleep_time = min(max(remaining, 0), 1)
            time.sleep(sleep_time)
        else:
            time.sleep(1)  # Default sleep when no playback

# Start bg threads
thread1 = threading.Thread(target=continousMakeTranscript, daemon=True)
thread2 = threading.Thread(target=continousMakeAudio, daemon=True)
thread3 = threading.Thread(target=continousManageTopic, daemon=True)
thread4 = threading.Thread(target=playbackManager, daemon=True)

print("Starting background threads...")
thread1.start()
thread2.start()
thread3.start()
thread4.start()

# Whenever a new client connects to the websocket this runs
@socketio.on("connect")
def handle_connect():
    """Sends current playback state to a newly connected client."""
    print("Client connected:", request.sid)
    
    cp = None
    with current_playback_lock:
        cp = current_playback

    if cp:
        audio_obj = cp['audio']
        elapsed = time.time() - cp['start_time']
        filename = audio_obj['filename']
        audio_path = os.path.join("./audio", filename)
        
        # Send audio file to the new client only
        if os.path.exists(audio_path):
            with open(audio_path, "rb") as f:
                audio_data = f.read()
                socketio.emit("audio", {"data": audio_data, "file": filename}, to=request.sid)
                print(f'Emitted audio to new client {request.sid} with filename: {filename}')
        
        # Send transcript and position to the new client
        socketio.emit("transcript", {"data": audio_obj['text']}, to=request.sid)
        socketio.emit("position", {
            "file": filename,
            "elapsed_time": elapsed,
            "duration": audio_obj['duration'],
            "timestamp": int(time.time() * 1000)
        }, to=request.sid)
        print(f'Emitted transcripts and position to new client {request.sid}')

# Endpoints
@app.route('/chat-prompt', methods=['POST'])
def chat_prompt():
    user_input = request.json.get('user_prompt')
    
    if user_input:
        with user_prompts_lock:
            user_prompts.append({"user_name": "Some UserName", "text": user_input})

    return jsonify({"message": "Prompt added to queue"}), 200

# NOTE: This is a deprecated route, we don't actually use it play audio
@app.route('/audio', methods=['GET'])
def get_audio():
    with audio_lock:
        if len(audio) >= 1:
            audio_filename = audio[0]  # remove the file from the queue
        else:
            return jsonify({"message": "No audio files available"}), 404

    audio_path = os.path.join("path/to/audio/files", audio_filename)
    if os.path.exists(audio_path):
        return send_file(audio_path, mimetype='audio/wav')
    else:
        return jsonify({"message": "Audio file not found"}), 404
# Careful ^^ deprecated

# if __name__ == '__main__':
    # socketio.run(app, host="0.0.0.0", port=5001, debug=True, use_reloader=False)
