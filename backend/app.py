from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
from flask_socketio import SocketIO, emit
import threading
import time
import os
import random
import io
import json
from pydub import AudioSegment
from getWavFileDuration import get_wav_duration
import groqAudio
import generateContent
from Segment import SegmentsTracker, Segment
import base64
import sys

app = Flask(__name__)
CORS(app)
socketio = SocketIO(app, cors_allowed_origins="*")

# Globals
MOCK_NUMBER = 0
MOCK_MAX = 8
INFLUENCE_DEGREE = 3
MOCKING = False
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MAX_Q_SIZE = 8
MIN_Q_SIZE = 3
DEBUG = False

conv_topic = "Acoustic Treatment In Recording Space"
user_prompts = []
current_playback = None
last_sent_file = None
ST = SegmentsTracker()

ST_lock = threading.Lock()
conv_topic_lock = threading.Lock()
user_prompts_lock = threading.Lock()
current_playback_lock = threading.Lock()

def getRandomTopic():
    topics = []
    with open(os.path.join(BASE_DIR, "mock_data/LoopTopics.txt"), "r") as f:
        topics = [line.strip() for line in f]
    return random.choice(topics)

def loadAnotherTopic() -> int:
    new_conv_topic = getRandomTopic()
    #with ST_lock:
    #    if DEBUG: print("\tloadAnotherTopic():49 st_lock")
    count = ST.load_segments_from_topic(new_conv_topic)
    print(f"{count} new segments loaded on {new_conv_topic}")
    return count

def continousMakeTranscript():
    global MOCK_NUMBER
    while True:
        segment = None
        with ST_lock:
            if DEBUG: print("\t continuousMakeTranscript():59 st_lock")
            for i, s in enumerate(ST.segments):
                if s.text is None:
                    segment = s
                    start_idx = max(0, i - 4)
                    context_segments = [seg for seg in ST.segments[start_idx:i] if seg.text is not None]
                    context = [{'speaker_name': seg.speaker_name, 'text': seg.text} for seg in context_segments]
                    break
        
        if segment:
            with conv_topic_lock:
                current_topic = conv_topic
            
            new_script = generateContent.generateContent(context, current_topic, mock=MOCKING, mock_number=MOCK_NUMBER)
            with ST_lock:
                if DEBUG: print("\t continuousMakeTranscript():74 st_lock")
                segment.speaker_name = new_script['speaker_name']
                segment.text = new_script['text']
                segment.mock_number = MOCK_NUMBER
                if DEBUG: print(f"Generated transcript for {segment.speaker_name}: {segment.text[:30]}...")
            
            if MOCKING:
                MOCK_NUMBER = (MOCK_NUMBER + 1) % (MOCK_MAX + 1)
        
        time.sleep(5)

def continousMakeAudio():
    while True:
        segment = None
        with ST_lock:
            if DEBUG: print("\t continuousMakeTranscript():89 st_lock")
            for s in ST.segments:
                if s.audio_file is None:
                    segment = s
                    break
        
        if segment:
            with conv_topic_lock:
                new_file_name = f'{conv_topic.strip().replace(" ","-")}{round(time.time())}'
            speaker_name = segment.speaker_name or random.choice(['Aaliyah', 'Chip'])
            if DEBUG: print(speaker_name)
            
            audio_path = os.path.join("audio", f"{new_file_name}.wav")
            groqAudio.createAudio(segment.text, speaker_name, audio_path, MOCKING, segment.mock_number)
            
            with ST_lock:
                if DEBUG: print("\t continuousMakeTranscript():105 st_lock")
                segment.add_audio_file(audio_path)
                print(f"Generated audio for {segment.speaker_name} duration: {round(segment.duration, 2)} sec saved to: {new_file_name}")
        
        time.sleep(5)

def continousManageTopic():
    global conv_topic
    while True:
        new_up = None
        with user_prompts_lock:
            if user_prompts:
                new_up = user_prompts.pop(0)
        
        if new_up:
            print(f"Handling new user prompt from {new_up['user_name']} text: {new_up['text']}")
            with conv_topic_lock:
                if DEBUG: print("\t continuousManageTopic():122 conv_topic_lock")
                current_topic = conv_topic
                new_topic = generateContent.determineNewTopic(new_up['text'], MOCKING)
            
            if new_topic:
                with ST_lock:
                    if DEBUG: print("\t continuousManageTopic():127 st_lock")
                    latest_segment = ST.get_first_segment()
                    latest_script = ([{'speaker_name': latest_segment.speaker_name, 'text': latest_segment.text}] if latest_segment else [])
                
                transition_script = generateContent.generateNewTopicContent(
                    new_up['text'], new_up['user_name'], latest_script, current_topic, new_topic, MOCKING
                )
                
                if transition_script['speaker_name'] != 'System':
                    transition_segment = Segment(
                        conv_topic=new_topic,
                        speaker_name=transition_script['speaker_name'],
                        text=transition_script['text'],
                        mock_number='transition'
                    )
                    
                    with conv_topic_lock:
                        conv_topic = new_topic
                        print(f'New Topic is set to: {new_topic}')
                    
                    cp = None
                    with current_playback_lock:
                        cp = current_playback

                    with ST_lock:
                        if DEBUG: print("\t continuousManageTopic():148 st_lock")
                        # ST.clearQ()
                        ST.clearQBeyondXSeconds(35, cp)
                        ST.add_segment(transition_segment)
                        for _ in range(INFLUENCE_DEGREE):
                            ST.add_segment(Segment(conv_topic=new_topic))
                        print(f'Segments is now {len(ST.segments)} long')
                    
                    broadcastNewTopic(new_topic)
        
        time.sleep(3)

def broadcastNewTopic(new_topic):
    socketio.emit("new_topic", {"new_topic": new_topic})

def broadcastPlaybackState(playback, elapsed):
    global last_sent_file
    if playback:
        segment = playback['segment']
        filename = segment.audio_file
        
        if filename and os.path.exists(filename):
            if last_sent_file != filename:
                try:
                    with open(filename, "rb") as f:
                        audio_data = f.read()                        
                        encoded_audio = base64.b64encode(audio_data).decode('utf-8')
                        socketio.emit("audio", {"data": encoded_audio, "file": filename})
                        print(f'Broadcasted audio {filename} to all clients')
                    last_sent_file = filename
                    socketio.emit("transcript", {"data": segment.text})
                except Exception as e:
                    print(f"Error broadcasting {filename}: {e}")
            
            socketio.emit("position", {
                "file": filename,
                "elapsed_time": elapsed,
                "duration": segment.duration,
                "timestamp": int(time.time() * 1000)
            })

def playbackManager():
    global current_playback, last_sent_file
    while True:
        playback_snapshot = None
        elapsed = 0
        
        try:
            with current_playback_lock:
                if DEBUG: print("\t current_playback_lock():196 current_playback_lock")
                if current_playback:
                    elapsed = time.time() - current_playback['start_time']
                    duration = current_playback['segment'].duration
                    
                    if elapsed >= duration:
                        with ST_lock:
                            if DEBUG: print("\t playbackManager():202 st_lock")
                            if ST.segments:
                                ST.segments.pop(0)
                                if len(ST.segments) < MIN_Q_SIZE:
                                    loadAnotherTopic()
                        current_playback = None
                        last_sent_file = None
                        elapsed = 0
                
                if not current_playback:
                    with ST_lock:
                        if DEBUG: print("\t playbackManager():212 st_lock")
                        if ST.segments and ST.segments[0].audio_file is not None:
                            current_playback = {'segment': ST.segments[0], 'start_time': time.time()}
                            print(f"Starting playback: {ST.segments[0].audio_file}")
                        else:
                            print(f"Can't start next playback as audio not in Q")
                
                playback_snapshot = current_playback
            
            broadcastPlaybackState(playback_snapshot, elapsed)
            
            if playback_snapshot:
                remaining = playback_snapshot['segment'].duration - elapsed
                sleep_time = min(max(remaining, 0), 1)
                time.sleep(sleep_time)
            else:
                time.sleep(1)
        except Exception as e:
            print(f"playbackManager error: {e}")
            time.sleep(1)  # Recover and retry

loadAnotherTopic()

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

@socketio.on("connect")
def handle_connect():
    print("Client connected:", request.sid)
    socketio.emit("ready", {"message": "Connected"}, to=request.sid)

@socketio.on("request_playback")
def handle_request_playback():
    sid = request.sid
    print(f"{sid} hit request_playback")
    try:
        cp = None
        with current_playback_lock:
            cp = current_playback
            if DEBUG: print(f"{sid} acquired current_playback_lock")

        if cp:
            segment = cp['segment']
            elapsed = time.time() - cp['start_time']
        else:
            print(f"{sid} no current_playback")
            with ST_lock:
                if DEBUG: print("\t handle_request_playback():268 st_lock")
                print(f"{sid} acquired ST_lock")
                if ST.segments and ST.segments[0].audio_file is not None:
                    segment = ST.segments[0]
                    elapsed = 0
                else:
                    print(f"{sid} No playable segments available.")
                    return
        
        filename = segment.audio_file
        if DEBUG: print(f"{sid} HERE filename {filename}")
        if filename and os.path.exists(filename):
            try:
                audio_seg = AudioSegment.from_file(filename)
                if DEBUG: print(f"{sid} Loaded AudioSegment")
                trimmed_audio = audio_seg[int(elapsed * 1000):]
                if DEBUG: print(f"{sid} Trimmed audio")
                
                buffer = io.BytesIO()
                trimmed_audio.export(buffer, format="wav")
                buffer.seek(0)
                audio_data = buffer.read()
                if DEBUG: print(f"{sid} Exported audio to buffer")
                encoded_audio = base64.b64encode(audio_data).decode('utf-8')
                socketio.emit("audio", {"data": encoded_audio, "file": filename})
                print(f"{sid} Emitted audio file {filename}")
                if segment.text:
                    socketio.emit("transcript", {"data": segment.text}, to=sid)
                if segment.duration:
                    socketio.emit("position", {
                        "file": filename,
                        "elapsed_time": elapsed,
                        "duration": segment.duration,
                        "timestamp": int(time.time() * 1000)
                    }, to=sid)
            except Exception as e:
                print(f"{sid} Error processing audio: {e}")
        else:
            print(f"{sid} No valid audio file: {filename}")
    except Exception as e:
        print(f"{sid} Error in handle_request_playback: {e}")
    finally:
        if DEBUG: print(f"{sid} Released locks")

@app.route('/chat-prompt', methods=['POST'])
def chat_prompt():
    user_input = request.json.get('user_prompt')
    if user_input:
        with user_prompts_lock:
            user_prompts.append({"user_name": "User 573", "text": user_input})
    return jsonify({"message": "Prompt added to queue"}), 200

@app.route('/health')
def health():
    return "OK", 200

if __name__ == '__main__':
    socketio.run(app, host="0.0.0.0", port=5001, debug=True, use_reloader=False)
    DEBUG = True #if "-v" in sys.argv: DEBUG = True