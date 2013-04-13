# script to process new downloads from devices

from datetime import datetime
from optparse import OptionParser
import os
import shutil
from hb_encoder import HbEncoder
from renamer import proper_name

parser = OptionParser()
(options, args) = parser.parse_args()
work_dir = args[0]
encoder = HbEncoder()
for root, dirs, files in os.walk(work_dir):
    for file in files:
        full_name = os.path.join(root, file)
        original_mtime = os.path.getmtime(full_name)
        create_time = datetime.fromtimestamp(original_mtime)
        rename_to = proper_name(full_name, create_time)
        if rename_to != full_name:
            shutil.move(full_name, rename_to)
            print("%s => %s" % (full_name, rename_to))
        full_name = rename_to

        # maybe encode
        (no_ext_name, ext) = os.path.splitext(os.path.split(full_name)[1])
        if ext.lower() == ".mod":
            new_name = os.path.join(root, no_ext_name + ".mp4")
            print("encoding to %s" % (new_name,))
            if encoder.encode(full_name, new_name) == 0:
                os.utime(new_name, (-1, original_mtime))
                os.remove(full_name)
                full_name = new_name
            else:
                print("ERROR!!! " + full_name)

