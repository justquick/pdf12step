from unittest import mock


@mock.patch('builtins.input')
def test_utils(mocked_input):
    from pdf12step.main import booler, lister, prompt

    assert booler('YES') == 'true'
    assert booler('nope') == 'false'

    assert lister(None) == []
    assert lister('a,b,c') == ['a', 'b', 'c']

    assert prompt('test', 'this is a test field', default='nope', cast=bool) == {'test': True}
