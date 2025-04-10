import os
import requests
import json
from dotenv import load_dotenv
load_dotenv()
import random

WORD_LIMIT = 150
GROQ_API_KEY = os.environ.get("GROQ_API_KEY")
GROQ_API_URL = "https://api.groq.com/openai/v1/chat/completions"

def format_script_history(scripts):
    formatted = ""
    for turn in scripts:
        formatted += f"{turn['speaker_name']}: {turn['text']}\n"
    return formatted.strip()

def makeFirstScriptOnTopic(speaker, not_speaker, conv_topic):
    prompt = f"""
You are {speaker}, an AI host on a live podcast called *ForeverFM* — a 24/7 AI-driven show where two bots dive into topics like tech, finance, health, gaming, and more.

The conversation goes on 24/7 but is now shifting to **{conv_topic}**. You may mention how the podcast is still live because it's always live... that's the point. Maybe even make a joke or smart remark about it.
You may say to listeners that they are listening to *ForeverFM*.
Do not say welcome back or anything like that because there are no breaks.
Be clear that you are now shifting into a discussion about **{conv_topic}**

Avoid sounding robotic or repetitive.
Kick off the discussion in a natural, engaging, and conversational tone. Set the stage for your co-host {not_speaker} and the audience. Feel free to reference {not_speaker}, but remember they haven’t spoken yet.

Keep it concise (under {WORD_LIMIT} words) and generate only your own dialogue — just {speaker}'s script.
"""
    return prompt

def makeContinuationScriptOnTopic(speaker, not_speaker, conv_topic, history):
    prompt = f"""
Your name is {speaker}, and you're part of a live podcast discussing **{conv_topic}**.

Here's what has been said so far:
{history}

Now it's your turn to speak. Respond to your co-host {not_speaker}, continuing the conversation naturally. Be insightful, creative, and conversational. 
Avoid sounding robotic or repetitive. You may, but don't have to mention them by name.
Avoid repeating what was already said. Make a smooth transition, and keep the flow dynamic.

Limit your response to {WORD_LIMIT} words. Only generate the script for {speaker}.
"""
    return prompt

def makeLastScriptOnTopic(speaker, not_speaker, conv_topic, history):
    prompt = f"""
You are {speaker}, one of two AI hosts on a live podcast currently discussing **{conv_topic}**.

Here's what has been said so far:
{history}

It's now time to wrap up the conversation on {conv_topic}. Respond to your co-host {not_speaker} naturally — keep the tone conversational, creative, and reflective. 
Avoid sounding robotic or repetitive. No need to summarize everything, just leave a strong final thought or a clever closing remark.

Guide the conversation toward a new topic, but don’t mention what it is — keep it open-ended and seamless for a topic switch (handled by a separate script).

Limit your response to {WORD_LIMIT} words. Only generate the script for {speaker}.
"""
    return prompt


def generateContent(scripts, conv_topic, mock=True, mock_number=0, speaker=None, last_script_on_topic=False):
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
    
    if speaker is None:
        if scripts: # try to get last speaker to determine current speaker
            last_speaker = scripts[-1]['speaker_name']
            speaker = 'Chip' if last_speaker == 'Aaliyah' else 'Aaliyah'
        else: # resort to random
            speaker = random.choice(['Chip', 'Aaliyah'])
    
    not_speaker = 'Chip' if speaker == 'Aaliyah' else 'Aaliyah'

    if last_script_on_topic:
        history = format_script_history(scripts)
        prompt = makeLastScriptOnTopic(speaker, not_speaker, conv_topic, history)

    elif not scripts:
        prompt = makeFirstScriptOnTopic(speaker, not_speaker, conv_topic)

    else:
        history = format_script_history(scripts)
        prompt = makeContinuationScriptOnTopic(speaker, not_speaker, conv_topic, history)

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
        
        return {"speaker_name": speaker.strip(), "text": message.strip().replace('"', '')}
        
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
