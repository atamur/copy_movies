from optparse import OptionParser
import os
import shutil
import re

# extracts files by extension and copies away keeping dir structure (with yyyymmdd prefix)
# example args: -e "mod,avi,mp4,mov,3gp,m4v,asf" "D:\Pictures" "D:\vid"

parser = OptionParser()
parser.add_option("-e", "--extensions", dest="extensions")

(options, args) = parser.parse_args()

extensions = ["." + x for x in options.extensions.split(",")]
print (extensions)
source = args[0]
destination = args[1]

def find_date_folder(path):
    if not path.startswith(source):
        return None
    (parent, folder) = os.path.split(path)
    if re.match("\d{4}", folder):
        return folder
    return find_date_folder(parent)

for root, dirs, files in os.walk(source):
    for file in files:
        (unused, ext) = os.path.splitext(file)
        if ext.lower() in extensions:
            folder = find_date_folder(root)
            src = os.path.join(root, file)
            if folder is None: dst = os.path.join(destination, "misc")
            else: dst = os.path.join(destination, folder)
            os.makedirs(dst, exist_ok=True)
            shutil.move(src, dst)
            print("{0} => {1}".format(src, dst))






