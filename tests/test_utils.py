from unittest import mock


def test_week():
    from pdf12step.utils import Week

    print(0)
    w1 = Week()
    for d in w1:  # .days:
        print(d)

    print(3)
    w1 = Week(3)
    for d in w1:  # .days:
        print(d)


@mock.patch('builtins.input')
def test_utils(mocked_input):
    from pdf12step.utils import booler, lister

    assert booler('YES') == 'true'
    assert booler('nope') == 'false'

    assert lister(None) == []
    assert lister('a,b,c') == ['a', 'b', 'c']
