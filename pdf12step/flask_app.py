from os.path import join

from flask import Flask, render_template, request
from flask_weasyprint import HTML as FHTML, render_pdf

from pdf12step.templating import DIR, Context, FSBC, LAYOUT_TEMPLATE


app = Flask(__name__, static_folder=join(DIR, 'assets'))
app.jinja_env.bytecode_cache = FSBC


def context():
    """
    Loads the Context instance from runtime Flask request parameters as args to Context config

    :rtype: Context
    """
    args = dict(request.args)
    args['flask'] = True
    return app.config.setdefault('context', Context(args))


@app.route('/meetings.pdf')
def pdf():
    """
    View to render live PDF view. Takes a while to run but produces live PDF
    """
    context().prerender()
    html = render_template(LAYOUT_TEMPLATE, **app.config['context'])
    return render_pdf(FHTML(string=html), stylesheets=app.config['context']['config']['stylesheets'])


@app.route('/meetings.html')
def html():
    """
    View to render live HTML. Doesnt have the page/header formatting like the PDF but renders faster.
    """
    context().prerender()
    return render_template(LAYOUT_TEMPLATE, **app.config['context'])
