import argparse
import sys
import os

from jinja2 import Environment, FileSystemLoader, select_autoescape

from pdf12step.templating import Context, DIR
from pdf12step.log import logger
from pdf12step.config import Config
from pdf12step.client import Client


def add_arguments(parser):
    """
    Adds base arguments to all commands

    :param argparse.ArgumentParser parser: Parser isinstance to add base args to
    """
    parser.add_argument('--config', '-c', action='append', help='Configs file for runtime vars. Can pass multiple to override options.')
    parser.add_argument('--verbose', '-v', action='count', default=0, help='More verbose logging')
    parser.add_argument('--logfile', default=None, help='Optional log file to wrie to')
    return parser


pdf_parser = argparse.ArgumentParser(description='Format meeting PDF')
pdf_parser = add_arguments(pdf_parser)
pdf_parser.add_argument('--output', '-o', default=None, help='Output file name to render to. Use "-" for stdout')
pdf_parser.add_argument('--download', '-d', action='store_true', help='Download the assets before rendering. Produces up to date PDFs')
pdf_parser.add_argument('--limit', '-l', type=int, help='Limit the rendering to this number of meetings')

flask_parser = argparse.ArgumentParser(
    description='Run Flask webapp for Development. This should never be run in production! You must restart this if you make any changes to code or asset files')
flask_parser.add_argument('-a', '--address', default='0.0.0.0', help='The host interface address to bind to')
flask_parser.add_argument('-p', '--port', type=int, default=5000, help='The port to bind to')

client_parser = argparse.ArgumentParser(description='Download meeting data from a WordPress site with 12-step-meeting-list plugin.')
client_parser = add_arguments(client_parser)
client_parser.add_argument('-u', '--site-url', default=None, help='WordPress Site URL root')
client_parser.add_argument('-f', '--format', default='json', choices=('json', 'csv'), help='Format of downloaded meeting data')
client_parser.add_argument('-s', '--sections',  default=','.join(Client.sections), help='Comma separated list of sections to download')

init_parser = argparse.ArgumentParser(description='Iniitialize your custom configuration interactively by answering a few questions')
init_parser.add_argument('-o', '--output',  default='config.yaml', help='Filename to output your config to')


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


def init_main():
    args = init_parser.parse_args()
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


def client_main():
    args = client_parser.parse_args().__dict__
    site_url = args.pop('site_url')
    config = Config().load(args)
    Client(site_url if site_url is not None else config.site_url).download(*args['sections'].split(','), format=args['format'])


def pdf_main():
    args = pdf_parser.parse_args()
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


def flask_main():
    from pdf12step.flask_app import app

    args = flask_parser.parse_args()
    os.environ['FLASK_APP'] = __name__
    app.run(args.address, args.port)


def main():
    from IPython import embed

    context = Context({})
    config = context.config
    meetings = context.get_meetings()
    ctx = sys.modules['__main__'].__dict__
    ctx.update(locals())
    embed(colors='linux', module=sys.modules['__main__'], user_ns=ctx)


if __name__ == '__main__':
    main()
