import groqAudio
import json
import os
import time

for i in range(8):
    with open(f'mock_data/scripts/mock_script{i}.json', 'r') as f:
        data: dict = json.load(f)
        # print(script['text'])
        groqAudio.createAudio(text=data["text"],voice=f"{data["speaker_name"]}-PlayAI",file_path=f"mock_data/audio/mock_audio{i}.wav",mock=False)
        f.close()
    # groqAudio.createAudio("",'Chip-PlayAI',f'''mock_data/audio/out{i}.wav''')
    time.sleep(15)


# Get the mock transition script

# generic_transition_text = 'Alright we got a message here from User Qwerty imma read it out loud: "Hey Aaliyah and Chip, that was very interesting to hear about audio engineering. I was wondering if you guys could talk about World War 2 and all its quirks." Huh what an interesting topic. Alright guys lets dive straight into talking about World War 2 here.'
# groqAudio.createAudio(text=generic_transition_text, voice="Chip-PlayAI", file_path=f"mock_data/audio/mock_audio_transition.wav", mock=False)