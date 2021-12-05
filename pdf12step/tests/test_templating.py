from os import path

from pdf12step.templating import slugify, Context

DATA_DIR = path.join(path.dirname(__file__), 'data')
CONFIG_FILE = path.join(DATA_DIR, 'test.config.yml')


def test_slugify():
    for text, slug in (
        ('concurrently.\n-Zoom Mee', 'concurrently-zoom-mee'),
        ('23,,5131', '235131'),
        ('A@#$@^%__---Z', 'a__-z'),
    ):
        assert slugify(text) == slug


def test_template():
    ctx = Context({
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


def test_pdftemplate():
    ctx = Context({
        'config': [CONFIG_FILE],
    })
    content = ctx.render('layout.html')
