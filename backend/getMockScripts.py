import generateContent
import json
import os
import time

conv_topic = "Startups and What It Takes to Succeed"
scripts = []

for i in range(8):
    new_script = generateContent.generateContent(scripts, conv_topic, False)
    print(new_script)
    scripts.append(new_script)
    file_name = f'''{conv_topic.replace(' ', '-')}{i}.json'''
    file_path = os.path.join('./mock_data./scripts',file_name)
    with open(file_path, 'w') as json_file:
        json.dump(new_script, json_file, indent=4)  # indent=4 makes the JSON more readable
    time.sleep(8)