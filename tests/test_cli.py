from unittest import mock


@mock.patch('builtins.input')
def test_prompt(mocked_input):
    from pdf12step.cli import prompt

    assert prompt('test', 'this is a test field', default='nope', cast=bool) == {'test': True}
