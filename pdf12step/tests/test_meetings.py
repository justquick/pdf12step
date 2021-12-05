from os import path
from unittest import TestCase

from pdf12step.meetings import MeetingSet, Meeting


class MeetingTest(TestCase):
    def item(self, **kwargs):
        return Meeting(str, kwargs)

    def test_day_display(self):
        assert self.item(day=4).day_display == 'Thursday'
        assert self.item(day=40).day_display == 'Other'

    def test_region(self):
        assert not self.item().region
        assert self.item(region='foo').region == 'foo'

    def test_zipcode(self):
        assert self.item().zipcode == ''
        assert self.item(formatted_address='123 fake st, springfield KS 88888').zipcode == '88888'

    def test_conference_id(self):
        assert self.item().conference_id == ''
        for url, cid in (
            ('https://z.us/j/85755551465', '857 5555 1465'),
            ('https://z.us/j/123555137', '123 555 137'),
            ('https://z.us/j/85755551465?foo=bar', '857 5555 1465'),
            ('https://us02web.zoom.us/j/2335558121\xa0', '233 555 8121'),
            ('https://us02web.zoom.us/j/85955555990%20', '859 5555 5990'),
            ('https://us04web.zoom.us/j/943555671://us04web.zoom.us/j/943555671', '943 555 671'),
        ):
            assert self.item(conference_url=url).conference_id_formatted == cid


class MeetingSetTest(TestCase):

    def setUp(self):
        self.meetings = MeetingSet(path.join(path.dirname(__file__), 'data', 'meetings.json'))
        self.attendance_options = {'hybrid', 'online', 'in_person'}

    def test_copy(self):
        assert self.meetings.items == self.meetings.copy().items

    def test_magic(self):
        assert len(self.meetings) == len(self.meetings.items)
        assert len(self.meetings + self.meetings) == 24

    def test_values_set(self):
        assert self.meetings.value_set('types') == {'TC', 'D', 'ONL', 'O'}
        assert self.meetings.value_set('attendance_option') == self.attendance_options
        locations = self.meetings.value_set('location', 'latitude', 'longitude')
        assert isinstance(locations, set)
        assert len(locations) == len(self.meetings) - 1

    def test_value_count(self):
        assert self.meetings.value_count('location')[''] == 2
        ids = self.meetings.value_count('id')
        assert len(ids) == len(self.meetings)
        assert set(ids.values()) == {1}

    def test_by_values(self):
        assert len(self.meetings.by_value('id', limit=3)) == 3

        options = self.meetings.by_value('attendance_option')
        assert set(options) == self.attendance_options
        assert all([isinstance(meets, MeetingSet) for meets in options.values()])

        online_locations = options['online'].by_value('location', sort=True)
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
        assert len(self.meetings.index) == 10
        assert isinstance(self.meetings.index, list)
        assert len(self.meetings.index[0]) == len(self.meetings.index[0][1]) == 2

    def test_regions(self):
        assert len(self.meetings.regions) == 10
        names = [meet[0] for meet in self.meetings.regions]
        assert sorted(names) == names
        assert len(self.meetings.regions[0][1].pop()) == 5

    def test_sort(self):
        sort_ids = [m.id for m in self.meetings.sort('id')]
        assert sort_ids != [m.id for m in self.meetings]
        prev = 0
        for mid in sort_ids:
            assert prev < mid
            prev = mid
