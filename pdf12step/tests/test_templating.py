from unittest import mock
from os import environ

from .base import ENV, CONFIG_FILE, DATA_DIR


@mock.patch.dict(environ, ENV, clear=True)
def test_slugify():
    from pdf12step.templating import slugify
    for text, slug in (
        ('concurrently.\n-Zoom Mee', 'concurrently-zoom-mee'),
        ('23,,5131', '235131'),
        ('A@#$@^%__---Z', 'a__-z'),
    ):
        assert slugify(text) == slug


@mock.patch.dict(environ, ENV, clear=True)
def test_template():
    from pdf12step.templating import Context
    ctx = Context({
        'data_dir': DATA_DIR,
        'config': [CONFIG_FILE],
        'template_dirs': [DATA_DIR],
        'title': 'My Test Title',
        'mycodes': ['A', 'B', 'C'],
    })
    content = ctx.render('test.txt')
    for part in [
        'my-test-title',
        DATA_DIR,
        'A BB',
        'Test Author Intergroup'
    ]:
        assert part in content


@mock.patch.dict(environ, ENV, clear=True)
def test_pdftemplate():
    from pdf12step.templating import Context
    ctx = Context({
        'data_dir': DATA_DIR,
        'config': [CONFIG_FILE],
    })
    content = ctx.render('layout.html')
