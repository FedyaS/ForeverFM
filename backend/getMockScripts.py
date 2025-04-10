from generateContent import generateContent
import json
import os
import time

# Generates intro script, middle scripts, last script and saves to appropriate directory
def generateAllScripts(conv_topic, count):
    topic_slug = conv_topic.replace(' ', '-')
    dir_path = os.path.join('./mock_data/scripts', topic_slug)

    os.makedirs(dir_path, exist_ok=True)

    scripts = []

    # Intro script (index 0)
    intro_script = generateContent(scripts, conv_topic, mock=False)
    scripts.append(intro_script)
    intro_path = os.path.join(dir_path, f"{topic_slug}0.json")
    with open(intro_path, 'w') as f:
        json.dump(intro_script, f, indent=4)
    print(f"[Saved] Intro: {intro_path}")
    time.sleep(1)

    # Middle scripts (indexes 1 to count-2)
    for i in range(1, count - 1):
        middle_script = generateContent(scripts, conv_topic, mock=False)
        scripts.append(middle_script)
        file_path = os.path.join(dir_path, f"{topic_slug}{i}.json")
        with open(file_path, 'w') as f:
            json.dump(middle_script, f, indent=4)
        print(f"[Saved] Script {i}: {file_path}")
        time.sleep(8)

    # Final script (index count - 1)
    final_script = generateContent(scripts, conv_topic, mock=False, last_script_on_topic=True)
    scripts.append(final_script)
    final_path = os.path.join(dir_path, f"{topic_slug}{count - 1}.json")
    with open(final_path, 'w') as f:
        json.dump(final_script, f, indent=4)
    print(f"[Saved] Final script: {final_path}")


def generateLastScript(conv_topic):
    # Normalize topic to match filenames and folder name
    topic_slug = conv_topic.replace(' ', '-')
    dir_path = os.path.join('./mock_data/scripts', topic_slug)

    # Ensure directory exists
    if not os.path.isdir(dir_path):
        raise FileNotFoundError(f"Directory does not exist: {dir_path}")

    # Load existing scripts
    scripts = []
    i = 0
    while True:
        file_name = f"{topic_slug}{i}.json"
        file_path = os.path.join(dir_path, file_name)
        if os.path.exists(file_path):
            with open(file_path, 'r') as f:
                scripts.append(json.load(f))
            i += 1
        else:
            break  # Stop when no more sequential files

    # Generate the new script
    new_script = generateContent(scripts, conv_topic, False, last_script_on_topic=True)
    print(new_script)

    # Save it as the next file in sequence
    next_file_name = f"{topic_slug}{i}.json"
    next_file_path = os.path.join(dir_path, next_file_name)
    with open(next_file_path, 'w') as json_file:
        json.dump(new_script, json_file, indent=4)

    # Optional: small pause if you ever want rate-limiting
    time.sleep(1)

# generateLastScript('Startups-and-What-It-Takes-to-Succeed')
generateAllScripts('The-Rise-of-Nvidia', 8)