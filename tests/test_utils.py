from unittest import mock

@mock.patch('builtins.input')
def test_utils(mocked_input):
    from pdf12step.utils import booler, lister

    assert booler('YES') == 'true'
    assert booler('nope') == 'false'

    assert lister(None) == []
    assert lister('a,b,c') == ['a', 'b', 'c']
