import os
import requests
import json
from dotenv import load_dotenv
load_dotenv()
import random

GROQ_API_KEY = os.environ.get("GROQ_API_KEY")
GROQ_API_URL = "https://api.groq.com/openai/v1/chat/completions"

def format_script_history(scripts):
    formatted = ""
    for turn in scripts:
        formatted += f"{turn['speaker_name']}: {turn['text']}\n"
    return formatted.strip()

def generateContent(scripts, conv_topic, mock=True, mock_number=0):
    if mock:
        mock_file_path = f"mock_data/scripts/mock_script{mock_number}.json"
        try:
            with open(mock_file_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            print(f"Error loading mock script {mock_number}:", e)
            return {
                "speaker_name": "System",
                "text": "Mock script could not be loaded."
            }
    
    history = format_script_history(scripts)
    prompt = f"""
You are helping write an ongoing podcast about **{conv_topic}**.

Here is the previous script so far:
{history}

Continue the podcast with the next speaker's turn. Keep the tone natural, insightful, and conversational. Be creative, stay on topic, and make the transition smooth. Use only one speaker for this turn.
"""

    response = requests.post(
        GROQ_API_URL,
        headers={"Authorization": f"Bearer {GROQ_API_KEY}"},
        json={
            "model": "llama-3.3-70b-versatile",  # adjust if needed
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0.7
        }
    )

    try:
        json_data = response.json()
        #print("Groq Response JSON:", json_data)  # Debug print

        message = json_data['choices'][0]['message']['content']
        lines = message.strip().split("\n", 1)
        if len(lines) == 2 and ":" in lines[0]:
            speaker, text = lines[0].split(":", 1)
            return {"speaker_name": speaker.strip(), "text": text.strip()}
        else:
            return {"speaker_name": "AI Narrator", "text": message.strip()}
    except Exception as e:
        print("Error parsing Groq response:", e)
        print("Raw response text:", response.text)
        return {"speaker_name": "System", "text": "Error generating script."}

def determineNewTopic(user_prompt, mock=True):
    if mock:
        return f'This is some new topic {random.randint(0, 100)}'

    prompt = f"""
        A new user prompt has come in saying: {user_prompt}
        If this user prompt is invalid, inappropriate, or does not provide a topic to discuss, simply return the word NONE and nothing else.
        Otherwise, deduce the topic the user would like to hear from the user_prompt and state it in a few words. Return only those words.
        """
    
    response = requests.post(
        GROQ_API_URL,
        headers={"Authorization": f"Bearer {GROQ_API_KEY}"},
        json={
            "model": "llama-3.3-70b-versatile",  # adjust if needed
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0.7
        }
    )

    try:
        json_data = response.json()
        print("Groq Response JSON:", json_data) # Debug print
        message = json_data['choices'][0]['message']['content']
        if message == 'NONE':
            return None
        else:
            return message
    except Exception as e:
        print("Error parsing Groq response:", e)
        print("Raw response text:", response.text)
        return None


def generateNewTopicContent(user_prompt_text, user_name, scripts, old_conv_topic, new_conv_topic, mock=True):
    if mock:
        mock_file_path = f"mock_data/scripts/mock_script_transition.json"
        try:
            with open(mock_file_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            print(f"Error loading mock script transition:", e)
            return {
                "speaker_name": "System",
                "text": "Mock script could not be loaded."
            }
        
    scripts = scripts[:1] # we only really need the last bit
    history = format_script_history(scripts)
    prompt = f"""
        You are helping write an ongoing podcast which has been discussing **{old_conv_topic}**.

        Here is the last script:
        {history}

        Continue the podcast with either Chip or Aaliyah turn. But now it is time for a transition.
        Make a smooth transition where you quickly wrap up the last topic.
        Then say that there is a new message from listener {user_name}
        Read the message from the user: {user_prompt_text}
        Then transition into this new discussing {new_conv_topic}

        Keep the tone natural, insightful, and conversational. Be creative and make the transition smooth. Use only one speaker for this turn.
        """
    response = requests.post(
        GROQ_API_URL,
        headers={"Authorization": f"Bearer {GROQ_API_KEY}"},
        json={
            "model": "llama-3.3-70b-versatile",  # adjust if needed
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0.7
        }
    )

    try:
        json_data = response.json()
        print("Groq Response JSON:", json_data)  # Debug print

        message = json_data['choices'][0]['message']['content']
        lines = message.strip().split("\n", 1)
        if len(lines) == 2 and ":" in lines[0]:
            speaker, text = lines[0].split(":", 1)
            return {"speaker_name": speaker.strip(), "text": text.strip()}
        else:
            return {"speaker_name": "AI Narrator", "text": message.strip()}
    except Exception as e:
        print("Error parsing Groq response:", e)
        print("Raw response text:", response.text)
        return {"speaker_name": "System", "text": "Error generating script."}
