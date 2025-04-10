import groqAudio
import json
import os
import time

def generateAudioFromScripts(conv_topic):
    topic_slug = conv_topic.replace(' ', '-')
    
    script_dir = os.path.join('mock_data', 'scripts', topic_slug)
    audio_dir = os.path.join('mock_data', 'audio', topic_slug)
    os.makedirs(audio_dir, exist_ok=True)

    i = 0
    while True:
        script_path = os.path.join(script_dir, f"{topic_slug}{i}.json")
        audio_path = os.path.join(audio_dir, f"{topic_slug}{i}.wav")

        if not os.path.exists(script_path):
            break  # Stop when the next script is missing

        with open(script_path, 'r') as f:
            data: dict = json.load(f)

        groqAudio.createAudio(
            text=data["text"],
            voice=f"{data['speaker_name']}-PlayAI",
            file_path=audio_path,
            mock=False
        )

        print(f"[Audio saved] {audio_path}")
        time.sleep(15)
        i += 1

generateAudioFromScripts('Music-Theory-and-the-Science-Behind-Viral-Pop-Songs')


# Get the mock transition script

# generic_transition_text = 'Alright we got a message here from User Qwerty imma read it out loud: "Hey Aaliyah and Chip, that was very interesting to hear about audio engineering. I was wondering if you guys could talk about World War 2 and all its quirks." Huh what an interesting topic. Alright guys lets dive straight into talking about World War 2 here.'
# groqAudio.createAudio(text=generic_transition_text, voice="Chip-PlayAI", file_path=f"mock_data/audio/mock_audio_transition.wav", mock=False)