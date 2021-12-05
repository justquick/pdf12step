from pdf12step.templating import slugify, codify, link


def test_slugify():
    for text, slug in (
        ('concurrently.\n-Zoom Mee', 'concurrently-zoom-mee'),
        ('23,,5131', '235131'),
        ('A@#$@^%__---Z', 'a__-z'),
    ):
        assert slugify(text) == slug
