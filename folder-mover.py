__author__ = 'looser'
from optparse import OptionParser
import os
import shutil
import re

# Moves YYYMMDD folders into year subfolders
# example args: "D:\Pictures"
# will move /2012.01.01 to /2012/01.01

parser = OptionParser()

(_, args) = parser.parse_args()

target = args[0]

for file in os.listdir(target):
    match = re.match("^(\d{4})\.", file)
    src = os.path.join(target, file)
    if match and os.path.isdir(src):
        year = match.group(1)
        year_dir = os.path.join(target, year)
        dst = os.path.join(year_dir, file.replace(year + ".", ""))
        print("{0} => {1}".format(src, dst))
        os.makedirs(year_dir, exist_ok=True)
        shutil.move(src, dst)






