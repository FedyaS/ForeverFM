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
import json
from pydub import AudioSegment
import io

# Initialize Flask app and CORS
app = Flask(__name__)
CORS(app)
socketio = SocketIO(app, cors_allowed_origins="*")  # Allow CORS for Next.js frontend

# Some stupid globals
MOCK_NUMBER = 0
MOCK_MAX = 8
INFLUENCE_DEGREE = 3 # Number of audios generated per Influence comment. An additional one happens before this, which is the transition.
MOCKING = False
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MAX_Q_SIZE = 8

# Shared variables
conv_topic = "Acoustic Treatment In Recording Space0" # file_name .replace("-"," ")
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

# Load Initial Audios and Scripts
def loadAnotherTopic(file_paths:list = [""],mock_max:int = 7) -> int:
    '''Loads a list of file_paths into audio[] and scripts[]. This function enables our program to run 24/7
    without costing us anything extra.
    `file_path`: List of file_paths for audios and scripts. Requires both to be named the same thing.
    `mock_max`: The number of mock audios and scripts to pull for each file_path. In other words the MAX MOCK NUMBER.
    
    @return: # of things actually appended'''
    c=0
    for fp in file_paths:
        for i in range(mock_max):
            new_script:dict = None
            with open(os.path.join(BASE_DIR, "mock_data", "scripts", f"{fp}{i}.json"),"r") as f:
                new_script = json.load(f)
                new_script['mock_number'] = MOCK_NUMBER
                new_script['is_audio_generated'] = True

                with scripts_lock:
                    scripts.append(new_script)

                audio_fn = os.path.join(BASE_DIR, "mock_data", "audio", f"{fp}{i}.wav")
                duration = get_wav_duration(audio_fn)
                new_audio = {
                    'speaker_name': new_script['speaker_name'],
                    'duration': duration,
                    'text': new_script['text'],
                    'filename': audio_fn
                }

                with audio_lock:
                    audio.append(new_audio)

                c+=1
    return c


# Thread functions
def continousMakeTranscript():
    """Continously generates content (scripts) to be spoken.
    Update: This should only work for chat-prompted stuff now!"""
    #global MOCK_NUMBER
    global MOCK_NUMBER
    should_be_generating_new_data = False
    with conv_topic_lock:
        cur_topic = conv_topic
    while True:
        len_scripts = 0
        with scripts_lock:
            len_scripts = len(scripts)
        with conv_topic_lock:
            if conv_topic != cur_topic:
                should_be_generating_new_data = True
            else:
                should_be_generating_new_data = False
            cur_topic = conv_topic
        
        if should_be_generating_new_data:
            # Send only the (next) 4 scripts for context (before clearing them)
            new_scripts = list()
            for i in range(INFLUENCE_DEGREE):
                new_script = generateContent.generateContent(scripts[:4], conv_topic, mock=MOCKING, mock_number=MOCK_NUMBER)
                new_script['mock_number'] = MOCK_NUMBER
                new_script['is_audio_generated'] = False
                with scripts_lock:
                    scripts.append(new_script)
                    #if len(scripts) >= MAX_Q_SIZE and scripts[0]['is_audio_generated']:
                    #    scripts.pop(0)
            
            if MOCKING:
                MOCK_NUMBER += 1
                if MOCK_NUMBER > MOCK_MAX:
                    MOCK_NUMBER = 0

            loadAnotherTopic(file_paths=["Acoustic-Treatment-In-Recording-Space"],mock_max=MOCK_MAX)

            # new_script = {'speaker_name': 'Chip', 'text': 'blah blah blah', 'mock_number': 1, 'is_audio_generated': False}

            print(f"Generated script for {new_script['speaker_name']} saying: {new_script['text'][:20]}")

            '''with scripts_lock:
                scripts.append(new_script)
                if len(scripts) >= MAX_Q_SIZE and scripts[0]['is_audio_generated']:
                    scripts.pop(0)'''

        time.sleep(5)  # not sure if we really need this, but it was working with it so keeping it here
        
def continousMakeAudio():
    """Continously checks the scripts Q and generates new audio, appends the audio to audio var"""
    while True:
        script = None
        script_index = None

        with scripts_lock:
            for i, s in enumerate(scripts):
                #print("===s===\n",scripts,enumerate(scripts),"\n===s===")
                if not s['is_audio_generated']: # Grab the first script that doesn't have audio generated
                    script = s
                    script_index = i
                    break
        
        # script = {'speaker_name': 'Aaliyah', 'text': 'blah blah'} # Mock
        
        if script:
            # Generate our audio
            with conv_topic_lock:
                new_file_name = f'{conv_topic.strip().replace(" ","-")}{round(time.time())}'
            speaker_name = script['speaker_name']
            
            # Dirty fix as sometimes generateContent() returns a weird speaker name
            if speaker_name not in ['Aaliyah', 'Chip']:
                speaker_name = random.choice(['Aaliyah', 'Chip'])
            
            # Creates audio wav
            groqAudio.createAudio(script['text'], f'{speaker_name}', f'audio/{new_file_name}.wav', MOCKING, script['mock_number'])
            # Creates script json
            with open(f"scripts/{new_file_name}.json","w") as f:
                json.dump(script, f)

            duration = get_wav_duration(f'audio/{new_file_name}.wav')
            new_audio_object = {
                'speaker_name': script['speaker_name'],
                'duration': duration,
                'text': script['text'],
                'filename': f'audio/{new_file_name}'
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
        elif len(audio) < INFLUENCE_DEGREE: # this can be any number really, its when the topic is placed on the back of queue again
            print("Audio queue is small, adding random topic... len(audio) =",len(audio))
            loadAnotherTopic(file_paths=["Acoustic-Treatment-In-Recording-Space"],mock_max=MOCK_MAX)
            print("Audio queue restocked! len(audio) =",len(audio))

        time.sleep(5)  # not sure if we really need this, but it was working with it so keeping it here
        

def continousManageTopic():
    """Continously check for new user topics, if a new user topic is found handle the transition"""
    # Note this function will quickly jump from topic to topic if there are many user prompts, will need to implement logic to limit topic jumps
    
    global conv_topic, scripts, audio
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
                #should_be_generating_new_data = False # Pauses script / audio generation while the topic is being switched
                
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
                print(f'Broadcasted audio {filename.split("backend/")[1].strip()} to all clients')
            
            last_sent_file = filename
            socketio.emit("transcript", {"data": audio_obj['text']})

        # Always broadcast position
        socketio.emit("position", {
            "file": filename,
            "elapsed_time": elapsed,
            "duration": audio_obj['duration'],
            "timestamp": int(time.time() * 1000)
        })
        #print(f'Broadcasted position {elapsed} of {filename.split("backend/")[1].strip()} to all clients')


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
                        #print(current_playback['audio'])
                        print(f"Starting playback: {current_playback['audio']['filename'].split("backend/")[1]}")
            
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

loadAnotherTopic(file_paths=["Acoustic-Treatment-In-Recording-Space"],mock_max=MOCK_MAX)

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
print("Background threads running!")

# Whenever a new client connects to the websocket this runs
@socketio.on("connect")
def handle_connect():
    print("Client connected:", request.sid)

    cp = None
    with current_playback_lock:
        cp = current_playback

    if cp:
        audio_obj = cp['audio']
        elapsed = time.time() - cp['start_time']
    else:
        with audio_lock:
            if audio:
                # If no current playback, but audio queue is not empty, send the first audio
                audio_obj = audio[0]
                elapsed = 0
            else:
                # No audio to send at all
                print("No current playback or audio queued.")
                return

    filename = audio_obj['filename']
    audio_path = os.path.join("./audio", filename)

    if os.path.exists(audio_path):
        # Load and trim the audio using pydub
        try:
            audio_seg = AudioSegment.from_file(audio_path)
            trimmed_audio = audio_seg[int(elapsed * 1000):]  # cut off beginning

            # Convert trimmed audio to bytes
            buffer = io.BytesIO()
            trimmed_audio.export(buffer, format="wav")
            buffer.seek(0)
            audio_data = buffer.read()

            socketio.emit("audio", {"data": audio_data, "file": filename}, to=request.sid)
            print(f'Emitted trimmed audio to new client {request.sid} with filename: {filename}')

            socketio.emit("transcript", {"data": audio_obj['text']}, to=request.sid)
            socketio.emit("position", {
                "file": filename,
                "elapsed_time": elapsed,
                "duration": audio_obj['duration'],
                "timestamp": int(time.time() * 1000)
            }, to=request.sid)
            print(f'Emitted transcript and position to new client {request.sid}')

        except Exception as e:
            print(f"Error processing audio for {request.sid}: {e}")

# Endpoints
@app.route('/chat-prompt', methods=['POST'])
def chat_prompt():
    user_input = request.json.get('user_prompt')
    
    if user_input:
        with user_prompts_lock:
            user_prompts.append({"user_name": "User 573", "text": user_input})

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

@app.route('/health')
def health():
    return "OK", 200

if __name__ == '__main__':
    socketio.run(app, host="0.0.0.0", port=5001, debug=True, use_reloader=False)
