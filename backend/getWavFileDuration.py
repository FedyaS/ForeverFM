import soundfile as sf
import os

def get_wav_duration(file_path):
    with sf.SoundFile(file_path) as file:
        duration = len(file) / file.samplerate  # len(file) gives number of frames
    return duration

def countSequentialWavs(base_name):
    i = 0
    while True:
        file_path = os.path.join(BASE_DIR, f"mock_data/audio/{base_name}", f"{base_name}{i}.wav")
        if not os.path.exists(file_path):
            break
        i += 1
    return i