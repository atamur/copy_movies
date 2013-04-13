from datetime import datetime
import os
import re
from renamer import proper_name
import shutil
import sys

# Copies back metadata from backup

target = sys.argv[1]

for root, dirs, files in os.walk(target):
    for file in files:
        if re.match(".*((Makhm|Family) video|2007\.07 London)", root) or re.match("Thumbs", file):
            continue
        (unused, ext) = os.path.splitext(file)
        if not (ext.lower()[1:] in ["mod","avi","mp4","mov","3gp","m4v","asf"]):
            continue
        full_name = os.path.join(root, file)
        create_time = datetime.fromtimestamp(os.path.getmtime(full_name))
        rename_to = proper_name(full_name, create_time, False)
        if rename_to != full_name:
            shutil.move(full_name, rename_to)
            print("%s => %s" % (full_name, rename_to))


