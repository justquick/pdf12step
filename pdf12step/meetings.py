import json
import re
from datetime import datetime
from collections import defaultdict
from urllib.parse import unquote, urlparse

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
US_ZIP_RE = re.compile(r'(\d{5})')
CA_ZIP_RE = re.compile(r'([ABCEGHJ-NPRSTVXY]\d[ABCEGHJ-NPRSTV-Z][ -]?\d[ABCEGHJ-NPRSTV-Z]\d)', re.I)


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
    def id_display(self):
        """
        Gets a unique ID of the meeting either from the id or slug field or python generated
        """
        if self.id:
            return self.id
        if self.slug:
            return self.slug
        return id(self)

    @cached_property
    def day_display(self):
        """Gets the weekday name (eg Thursday)"""
        return DAYS.get(self.day, 'Other')

    @cached_property
    def address_display(self):
        """
        Displays a long form address line
        """
        if self.formatted_address:
            return self.formatted_address
        return f'{self.address}, {self.city} {self.state}, {self.zipcode}'

    @cached_property
    def zipcode(self):
        """
        Returns a 5 digit zipcode from the formatted address
        """
        if self.postal_code:
            return self.postal_code
        addr = ' '.join(self.formatted_address.split()[1:])
        zipre = CA_ZIP_RE if '.ca/' in self.url else US_ZIP_RE
        match = zipre.search(addr)
        return match.groups()[0] if match else ''

    @cached_property
    def time_display(self):
        """
        Returns the formatted time of day in H:M AM/PM
        """
        if self.time_formatted:
            return self.time_formatted.upper()
        if self.time:
            dt = datetime.strptime(self.time, '%H:%M')
            return dt.strftime('%I:%M %p').strip('0')

    @cached_property
    def conference_url(self):
        """
        Returns a cleaned conference_url
        """
        return clean_url(self['conference_url'])

    @cached_property
    def conference_id(self):
        """
        Returns the conference ID from the URL usually used for zoom
        """
        if not self.conference_url:
            return ''
        confid = self.conference_url.split('/')[-1]
        if self.conference_type == 'zoom':
            return confid.split('?')[0]
        return confid

    @cached_property
    def conference_id_formatted(self):
        """
        Returns a formatted conference ID. Eg 000 000 0000 for zoom
        """
        if not self.conference_id:
            return ''
        if self.conference_type == 'zoom':
            zoom_id = self.conference_id
            idx = 7 if len(zoom_id) == 11 else 6
            return ' '.join([zoom_id[:3], zoom_id[3:idx], zoom_id[idx:]])
        return self.conference_id

    @cached_property
    def conference_notes_display(self):
        """
        Gets the text of the conference notes
        """
        if self.conference_notes:
            return self.conference_notes
        return self.conference_url_notes

    @cached_property
    def conference_type(self):
        """
        Returns the type of conference URL by domain name (zoom/gotomeet/google)
        Returns domain if nothing matches
        """
        if not self.conference_url:
            return
        domain = urlparse(self.conference_url).netloc.lower()
        if domain.endswith('zoom.us'):
            return 'zoom'
        elif 'gotomeet' in domain:
            return 'gotomeet'
        elif domain.endswith('google.com'):
            return 'google'
        return domain

    @cached_property
    def notes_list(self):
        """
        Returns a list of notes
        """
        return [line.lstrip('-').strip() for line in self.notes.splitlines() if line.lstrip('-').strip()]

    @cached_property
    def region_display(self):
        """
        Gets the text of the region and sub_region
        """
        if self.region:
            return f'{self.region}/{self.sub_region}' if self.sub_region else self.region
        elif self.regions:
            return '/'.join(self.regions)

    @cached_property
    def latlon(self):
        """
        Returns the latitude,longitude tuple for usage in map locations
        """
        return f'{self.latitude},{self.longitude}'

    @cached_property
    def is_conference(self):
        """
        Returns True if the attendance_option is either online or hybrid.
        Failing having that value, determines whether a conference_url is set
        """
        if self.attendance_option:
            return self.attendance_option in ('online', 'hybrid')
        return bool(self.conference_url)

    @cached_property
    def attendance_option(self):
        if 'attendance_option' in self:
            return self['attendance_option']
        if 'ONL' in self.types:
            return 'online'
        if 'HY' in self.types or 'HYB' in self.types:
            return 'hybrid'
        return 'in_person'


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

    def value_set(self, attr, sort=False, filter_none=False):
        """
        Returns a set of unique values for the passed atribute name

        :param str attr: Attribute name of a Meeting
        :rtype: set
        """
        vset = set()
        for item in self.items:
            value = item[attr] if attr in item else getattr(item, attr)
            if filter_none and not value:
                continue
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

    def by_value(self, attr, sort=False, limit=None, cast=str, reverse=False):
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
            key = getattr(item, attr)
            if isinstance(key, list):
                for value in key:
                    result[value].append(item)
            else:
                result[key].append(item)
        if sort:
            return sorted([(cast(key), MeetingSet(items)) for key, items in result.items()], reverse=reverse)
        return {key: MeetingSet(items) for key, items in result.items()}

    def filter(self, **kwargs):
        """
        Filter by all passed attribute value key pairs (AND filter)
        """
        query = kwargs.items()
        for item in self.items:
            for key, val in query:
                attr = getattr(item, key)
                if isinstance(val, list) and attr in val:
                    yield item
                elif attr == val:
                    yield item

    def filter_types(self, types):
        """
        Filter by passed list of types to ignore
        """
        for item in self.items:
            if any([type in item.types for type in types]):
                continue
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
        """
        Returns a dictionary mapping between the Meeting's ID and the Meeting object itself
        """
        return {meeting[0].id: meeting[0] for meeting in self.by_value('id')}

    @cached_property
    def index(self):
        """
        Returns sorted list of meeting index section information
        Used to show which meetings meet in which zipcode and on which days
        """
        meets = {}
        for item in self.items:
            if item.zipcode:
                meets.setdefault(item.name, {'zip': item.zipcode, 'region': item.region_display, 'days': {}})
                meets[item.name]['days'][item.day] = item.id_display
        return sorted(meets.items(), key=lambda i: i[0])

    @cached_property
    def regions(self):
        """
        Returns a sorted list of regions and the zipcodes associated with them
        """
        region_set = defaultdict(set)
        for item in self.items:
            region_set[item.region_display] |= set([item.zipcode] if item.zipcode else [])
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
        return [str(typ) for typ in self.value_set('types')]

    @cached_property
    def zipcodes(self):
        """
        Returns a set of all zipcodes for meetings in the MeetingSet
        """
        return self.value_set('zipcode', filter_none=True)
