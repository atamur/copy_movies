import os
import shutil
import sys

from hb_encoder import HbEncoder

# Encodes the MOD files from my video dir:
# 1) encode to a temp folder
# 2) move original to backup
# 3) copy encoded back to original location

source = sys.argv[1]
destination = sys.argv[2]
backup = sys.argv[3]

encoder = HbEncoder()
for root, dirs, files in os.walk(source):
    for file in files:
        (no_ext_name, ext) = os.path.splitext(file)
        if ext.lower() == ".mod":
            relative_dir = root[(len(source) + 1):]
            src = os.path.join(root, file)
            print("Processing {0}".format(src))

            processed_dst = os.path.join(destination, relative_dir)
            backup_dst = os.path.join(backup, relative_dir)
            processed_file = os.path.join(processed_dst, no_ext_name + ".mp4")

            os.makedirs(processed_dst, exist_ok=True)
            os.makedirs(backup_dst, exist_ok=True)

            if encoder.encode(src, processed_file) != 0:
                print("NOT ENCODED!!!")
                continue

            shutil.copy2(src, backup_dst)
            os.remove(src)
            shutil.copy2(processed_file, root)
