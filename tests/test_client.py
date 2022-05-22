from unittest import mock
from json import load
from os import environ


from .base import ENV, DATA_DIR, MEETINGS_FILE


class MockedResponse:
    content = b':null,\n"nonce":"1622995ce5","pr'
    status_code = 200
    elapsed = 0
    headers = {
        'Content-Type': 'text/plain'
    }

    def json(self):
        return load(open(MEETINGS_FILE))

    def raise_for_status(self):
        pass


@mock.patch('requests.post')
@mock.patch('requests.get')
@mock.patch('pdf12step.client.json_dump')
@mock.patch.dict(environ, ENV, clear=True)
def test_cilent(mocked_dump, mocked_get, mocked_post):
    mocked_post.return_value = mocked_get.return_value = MockedResponse()
    from pdf12step.client import Client

    client = Client('http://fakewordpress-site.us', 'api', 'nonce')
    meetings = client.meetings()
    assert len(meetings) == 12

    args, kwargs = mocked_get.call_args
    assert args[0] == 'http://fakewordpress-site.us/api'
    assert 'headers' in kwargs

    client.download()
    calls = mocked_dump.call_args_list
    assert len(calls) == len(Client.sections)
    meeting = calls[0][0][0][0]
    assert meeting['id'] == 319513
    assert meeting['name'] == 'Columbia Dawn Patrol'

    filenames = [f'{section}.json' for section in Client.sections]
    for i, call in enumerate(calls):
        fname = call[0][-1]
        assert fname.endswith(filenames[i])
