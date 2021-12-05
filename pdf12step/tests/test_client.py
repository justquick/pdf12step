from unittest import mock
from json import load
from os import path


DATA_DIR = path.join(path.dirname(__file__), 'data')


class MockedResponse:
    content = b':null,\n"nonce":"1622995ce5","pr'
    status_code = 200
    elapsed = 0
    headers = {
        'Content-Type': 'text/plain'
    }

    def json(self):
        return load(open(path.join(DATA_DIR, 'meetings.json')))

    def raise_for_status(self):
        pass


@mock.patch('requests.post')
@mock.patch('requests.get')
def test_cilent(mocked_get, mocked_post):
    mocked_post.return_value = mocked_get.return_value = MockedResponse()
    from pdf12step.client import Client

    client = Client('http://fakewordpress-site.us')
    meetings = client.meetings()
    assert len(meetings) == 12

    args, kwargs = mocked_get.call_args
    assert args[0] == 'http://fakewordpress-site.us/meetings/'
    assert len(kwargs) == 0

    args = mocked_post.call_args[0]
    assert args[0] == 'http://fakewordpress-site.us/wordpress/wp-admin/admin-ajax.php'
    assert args[1] == {
        'mode': 'search',
        'distance': 2,
        'view': 'list',
        'distance_units': 'm',
        'nonce': '1622995ce5',
        'action': 'meetings'
    }
