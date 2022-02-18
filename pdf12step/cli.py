import sys
import os

import click
from jinja2 import Environment, FileSystemLoader, select_autoescape

from pdf12step.templating import Context, DIR
from pdf12step.log import logger
from pdf12step.config import Config
from pdf12step.client import Client
from pdf12step.adict import AttrDict
from pdf12step.__main__ import main


def lister(value):
    return value.split(',') if value else []


def booler(value):
    if isinstance(value, str):
        value = value.lower() in ('y', 'yes', 'true')
    return str(value).lower()


def prompt(name, title, default=None, cast=str):
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


@click.group('12step')
@click.option('--config', '-c', multiple=True,  help='Configs file for runtime vars. Can pass multiple to override options.')
@click.option('--verbose', '-v', count=True, default=0, help='More verbose logging')
@click.option('--logfile',  default=None, help='Optional log file to wrie to')
@click.pass_context
def cli(ctx, config, verbose, logfile):
    ctx.ensure_object(dict)
    ctx.obj.update(config=config, verbose=verbose, logfile=logfile)


@cli.command()
@click.option('--output', '-o', default=None, help='Output file name to render to. Use "-" for stdout')
@click.option('--download', '-d', is_flag=True, help='Download the assets before rendering. Produces up to date PDFs')
@click.option('--limit', '-l', type=int, help='Limit the rendering to this number of meetings')
@click.pass_context
def pdf(ctx, **kwargs):
    """Formats meeting PDFs"""
    ctx.obj.update(kwargs)
    args = AttrDict(ctx.obj)
    context = Context(args)
    context.prerender()
    content = context.pdf()
    logger.info(f'Generated {len(content)//1000}KB of PDF content')
    logger.info(f'Total meetings renderd: {len(context["meetings"])}')
    outfile = args.output
    if outfile is None:
        outfile = open(context['now'].strftime('%B %Y Directory.pdf'), 'wb')
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
    ctx.obj.update(kwargs)
    args = AttrDict(ctx.obj)
    from pdf12step.flask_app import app

    os.environ['FLASK_APP'] = __name__
    app.run(args.address, args.port)


@cli.command()
@click.option('-u', '--site-url', default=None, help='WordPress Site URL root')
@click.option('-f', '--format', default='json', type=click.Choice(('json', 'csv')), help='Format of downloaded meeting data')
@click.option('-s', '--sections',  default=','.join(Client.sections), help='Comma separated list of sections to download')
@click.pass_context
def download(ctx, **kwargs):
    """
    Downloads meeting data from your site_url
    The site must be a WordPress site running the 12-step-meeting-list plugin.
    """
    ctx.obj.update(kwargs)
    args = ctx.obj
    site_url = args.pop('site_url')
    config = Config().load(args)
    Client(site_url if site_url is not None else config.site_url).download(*args['sections'].split(','), format=args['format'])


@cli.command()
@click.option('-o', '--output',  default='config.yaml', help='Filename to output your config to')
@click.pass_context
def init(ctx, **kwargs):
    """
    Prompts you to create a custom config
    Iniitialize your custom configuration interactively by answering a few questions
    """
    ctx.obj.update(kwargs)
    args = AttrDict(ctx.obj)
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
            ('show_links', 'Display links on pages', True, booler)
        ],),
        ('Customizations', [
            ('template_dirs', 'Directories to search for templates (comma separated)', [], lister),
            ('stylesheets', 'CSS files to add to modify page styles (comma separated)', [], lister),
            ('attendance_options', 'Only display these comma separated attendance_options (eg in_person/hybrid/online)', [], lister),
            ('filtercodes', 'Do not display meetings that have these codes (comma separated)', [], lister)
        ])
    ]
    ctx = {}
    for section, fields in sections:
        print()
        print(section)
        print('-' * len(section))
        for field in fields:
            ctx.update(prompt(*field))
    env = Environment(
        loader=FileSystemLoader([os.path.join(DIR, 'templates')]),
        autoescape=select_autoescape(),
    )
    content = env.get_template('default.config.yaml').render(ctx)
    with open(args.output, 'w') as conf:
        conf.write(content)
    logger.debug(f'Wrote init config to {args.output}')
    print()
    print(f'Your custom config has been rendered to {args.output}')
    print('You can now render documents using')
    print(f'12step-pdf -c {args.output}')


@cli.command()
@click.pass_context
def shell(ctx, **kwargs):
    """
    Drops into an IPython shell
    Contains the context, config and meetings instances
    """
    ctx.obj.update(kwargs)
    args = AttrDict(ctx.obj)
    main(args)


if __name__ == '__main__':
    import ipdb
    with ipdb.launch_ipdb_on_exception():
        cli(obj={})
