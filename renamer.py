import os
import re


def proper_name(file, timestamp):
    """ Finds  proper name based on given timestamp. """
    (folder, full_name) = os.path.split(file)
    (name, ext) = os.path.splitext(full_name)
    # first put the date out
    if not re.match("\d\d\d\d\.\d\d\.\d\d", name):
        name = timestamp.strftime("%Y.%m.%d_%H-%M-%S") + "_" + name

    # now unwrap hex number from JVC
    match = re.search("MOV([0-9A-F]{3})", name)
    if match:
        number = int(match.group(1), 16)
        name = name.replace(match.group(0), "MOV" + ("%04d" % (number,)))

    return os.path.join(folder, name + ext)


