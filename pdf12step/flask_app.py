from os.path import join
import json
import sys
import subprocess
try:
    from flask import Flask
except ModuleNotFoundError:
    print('You must install Flask to use the pdf12step Flask app')
    exit(1)

from flask import render_template, request, Response
from flask_weasyprint import HTML as FHTML, render_pdf

from yaml.parser import ParserError
from yaml.scanner import ScannerError

from pdf12step.templating import Context, FSBC, LAYOUT_TEMPLATE
from pdf12step.config import BASE_DIR
from pdf12step.utils import yaml_load


app = Flask(__name__, static_folder=join(BASE_DIR, 'assets'))
app.secret_key = 'wtf'
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
        hashmap = {str(hash(name)): name for name in app.pdfconfig.config}
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
    return render_template('flask/pdf.html', hash=hash, errors=errors, app_config=app.pdfconfig, config=app.pdfconfig.config)


@app.route('/edit', methods=['GET', 'POST'])
def edit():
    context = {'hash': hash, 'errors': {}, 'success': []}
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
