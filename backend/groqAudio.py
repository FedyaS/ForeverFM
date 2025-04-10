import os
import shutil
from groq import Groq
from dotenv import load_dotenv
load_dotenv()

client = Groq(api_key=os.environ.get("GROQ_API_KEY"))

def createAudio(text: str = "", voice: str = "Aaliyah-PlayAI", file_path: str = "audio/out", mock: bool = True, mock_number: str = '0') -> None:
    voice += "-PlayAI"
    if mock:
        mock_audio_path = f"mock_data/{file_path}{mock_number}.wav"
        try:
            shutil.copy(mock_audio_path, file_path)
            print(f"[Mock] Copied {mock_audio_path} to {file_path}")
        except Exception as e:
            print(f"[Mock] Failed to copy mock audio {mock_number}:", e)

    # Test

    else:
        # Real audio generation
        model = "playai-tts"
        response_format = "wav"

        response = client.audio.speech.create(
            model=model,
            voice=voice,
            input=text,
            response_format=response_format
        )

        response.write_to_file(file_path)
