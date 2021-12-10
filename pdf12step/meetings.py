import json
import re
from collections import defaultdict
from urllib.parse import unquote

from pdf12step.adict import AttrDict
from pdf12step.cached import cached_property


DAYS = {
    0: 'Sunday',
    1: 'Monday',
    2: 'Tuesday',
    3: 'Wednesday',
    4: 'Thursday',
    5: 'Friday',
    6: 'Saturday',
    12: 'Other'
}
ZIP_RE = re.compile(r'(\d{5})')


def clean_url(url):
    """
    Cleans and unquotes a URL that might be poorly formatted

    :param str url: URL string to clean/unquote
    :rtype: str
    """
    if url.count('://') == 2:
        url = '://'.join(url.split('://')[:2])
    return unquote(url).strip()


class Meeting(AttrDict):

    @cached_property
    def day_display(self):
        """Gets the weekday name (eg Thursday)"""
        return DAYS.get(self.day, 'Other')

    @cached_property
    def zipcode(self):
        """
        Returns a 5 digit zipcode from the formatted address
        """
        addr = ' '.join(self.formatted_address.split()[1:])
        match = ZIP_RE.search(addr)
        return match.groups()[0] if match else ''

    @cached_property
    def conference_url(self):
        """
        Returns a cleaned conference_url
        """
        return clean_url(self['conference_url'])

    @cached_property
    def conference_id(self):
        """
        Returns the Zoom conference ID from the URL
        """
        if not self.conference_url:
            return ''
        return self.conference_url.split('/')[-1].split('?')[0]

    @cached_property
    def conference_id_formatted(self):
        """
        Returns a Zoom formatted conference ID. Eg 000 000 0000
        """
        if not self.conference_id:
            return ''
        zoom_id = self.conference_id
        idx = 7 if len(zoom_id) == 11 else 6
        return ' '.join([zoom_id[:3], zoom_id[3:idx], zoom_id[idx:]])

    @cached_property
    def notes_list(self):
        """
        Returns a list of notes
        """
        return [line.lstrip('-').strip() for line in self.notes.splitlines()]


class MeetingSet(object):
    def __init__(self, fn_or_obj):
        self.fn_or_obj = fn_or_obj

    @cached_property
    def items(self):
        itms = json.load(open(self.fn_or_obj)) if isinstance(self.fn_or_obj, str) else self.fn_or_obj
        return [Meeting(item, default='') for item in itms]

    def copy(self):
        return MeetingSet(self.items.copy())

    def __iter__(self):
        for item in self.items:
            yield item

    def __len__(self):
        return len(self.items)

    def __add__(self, other):
        return MeetingSet(self.items + other.items)

    def __getitem__(self, key):
        return self.items[key]

    def limit(self, num):
        """
        Limits the MeetingSet to num entries

        :param int num: Limit number
        :rtype: MeetingSet
        """
        return MeetingSet(self.items[:num])

    def value_set(self, attr, sort=False):
        """
        Returns a set of unique values for the passed atribute name

        :param str attr: Attribute name of a Meeting
        :rtype: set
        """
        vset = set()
        for item in self.items:
            value = item[attr]
            if isinstance(value, list):
                vset |= set(value)
            else:
                vset.add(value)
        return sorted(vset) if sort else vset

    def value_count(self, attr):
        """
        Returns a dict with the attribute's values and the number of occurances
        """
        counter = defaultdict(int)
        for item in self.items:
            counter[getattr(item, attr)] += 1
        return counter

    def by_value(self, attr, sort=False, limit=None):
        """
        Groups the results by the given attribute values.
        Returns a dict with the values as keys and filtered MeetingSet as values
        If sorted, it returns a sorted items list
        If limited, only returns up to X number of Meetings
        """
        result = defaultdict(list)
        count = 0
        for item in self.items:
            if limit and count >= limit:
                break
            count += 1
            result[getattr(item, attr)].append(item)
        if sort:
            return sorted([(key, MeetingSet(items)) for key, items in result.items()])
        return {key: MeetingSet(items) for key, items in result.items()}

    def filter(self, **kwargs):
        """
        Filter by all passed attribute value key pairs (AND filter)
        """
        query = kwargs.items()
        for item in self.items:
            if all([getattr(item, key) == val for key, val in query]):
                yield item

    def sort(self, *attrs, reverse=False):
        """
        Returns a new MeetingSet isinstance with the items ordered by the given attributes
        """
        def keyfunc(item):
            return [item[attr] for attr in attrs]
        return MeetingSet(sorted(self.items, key=keyfunc, reverse=reverse))

    @cached_property
    def by_id(self):
        return {meeting[0].id: meeting[0] for meeting in self.by_value('id')}

    @cached_property
    def zipcodes(self):
        return set([meeting.zipcode for meeting in self.items if meeting.zipcode])

    @cached_property
    def index(self):
        """
        Returns sorted list of meeting index section information
        Used to show which meetings meet in which zipcode and on which days
        """
        meets = {}
        for item in self.items:
            if item.zipcode:
                meets.setdefault(item.name, {'zip': item.zipcode, 'days': {}})
                meets[item.name]['days'][item.day] = item.id
        return sorted(meets.items(), key=lambda i: i[0])

    @cached_property
    def regions(self):
        """
        Returns a sorted list of regions and the zipcodes associated with them
        """
        region_set = defaultdict(set)
        for item in self.items:
            if item.zipcode:
                region_set[item.region] |= set([item.zipcode])
        return sorted(region_set.items(), key=lambda i: i[0])

    @cached_property
    def names(self):
        """
        Returns a value_set of names
        """
        return self.value_set('name')

    @cached_property
    def types(self):
        """
        Returns a value_set of types
        """
        return self.value_set('types')
