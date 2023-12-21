__author__ = 'looser'

import json
import os
import re
import shutil
from datetime import datetime

def copy_with_new_name(source, copy_dir):
    file_name = os.path.basename(source)
    copy_to = os.path.join(copy_dir, file_name)

    # Check if the destination file already exists
    counter = 1
    while os.path.exists(copy_to):
        # If it does, create a new file name with a counter
        new_file_name = f"{os.path.splitext(file_name)[0]}_{counter}{os.path.splitext(file_name)[1]}"
        copy_to = os.path.join(copy_dir, new_file_name)
        counter += 1
        print("New filename: " + copy_to)

    shutil.copy(source, copy_to)

copy_dir = 'D:\\temp\\copy'
work_dir = 'D:\\temp\\Google Фото'
suffixes = ('-измененный', '-', '(1)', '(2)', '(3)', '(4)', '2', '9', '4')
for root, dirs, files in os.walk(work_dir):
    for file in files:
        if file.endswith("json"):
            continue
        full_name = os.path.join(root, file)
        file_name, extension = os.path.splitext(full_name)

        names_to_test = [file_name + extension + '.json', file_name + '.json']
        for s in suffixes:
            if file_name.endswith(s):
                shortened = re.sub(re.escape(s) + '$', '', file_name)
                names_to_test.append(shortened + extension + '.json')
                names_to_test.append(shortened + '.json')
                names_to_test.append(shortened + extension + s + '.json')

        json_name = False
        for name in names_to_test:
            if os.path.isfile(name):
                json_name = name
                break

        if file.endswith('.MP') or file.endswith('.MP~2'):
            json_name = full_name + '.jpg.json'

        if not json_name:
            print("Skip no JSON: " + full_name)
            continue

        with open(json_name) as fp:
            data = json.load(fp)
            if not data['creationTime']['timestamp']:
                print("No timestamp: " + json_name)
            date = datetime.fromtimestamp(int(data['creationTime']['timestamp']))
            if date < datetime(2022, 12, 1) or date >= datetime(2023, 12, 10):
                # print('Skip cuz date outside: %s / %s' % (date, file))
                continue

        file_name = os.path.basename(full_name)
        copy_to = os.path.join(copy_dir, file_name)
        if not os.path.exists(copy_to):
            shutil.copy(full_name, copy_to)

