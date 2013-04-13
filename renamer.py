import os
import re


def apply_timestamp_convention(name, timestamp):
    return  timestamp.strftime("%Y.%m.%d_%H-%M-%S") + "_" + name


def proper_name(file, timestamp, fix_hex = True):
    """ Finds  proper name based on given timestamp. """
    (folder, full_name) = os.path.split(file)
    (name, ext) = os.path.splitext(full_name)

    # first pull the date out
    # try to find embedded date
    existing_date = re.search("[-._ ]?(?P<Y>\d{4})[-._ ]?(?P<m>\d{2})[-._ ]?(?P<d>\d{2})[-._ ]?(?P<H>\d{2})[-._ ]?(?P<M>\d{2})[-._ ]?(?P<S>\d{2})[-._ ]?", name)
    if existing_date:
        name = name.replace(existing_date.group(0), "").__str__()

        # check there's no dup date
        dup_match = re.search("[-._ ]?\d\d\d\d\.\d\d\.\d\d$", name)
        if dup_match:
            name = name.replace(dup_match.group(0), "")

        name = "_{0}".format(name) if name else ""
        name = "%s.%s.%s_%s-%s-%s%s" % (
            existing_date.group("Y"),
            existing_date.group("m"),
            existing_date.group("d"),
            existing_date.group("H"),
            existing_date.group("M"),
            existing_date.group("S"),
            name
        )
    else:
        date_match = re.search("\d\d\d\d\.\d\d\.\d\d[_ ]", name)
        if not date_match:
            name = apply_timestamp_convention(name, timestamp)
        elif not re.match("\d\d\d\d\.\d\d\.\d\d_\d\d-\d\d-\d\d", name):
            name = name.replace(date_match.group(0), "")
            name = apply_timestamp_convention(name, timestamp)

    if fix_hex:
        # now unwrap hex number from JVC
        match = re.search("MOV([0-9A-F]{3})", name)
        if match:
            number = int(match.group(1), 16)
            name = name.replace(match.group(0), "MOV" + ("%03d" % (number,)))

    return os.path.join(folder, name + ext)


