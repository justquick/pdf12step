import re
import os
import json
import calendar
from csv import DictWriter
from itertools import islice, cycle

from markupsafe import Markup
from qrcode import QRCode
from yaml import safe_load

from pdf12step.adict import AttrDict


class Week(dict):
    def __init__(self, start=0):
        self.start = start
        self._days = list(calendar.day_name)
        self._days.insert(0, self._days.pop())  # for TSML Sunday is first (0)
        self.update(enumerate(self._days))

    def __iter__(self):
        start, stop = self.start, self.start + len(self)
        return islice(cycle(sorted(self.items())), start, stop)

    def __len__(self):
        return 7


def yaml_load(filename_or_string):
    """
    Returns the config dict loaded from the given filename

    :param str filename: YAML filename to load
    :rtype: dict
    """
    if os.path.isfile(filename_or_string):
        filename_or_string = open(filename_or_string).read()
    return safe_load(filename_or_string)


def csv_dump(data, outfile):
    """
    Dumps csv data to a file with default Nones and AttrDefaults to handle missing fields

    :param list data: List of row data to dump
    :param file outfile: File instance to write to
    """
    keys = set()
    [keys.update(item.keys()) for item in data]
    if 'id' in keys:
        keys = ['id'] + list(keys.difference({'id'}))
    with open(outfile, 'w') as csvfile:
        writer = DictWriter(csvfile, keys,  extrasaction='ignore')
        writer.writeheader()
        writer.writerows([AttrDict({key: '|'.join(map(str, value)) if isinstance(value, list) else value
                                    for key, value in item.items()})
                          for item in data])


def json_dump(data, outfile):
    """
    Dumps list/dict data to outfile with indent for readability
    """
    with open(outfile, 'w') as jsonfile:
        json.dump(data, jsonfile, indent=2)


def qrcode(data, dest, **kwargs):
    """
    Creates a QRCode of the given data written as a PNG to the dest filename
    Returns the PIL image instance
    """
    qr = QRCode(box_size=kwargs.pop('box_size', 5))
    qr.add_data(data, kwargs.pop('optimize', 20))
    qr.make(fit=True)
    img = qr.make_image(**kwargs)
    os.makedirs(os.path.dirname(dest), exist_ok=True)
    img.save(dest)
    return img


def slugify(value):
    """
    Turns str into slug value

    :param str value: Regular string to slugify
    """
    value = re.sub(r'[^\w\s-]', '', value.lower()).strip()
    return re.sub(r'[-\s]+', '-', value)


def codify(codemap, filtercodes):
    """
    Filters codes list in values to renamed/ignored list of codes

    :param dict codemap: Mapping of codes to names to use in display
    :param list filtercodes: List of codes to ignore
    """
    def inner(values):
        codes = [str(codemap.get(code, code))
                 for code in values if filtercodes and code and code not in filtercodes]
        return filter(lambda c: len(c), codes)
    return inner


def link(show):
    """
    Displays an <a> tag for the given url and name
    If show (config.show_links) is False, just returns name

    :param bool show: True if to display <a> tags
    """
    def inner(url, name, id=None):
        if show:
            id = f' id="{id}"' if id is not None else ''
            return Markup(f'<a{id} href="{url}">{name}</a>')
        return name
    return inner


def show(hide):
    """
    Returns True if the Meeting attribute should be shown (not in config.hide)
    """
    def inner(meeting, attr):
        return attr not in hide and getattr(meeting, attr)
    return inner


def lister(value):
    """
    Returns a (comma separated) string value as a list
    """
    return value.split(',') if value else []


def booler(value):
    """
    Returns a string value as a bool (eg yes, True)
    """
    if isinstance(value, str):
        value = value.lower() in ('y', 'yes', 'true')
    return str(value).lower()
