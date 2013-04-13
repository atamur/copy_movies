from datetime import datetime
import os
from renamer import proper_name
import shutil
import sys

# Copies back metadata from backup

backup = sys.argv[1]
target = sys.argv[2]

for root, dirs, files in os.walk(backup):
    for file in files:
        (no_ext_name, ext) = os.path.splitext(file)
        new_name = no_ext_name + ".mp4"
        relative_dir = root[(len(backup) + 1):]
        full_new_name = os.path.join(target, os.path.join(relative_dir, new_name))
        if not os.path.exists(full_new_name):
            print("ERROR %s" % (full_new_name,))
            continue
        create_time = datetime.fromtimestamp(os.path.getmtime(os.path.join(root, file)))
        rename_to = proper_name(full_new_name, create_time)
        if rename_to != full_new_name:
            shutil.move(full_new_name, rename_to)
            print("%s => %s" % (full_new_name, rename_to))


