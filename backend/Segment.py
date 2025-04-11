import json
import os
from getWavFileDuration import get_wav_duration 

class Segment:
    def __init__(self, conv_topic=None, speaker_name=None, text=None, audio_file=None, duration=None):    
        self.conv_topic = conv_topic
        self.speaker_name = speaker_name
        self.text = text
        self.audio_file = audio_file
        self.duration = duration
    
    def add_audio_file(self, audio_file):
        duration = get_wav_duration(audio_file)
        self.audio_file = audio_file
        self.duration = duration
    
    def load_from_mock(self, conv_topic, count=0) -> bool:
        conv_topic = conv_topic.replace(' ', '-')  # Fix the topic for paths
        
        script_path = os.path.join("mock_data", "scripts", conv_topic, f"{conv_topic}{count}.json")
        audio_path = os.path.join("mock_data", "audio", conv_topic, f"{conv_topic}{count}.wav")

        try:
            with open(script_path, 'r') as f:
                script = json.load(f)
        except FileNotFoundError:
            self.text = None  # Signal failure
            return False
        
        self.conv_topic = conv_topic
        self.speaker_name = script['speaker_name']
        self.text = script['text']

        audio_exists = os.path.exists(audio_path)
        if audio_exists:
            self.audio_file = audio_path
            self.duration = get_wav_duration(audio_path)

        return audio_exists


class SegmentsTracker:
    def __init__(self, segments=None):
        self.segments = segments if segments is not None else []
    
    def add_segment(self, segment):
        self.segments.append(segment)
    
    def get_first_segment(self):
        return self.segments[0] if self.segments else None
    
    def load_segments_from_topic(self, conv_topic):
        """
        Load all segments for a given conv_topic from mock data and append to self.segments.
        Iterates through possible script/audio files until a script is missing.
        """
        conv_topic = conv_topic.replace(' ', '-')  # Normalize topic for paths
        count = 0
        
        while True:
            segment = Segment()
            audio_loaded = segment.load_from_mock(conv_topic, count)
            
            if not audio_loaded:  # No script found, stop loading
                break
                
            self.segments.append(segment)
            count += 1
        
        return count
    
    def clearQ(self):
        """
        Keep only the first segment, clear the rest for user prompt response.
        """
        if self.segments:
            self.segments = self.segments[:1]
        # If empty, stays empty

# Play around with it --- 
# tracker = SegmentsTracker()
# tracker.load_segments_from_topic("The Rise of Nvidia")  # Loads small-talk0.json, small-talk1.json, etc.
# print(len(tracker.segments))  # e.g., 3 if three scripts exist
# print(tracker.segments[0])
# tracker.clearQ()
# print(len(tracker.segments))  # 1 (only first segment remains)