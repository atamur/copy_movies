import os
import re


def apply_timestamp_convention(name, timestamp):
    return  timestamp.strftime("%Y.%m.%d_%H-%M-%S") + "_" + name


def proper_name(file, timestamp):
    """ Finds  proper name based on given timestamp. """
    (folder, full_name) = os.path.split(file)
    (name, ext) = os.path.splitext(full_name)

    # first pull the date out
    date_match = re.search("\d\d\d\d\.\d\d\.\d\d[_ ]", name)
    if not date_match:
        name = apply_timestamp_convention(name, timestamp)
    elif not re.match("\d\d\d\d\.\d\d\.\d\d_\d\d-\d\d-\d\d", name):
        name = name.replace(date_match.group(0), "")
        name = apply_timestamp_convention(name, timestamp)


    # now unwrap hex number from JVC
    match = re.search("MOV([0-9A-F]{3})", name)
    if match:
        number = int(match.group(1), 16)
        name = name.replace(match.group(0), "MOV" + ("%03d" % (number,)))

    return os.path.join(folder, name + ext)


