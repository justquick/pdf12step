import os
import json
import sys
import hashlib
import subprocess
from datetime import datetime, timezone
try:
    from flask import Flask
except ModuleNotFoundError:
    print('You must install Flask to use the pdf12step Flask app')
    exit(1)

from flask import render_template, request, Response
from flask import send_from_directory
from flask_weasyprint import HTML as FHTML, render_pdf
from yaml.parser import ParserError
from yaml.scanner import ScannerError

from pdf12step.templating import Context, FSBC, LAYOUT_TEMPLATE
from pdf12step.config import BASE_DIR
from pdf12step.utils import yaml_load


app = Flask(__name__, static_folder=os.path.join(BASE_DIR, 'assets'))
app.jinja_env.bytecode_cache = FSBC


def validate_config_yaml(stream):
    try:
        yaml_load(stream)
    except (ParserError, ScannerError) as exc:
        return json.dumps({
            'context': exc.context,
            'context_mark': exc.context_mark.line,
            'problem': exc.problem,
            'problem_mark': exc.problem_mark.line,
        }).replace('"', '\\"')


def liveproc(args):
    yield f'{" ".join(map(str, args))}\n'
    proc = subprocess.Popen(args, stdout=subprocess.PIPE, bufsize=1)
    while True:
        line = proc.stdout.readline()
        if not line:
            break
        yield line


def hashfunc(s):
    return hashlib.md5(s.encode()).hexdigest()


def loadcontext():
    """
    Loads the Context instance from runtime Flask request parameters as args to Context config

    :rtype: Context
    """
    args = dict(request.args)
    args['flask'] = True
    return app.config.setdefault('context', Context(args))


@app.route('/meetings.pdf')
def viewpdf():
    """
    View to render live PDF view. Takes a while to run but produces live PDF
    """
    loadcontext().prerender()
    html = render_template(LAYOUT_TEMPLATE, **app.config['context'])
    return render_pdf(FHTML(string=html), stylesheets=app.config['context']['config']['stylesheets'])


@app.route('/meetings.html')
def viewhtml():
    """
    View to render live HTML. Doesnt have the page/header formatting like the PDF but renders faster.
    """
    loadcontext().prerender()
    return render_template(LAYOUT_TEMPLATE, **app.config['context'])


@app.route('/make/pdf', methods=['GET', 'POST'])
def makepdf():
    errors = {}
    if request.method == 'POST':
        hashmap = {str(hashfunc(name)): name for name in app.pdfconfig.config}
        args = [sys.executable, '-m', 'pdf12step', '-v', '--logfile', '-']
        for name, lst in request.form.lists():
            if name.startswith('configs'):
                for hsh in lst:
                    args.extend(['-c', hashmap[hsh]])
        args.append('pdf')
        if 'download' in request.form and request.form['download'] == 'true':
            args.append('-d')
        if 'output' in request.form and request.form['output']:
            args.extend(['-o', request.form['output']])
        return Response(liveproc(args))
    return render_template('flask/pdf.html', hash=hashfunc, errors=errors, app_config=app.pdfconfig, config=app.pdfconfig.config)


@app.route('/edit', methods=['GET', 'POST'])
def edit():
    context = {'hash': hashfunc, 'errors': {}, 'success': []}
    context['config'] = config = {name: open(name).read() for name in app.pdfconfig.config}
    if request.method == 'POST':
        for name, value in request.form.items():
            if name in config:
                config[name] = value
                err = validate_config_yaml(value)
                if err:
                    context['errors'][name] = err
        if not context['errors']:
            for name, content in request.form.items():
                with open(name, 'w') as f:
                    f.write(content.replace('\r', ''))
                context['success'].append(name)
    return render_template('flask/editor.html', **context)


@app.route('/preview')
def preview():
    def dt(attr):
        def inner(fn):
            stat = os.stat(fn)
            return datetime.fromtimestamp(getattr(stat, attr), tz=timezone.utc).strftime('%Y-%m-%dT%H:%M:%S')
        return inner
    pdfs = [fn for fn in os.listdir() if fn.endswith('.pdf')]
    return render_template('flask/preview.html', pdfs=pdfs, modified=dt('st_mtime'), created=dt('st_ctime'))


@app.route('/', methods=['GET', 'POST'])
def index():
    actions = {
        'preview': preview,
        'edit': edit,
        'makepdf': makepdf,
        'view': view
    }
    action = request.args.get('action', None)
    if action in actions:
        return actions[action]()
    return render_template('flask/base.html')


@app.route('/view')
def view():
    path = request.args.get('path')
    return send_from_directory(os.getcwd(), path)
