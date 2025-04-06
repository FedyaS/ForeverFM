
from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
import threading
import time
import os
from getWavFileDuration import get_wav_duration
from flask_socketio import SocketIO, emit


# Initialize Flask app and CORS
app = Flask(__name__)
CORS(app)
socketio = SocketIO(app, cors_allowed_origins="*")  # Allow CORS for Next.js frontend

# Some stupid globals
MOCKING = True
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MAX_Q_SIZE = 10
should_be_generating_new_data = True

# Shared variables
conv_topic = "Initial Topic"
scripts = [] # [{speaker_name: '', text: ''}, ...] # Newest last
user_prompts = [] # [{user_name: '', text: ''}, ...] # Newest last
audio = [] # [{speaker_name: '', duration: '', text: '', filename: ''}] # Newest last
current_playback = None  # Global playback state: {'audio': audio_obj, 'start_time': timestamp}
last_sent_file = None


# Lock for thread safety
scripts_lock = threading.Lock()
audio_lock = threading.Lock()
conv_topic_lock = threading.Lock()
user_prompts_lock = threading.Lock()
current_playback_lock = threading.Lock()  # Lock for current_playback

# Thread functions
def continousMakeTranscript():
    while True:
        time.sleep(5)  # sim time taken for processing
        # Make a call to
        # new_script = generateContent()
        new_script = {'speaker_name': 'Chip', 'text': 'blah blah blah'}
        # here
        
        print(f"Generated script for {new_script['speaker_name']} saying: {new_script['text'][:20]}")
        
        with scripts_lock:
            scripts.append(new_script)
            if len(scripts) >= 10:
                scripts.pop(0)
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
            
            # new_script = {'speaker_name': 'Chip', 'text': 'blah blah blah', is_audio_generated: False}

        # Just to test:
        with user_prompts_lock:
            print(user_prompts)
        
mock_audio_count = 0
def continousMakeAudio():
    global mock_audio_count
    while True:
        time.sleep(5)  # sim time taken for processing
        
        script = None
        with scripts_lock:
            if len(scripts) >= 1:
                script = scripts[0]
        
        # script = {'speaker_name': 'Aaliyah', 'text': 'blah blah'} # Mock
        if script and should_be_generating_new_data:
            # Generate our audio
            new_file_name = f'{round(time.time() * 10)}_audio.wav'
            groqAudio.createAudio(script['text'], f'{script['speaker_name']}-PlayAI', f'audio/{new_file_name}', MOCKING, script['mock_number'])
            
            # new_file_name = 'speech.wav' # For now
            new_file_name = f'mock_audio{mock_audio_count}.wav'
            mock_audio_count += 1
            if mock_audio_count > 7:
                mock_audio_count = 0
            #new_file_name = f"{script['speaker_name']}-{round(time.time() * 1000)}"
            

            # Make a call to
            # generateAudio(new_file_name)
            
            duration = get_wav_duration(new_file_name, MOCKING)
            new_audio_object = {
                'speaker_name': script['speaker_name'],
                'duration': duration,
                'text': script['text'],
                'filename': new_file_name
            }

            print(new_audio_object)
            print(audio)
            with audio_lock:
                audio.append(new_audio_object)
                if len(audio) > 10:
                    audio.pop(0) # For now
            
            print(f"Generated audio for {script['speaker_name']} duration: {round(duration, 2)} sec saved to: {new_file_name}")
        

def continousManageTopic():
    global should_be_generating_new_data, conv_topic, scripts, audio
    while True:
        new_up = None
        with user_prompts_lock:
            if user_prompts:
                new_up = user_prompts[0]
                user_prompts.pop(0)
        
        if new_up:
            print(f'Handling new user prompt from {new_up['user_name']} text: {new_up['text']}')
            new_topic = generateContent.determineNewTopic(new_up['text'], MOCKING)
            if new_topic:
                should_be_generating_new_data = False
                latest_spoken_script = []
                with scripts_lock:
                    if scripts:
                        latest_spoken_script = scripts[0]
                old_topic = ''
                with conv_topic_lock:
                    old_topic = conv_topic
                    
                transition_script = generateContent.generateNewTopicContent(new_up['text'], new_up['user_name'], latest_spoken_script, old_topic, new_topic, MOCKING)
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
                        audio = audio[:2] # May need to change the logic here
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
        if MOCKING:
            audio_path = os.path.join(BASE_DIR, "mock_data", "audio", filename)
        else:
            audio_path = os.path.join(BASE_DIR, "audio", filename)

        # Only broadcast if we haven't already sent this file
        if last_sent_file != filename and os.path.exists(audio_path):
            with open(audio_path, "rb") as f:
                audio_data = f.read()
                socketio.emit("audio", {"data": audio_data, "file": filename})
            
            last_sent_file = filename
            socketio.emit("transcript", {"data": audio_obj['text']})

        # Always broadcast position
        socketio.emit("position", {
            "file": filename,
            "elapsed_time": elapsed,
            "duration": audio_obj['duration'],
            "timestamp": int(time.time() * 1000)
        })


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
                if elapsed >= duration:
                    with audio_lock:
                        if audio:
                            audio.pop(0)
                    current_playback = None
                    last_sent_file = None
                    elapsed = 0

            if not current_playback and audio:
                with audio_lock:
                    if audio:
                        current_playback = {'audio': audio[0], 'start_time': time.time()}
                        print(f"Starting playback: {current_playback['audio']['filename']}")
            
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

thread1.start()
thread2.start()
thread3.start()
thread4.start()

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
        # Send transcript and position to the new client
        socketio.emit("transcript", {"data": audio_obj['text']}, to=request.sid)
        socketio.emit("position", {
            "file": filename,
            "elapsed_time": elapsed,
            "duration": audio_obj['duration'],
            "timestamp": int(time.time() * 1000)
        }, to=request.sid)

def get_current_audio():
    # Retrieve the oldest audio from the queue, if available
    with audio_lock:
        if audio:
            return audio[0]  # Returns dict with speaker_name, duration, text, filename
        return None

def send_audio_data(sid, current_audio, last_file):
    # Send audio file and metadata when a new file starts
    if current_audio and (not last_file or last_file != current_audio['filename']):
        filename = current_audio['filename']
        audio_path = os.path.join("./audio", filename)
        
        # Notify client of the new file
        socketio.emit("new_file", {"file": filename}, to=sid)
        
        # Send the audio file as binary data if it exists
        if os.path.exists(audio_path):
            with open(audio_path, "rb") as f:
                audio_data = f.read()
                socketio.emit("audio", {"data": audio_data}, to=sid)  # Send the data as part of the payload
        
        # Send the transcript associated with this audio
        socketio.emit("transcript", {"data": current_audio['text']}, to=sid)
        return filename  # Return the filename to mark it as sent
    return last_file  # No new file, keep the last one

def send_position_update(sid, current_audio, last_file, start_time):
    # Send playback position if there's an active audio file
    if last_file and current_audio:
        time_ms = time.time()
        elapsed = time_ms - start_time
        socketio.emit("position", {
            "file": last_file,
            "elapsed_time": elapsed,
            "duration": current_audio['duration'],
            "timestamp": int(time_ms)
        }, to=sid)

def stream_to_client(sid):
    # Main streaming loop for a connected client
    last_file = None  # Track the last file sent
    start_time = None  # When the current file started

    while True:
        # Get the current audio from the queue
        current_audio = get_current_audio()

        if current_audio:
            # Check if the current audio has finished playing
            if last_file and start_time and (time.time() - start_time >= current_audio['duration']):
                last_file = None  # Reset to allow the next file
                start_time = None

            # Send audio data and update last_file if a new file is processed
            if not last_file:
                start_time = time.time()
            last_file = send_audio_data(sid, current_audio, last_file)

            # Send periodic position updates
            send_position_update(sid, current_audio, last_file, start_time)

        # Wait before the next iteration
        time.sleep(1)  # Update every second


# Endpoints
@app.route('/chat-prompt', methods=['POST'])
def chat_prompt():
    user_input = request.json.get('user_prompt')
    
    if user_input:
        with user_prompts_lock:
            user_prompts.append({"user_name": "Some UserName", "text": user_input})

    return jsonify({"message": "Prompt added to queue"}), 200

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

if __name__ == '__main__':
    socketio.run(app, host="0.0.0.0", port=5001, debug=True, use_reloader=True)
