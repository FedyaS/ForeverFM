import json
import os
from getWavFileDuration import get_wav_duration

class Segment:
    def __init__(self, conv_topic=None, speaker_name=None, text=None, audio_file=None, duration=None, mock_number=None):
        self.conv_topic = conv_topic
        self.speaker_name = speaker_name
        self.text = text
        self.audio_file = audio_file
        self.duration = duration
        self.mock_number = mock_number
    
    def add_audio_file(self, audio_file):
        self.audio_file = audio_file
        self.duration = get_wav_duration(audio_file)
    
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
        self.mock_number = count if count else None

        audio_exists = os.path.exists(audio_path)
        if audio_exists:
            self.add_audio_file(audio_path)

        return audio_exists

class SegmentsTracker:
    def __init__(self, segments=None):
        self.segments = segments if segments is not None else []
    
    def add_segment(self, segment):
        self.segments.append(segment)
        if len(self.segments) > 8:  # MAX_Q_SIZE
            popped = self.segments.pop(0)
            if popped.audio_file and os.path.exists(popped.audio_file):
                os.remove(popped.audio_file)  # Clean up mock audio
    
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
            
            if segment.text is None:  # No script found, stop loading
                break
                
            self.add_segment(segment)
            count += 1
        
        return count
    
    def clearQ(self):
        """
        Keep only the first segment, clear the rest for user prompt response.
        """
        if self.segments:
            self.segments = self.segments[:1]