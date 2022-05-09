import sys
import os

import click
from jinja2 import Environment, FileSystemLoader, select_autoescape

from pdf12step.templating import Context
from pdf12step.config import Config, ASSET_DIR, DATA_DIR, BASE_DIR
from pdf12step.client import Client
from pdf12step.adict import AttrDict
from pdf12step.utils import booler, lister
from pdf12step.log import logger


def prompt(name, title, default=None, cast=str):
    """
    Prompts user input and returns a variable with type cast
    """
    field = input(f'{title} [{default}]: ' if default else f'{title}: ').strip()
    if not field:
        if default is not None:
            field = default
        else:
            print(f'Field {name} is required')
            return prompt(name, title, default)
    if field == 'empty':
        field = ''
    field = cast(field)
    logger.debug(f'Got prompt value {name}={field}')
    return {name: field}


def ensure_config(ctx):
    if not ctx.get('config', None):
        click.echo('No config found. Please create one with "12step init" and pass it with the --config option')
        raise click.Abort


def do_download(ctx):
    sections = ctx.obj.sections.split(',') if hasattr(ctx.obj, 'sections') else Client.sections
    client = Client(ctx.obj.configobj.site_url, ctx.obj.configobj.api_url, ctx.obj.configobj.nonce_url)
    client.download(sections, getattr(ctx.obj, 'format', 'json'), ctx.obj.data_dir, ctx.obj.configobj.site_domain)


@click.group('12step')
@click.option('--config', '-c', envvar='PDF12STEP_CONFIG', multiple=True,
              type=click.Path(file_okay=True, dir_okay=False),
              help='Configs file for runtime vars. Can pass multiple to override options.')
@click.option('--verbose', '-v', count=True, default=0, help='More verbose logging')
@click.option('--data-dir', '-D', default=DATA_DIR, envvar='PDF12STEP_DATA_DIR',
              type=click.Path(file_okay=False, dir_okay=True, exists=False),
              help='Data directory to download meeting data to')
@click.option('--asset-dir', '-A', default=ASSET_DIR, envvar='PDF12STEP_ASSET_DIR',
              type=click.Path(file_okay=False, resolve_path=True, dir_okay=True, exists=False),
              help='Asset directory to render static assets to')
@click.option('--logfile',  default=None, help='Optional log file to wrie to')
@click.pass_context
def cli(ctx, config, verbose, data_dir, asset_dir, logfile):
    ctx.ensure_object(dict)
    ctx.obj.update(config=config, data_dir=data_dir, asset_dir=asset_dir,
                   verbose=verbose, logfile=logfile)
    ctx.obj = AttrDict(ctx.obj)
    ctx.obj.configobj = AttrDict(Config.load(ctx.obj))


@cli.command()
@click.option('--output', '-o', default=None, help='Output file name to render to. Use "-" for stdout')
@click.option('--download', '-d', is_flag=True, help='Download the assets before rendering. Produces up to date PDFs')
@click.option('--limit', '-l', type=int, help='Limit the rendering to this number of meetings')
@click.option('--template', '-t', default=None, envvar='PDF12STEP_TEMPLATE', help='Base template to render')
@click.pass_context
def html(ctx, **kwargs):
    """Formats meeting HTML"""
    ensure_config(ctx.obj)
    ctx.obj.update(kwargs)
    if ctx.obj.download:
        do_download(ctx)
    context = Context(ctx.obj.configobj, ctx.obj)
    context.prerender()
    content = context.render(kwargs['template'])
    outfile = ctx.obj.output
    if outfile is None:
        outfile = open(f'{ctx.obj.configobj.date_fmt}.html', 'w')
    elif outfile == '-':
        outfile = sys.stdout.buffer
    else:
        outfile = open(outfile, 'w')
    outfile.write(content)
    outfile.close()
    logger.info(f'Wrote to {outfile.name}')


@cli.command()
@click.option('--output', '-o', default=None, help='Output file name to render to. Use "-" for stdout')
@click.option('--download', '-d', is_flag=True, help='Download the assets before rendering. Produces up to date PDFs')
@click.option('--limit', '-l', type=int, help='Limit the rendering to this number of meetings')
@click.option('--template', '-t', default=None, envvar='PDF12STEP_TEMPLATE', help='Base template to render')
@click.pass_context
def pdf(ctx, **kwargs):
    """Formats meeting PDFs"""
    ensure_config(ctx.obj)
    ctx.obj.update(kwargs)
    if ctx.obj.download:
        do_download(ctx)
    context = Context(ctx.obj.configobj, ctx.obj)
    context.prerender()
    content = context.pdf(kwargs['template'])
    outfile = ctx.obj.output
    if outfile is None:
        outfile = open(f'{ctx.obj.configobj.date_fmt}.pdf', 'wb')
    elif outfile == '-':
        outfile = sys.stdout.buffer
    else:
        outfile = open(outfile, 'wb')
    outfile.write(content)
    outfile.close()
    logger.info(f'Wrote to {outfile.name}')


@cli.command()
@click.option('-a', '--address', default='0.0.0.0', help='The host interface address to bind to')
@click.option('-p', '--port', type=int, default=5000, help='The port to bind to')
@click.pass_context
def flask(ctx, **kwargs):
    """
    Run Flask webapp for Development.
    This should never be run in production!
    You must restart this if you make any changes to code or asset file
    """
    ensure_config(ctx.obj)
    ctx.obj.update(kwargs)
    from pdf12step.flask_app import app

    os.environ['FLASK_APP'] = __name__
    app.pdfconfig = ctx.obj.configobj
    app.run(ctx.obj.address, ctx.obj.port)


@cli.command()
@click.option('-f', '--format', default='json', type=click.Choice(('json', 'csv')), help='Format of downloaded meeting data')
@click.option('-s', '--sections',  default=','.join(Client.sections), help='Comma separated list of sections to download')
@click.pass_context
def download(ctx, **kwargs):
    """
    Downloads meeting data from your site_url
    The site must be a WordPress site running the 12-step-meeting-list plugin.
    """
    ensure_config(ctx.obj)
    ctx.obj.update(kwargs)
    do_download(ctx)


@cli.command()
@click.option('-o', '--output',  default='config.yaml', help='Filename to output your config to')
@click.pass_context
def init(ctx, **kwargs):
    """
    Prompts you to create a custom config
    Iniitialize your custom configuration interactively by answering a few questions
    """
    ctx.obj.update(kwargs)
    sections = [
        ('Data Gathering', [
            ('site_url', 'Site URL running 12 Step Meeting WordPress plugin'),
        ],),
        ('Metadata', [
            ('author', 'Document author', 'empty'),
            ('description', 'Document description', 'empty'),
            ('website', 'Contact website display', 'empty'),
            ('email', 'Contact email address', 'empty'),
            ('address', 'Contact street address', 'empty'),
            ('phone', 'Contact phone number', 'empty'),
            ('fax', 'Contact fax number', 'empty'),
        ],),
        ('Formatting', [
            ('size', 'Page size to print', 'Letter'),
            ('color', 'Cover background and header color', 'lightblue'),
            ('show_links', 'Display links on pages', True, booler),
            ('qrcode_url', 'URL to tie to QR code on cover', 'empty')
        ],),
        ('Customizations', [
            ('template_dirs', 'Directories to search for templates (comma separated)', [], lister),
            ('stylesheets', 'CSS files to add to modify page styles (comma separated)', [], lister),
            ('asset_dir', 'Asset directory to look for static files', './assets'),
            ('attendance_options', 'Only display these comma separated attendance_options (eg in_person/hybrid/online)', [], lister),
            ('filtercodes', 'Do not display meetings that have these codes (comma separated)', [], lister)
        ])
    ]
    ctx = {}
    for section, fields in sections:
        click.echo()
        click.echo(section)
        click.echo('-' * len(section))
        for field in fields:
            ctx.update(prompt(*field))
    env = Environment(
        loader=FileSystemLoader([os.path.join(BASE_DIR, 'templates')]),
        autoescape=select_autoescape(),
    )
    content = env.get_template('default.config.yaml').render(ctx)
    with open(ctx.obj.output, 'w') as conf:
        conf.write(content)
    logger.debug(f'Wrote init config to {ctx.obj.output}')
    click.echo()
    click.echo(f'Your custom config has been rendered to {ctx.obj.output}')
    click.echo('You can now render documents using')
    click.echo(f'12step-pdf -c {ctx.obj.output}')


@cli.command()
@click.pass_context
def shell(ctx, **kwargs):
    """
    Drops into an IPython shell
    Contains the context, config and meetings instances
    """
    from IPython import embed
    ensure_config(ctx.obj)
    ctx.obj.update(kwargs)
    context = Context(ctx.obj.configobj, ctx.obj)
    ctx = sys.modules['__main__'].__dict__
    ctx.update(context=context, config=context.config, meetings=context.get_meetings())
    embed(colors='linux', module=sys.modules['__main__'], user_ns=ctx)
