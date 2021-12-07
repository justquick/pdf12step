from unittest import mock
from os import environ

from .base import ENV, CONFIG_FILE, DATA_DIR, contains_parts


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
def test_codify():
    from pdf12step.templating import Context, codify
    ctx = Context({
        'data_dir': DATA_DIR,
        'config': [CONFIG_FILE],
        'template_dirs': [DATA_DIR],
        'title': 'My Test Title',
        'mycodes': ['A', 'B', 'C'],
    })
    coded = codify(ctx.config.codemap, ctx.config.filtercodes)(['C', 'B'])
    assert list(coded) == ['BB']


@mock.patch.dict(environ, ENV, clear=True)
def test_link():
    from pdf12step.templating import link
    url, name, gid = 'http://google.com', 'Google', 'goo'
    assert link(True)(url, name, gid) == f'<a id="{gid}" href="{url}">{name}</a>'
    assert link(False)(url, name, gid) == name


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
    contains_parts(ctx.render('test.txt'), [
        'my-test-title',
        DATA_DIR,
        'A BB',
        'Test Author Intergroup'
    ])


@mock.patch.dict(environ, ENV, clear=True)
def test_pdftemplate():
    from pdf12step.templating import Context
    ctx = Context({
        'data_dir': DATA_DIR,
        'config': [CONFIG_FILE],
    })
    contains_parts(ctx.render('layout.html'), [
        'Tuesday - Parkton',
        '<link href="assets/css/style.css" rel="stylesheet">',
        '39.2912855,-76.5629126">100 S Haven St, Baltimore, MD 21224, USA',
        '<meta name="author" content="Test Author Intergroup" />',
        'D O ONL',
        '<a href="https://zoom.us/j/1234189178">Join on Zoom</a>'
    ])


@mock.patch.dict(environ, ENV, clear=True)
def test_methods():
    from pdf12step.templating import Context
    ctx = Context({
        'data_dir': DATA_DIR,
        'config': [CONFIG_FILE],
    })
    assert ctx.stylesheets == ['assets/css/style.css', 'test/css']
    assert len(ctx.template_dirs) == 2
    assert ctx.template_dirs[1] == 'test/templates'
