from unittest import TestCase

from pdf12step.meetings import MeetingSet, Meeting, Calendar

from .base import MEETINGS_FILE


def item(**kwargs):
    return Meeting(kwargs, default='')


def test_cal():
    cal = Calendar(3)
    week = list(cal)
    assert len(week) == 7
    assert week[0] == (3, 'Wednesday')
    assert week[-1] == (2, 'Tuesday')


def test_day_display():
    assert item(day=4).day_display == 'Thursday'
    assert item(day=40).day_display == 'Other'


def test_region():
    assert not item().region
    assert item(region='foo').region == 'foo'


def test_zipcode():
    assert item().zipcode == ''
    assert item(formatted_address='123 fake st, springfield KS 88888').zipcode == '88888'


def test_conference_id():
    assert item().conference_id == ''
    for url, cid in (
        ('https://zoom.us/j/85755551465', '857 5555 1465'),
        ('https://zoom.us/j/123555137', '123 555 137'),
        ('https://zoom.us/j/85755551465?foo=bar', '857 5555 1465'),
        ('https://us02web.zoom.us/j/2335558121\xa0', '233 555 8121'),
        ('https://us02web.zoom.us/j/85955555990%20', '859 5555 5990'),
        ('https://us04web.zoom.us/j/943555671://us04web.zoom.us/j/943555671', '943 555 671'),
    ):
        zitem = item(conference_url=url)
        assert zitem.conference_type == 'zoom'
        assert zitem.conference_id_formatted == cid


class MeetingSetTest(TestCase):

    def setUp(self):
        self.meetings = MeetingSet(MEETINGS_FILE)
        self.attendance_options = {'hybrid', 'online', 'in_person'}

    def test_copy(self):
        assert self.meetings.items == self.meetings.copy().items

    def test_magic(self):
        assert len(self.meetings) == len(self.meetings.items)
        assert len(self.meetings + self.meetings) == 24

    def test_values_set(self):
        assert self.meetings.value_set('attendance_option') == self.attendance_options
        test_types = {'Y', 'LIT', 'O', 'D', 'X', 'TC', 'M', 'CF', 'HYB', 'ONL', 'B'}
        assert set(self.meetings.types) == self.meetings.value_set('types') == test_types
        assert self.meetings.value_set('types', True) == sorted(test_types)

    def test_value_count(self):
        assert self.meetings.value_count('location')[''] == 2
        ids = self.meetings.value_count('id')
        assert len(ids) == len(self.meetings)
        assert set(ids.values()) == {1}

    def test_by_values(self):
        assert len(self.meetings.by_value('id', limit=3)) == 3

        options = self.meetings.by_value('attendance_option')
        assert set([i[0] for i in options]) == self.attendance_options
        assert all([isinstance(i[1], MeetingSet) for i in options])

        online_locations = dict(options)['online'].by_value('location')
        assert isinstance(online_locations, list)
        assert isinstance(online_locations[0], tuple)
        assert online_locations[0][0] == ''

    def test_filter(self):
        in_person = tuple(self.meetings.filter(attendance_option='in_person', time='19:00'))
        assert len(in_person) == 3
        for meeting in in_person:
            assert meeting.attendance_option == 'in_person'
            assert meeting.time == '19:00'

    def test_index(self):
        assert len(self.meetings.index) == 12
        assert isinstance(self.meetings.index, list)
        assert len(self.meetings.index[0]) == 2
        assert len(self.meetings.index[0][1]) == 3

    def test_regions(self):
        assert len(self.meetings.regions) == 11
        names = [meet[0] for meet in self.meetings.regions]
        assert sorted(names) == names
        assert len(self.meetings.regions[1][1]) == 1

    def test_sort(self):
        sort_ids = [m.id for m in self.meetings.sort('id')]
        assert sort_ids != [m.id for m in self.meetings]
        prev = 0
        for mid in sort_ids:
            assert prev < mid
            prev = mid
