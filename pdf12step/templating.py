from os import path, makedirs, getcwd
from datetime import datetime
from collections import defaultdict
from functools import reduce
from pprint import pformat

from weasyprint import HTML
from jinja2 import (Environment, FileSystemLoader, FileSystemBytecodeCache,
                    select_autoescape, PackageLoader, ChoiceLoader)

from pdf12step.meetings import MeetingSet, DAYS
from pdf12step.cached import cached_property
from pdf12step.config import CONFIG, BASE_DIR
from pdf12step.utils import slugify, link, codify, qrcode
from pdf12step.log import logger


FSBC = FileSystemBytecodeCache()
LAYOUT_TEMPLATE = 'layout.html'
ASSET_TEMPLATES = {
    'assets/img/cover_background.svg': ('img', 'cover_background.svg'),
    'assets/css/style.css': ('css', 'style.css')
}


def asset_join(*paths):
    return path.join(CONFIG.asset_dir, *paths).replace('\\', '/')


class Context(dict):
    """
    Context for jinja2 templating

    :param dict args: Runtime arguments to inject into template context
    """

    def __init__(self, args):
        dict.__init__(self)
        self.args = args = args if isinstance(args, dict) else args.__dict__
        self.is_flask = args.get('flask', False)
        self.update(
            meetings=self.get_meetings(),
            DAYS=DAYS,
            now=datetime.now(),
            zipcodes_by_region=self.zipcodes_by_region,
            filtered_codes=self.filtered_codes,
            stylesheets=self.stylesheets,
            slugify=slugify,
            codify=codify(CONFIG.codemap, CONFIG.filtercodes),
            link=link(CONFIG.show_links),
            qrcode=self.qrcode,
            config=CONFIG
        )
        logger.info('Loaded context config')
        logger.debug(pformat(dict(self)))

    @cached_property
    def qrcode(self):
        if CONFIG.qrcode_url:
            img_file = asset_join('img', 'qrcode.png')
            qrcode(CONFIG.qrcode_url, img_file, back_color=CONFIG.color)
            logger.info(f'Created QR {img_file}')
            return img_file

    @cached_property
    def zipcodes_by_region(self):
        """
        Returns a mapping of region->zipcode for zipcode list in config

        :rtype: dict
        """
        zbr = defaultdict(set)
        for zipcode, region in CONFIG.zipcodes.items():
            zbr[region].add(zipcode)
        return zbr

    @cached_property
    def filtered_codes(self):
        """
        Returns a list of meeting (code, name) after the codes have been filtered and remapped

        :rtype: list
        """
        codes = []
        for code, name in CONFIG.meetingcodes.items():
            if code in CONFIG.filtercodes:
                continue
            code = CONFIG.codemap.get(code, code)
            codes.append((code, name))
        return codes

    def get_meetings(self, meetings_file=None):
        """
        Loads list of meetings for main context based on filters/limiting

        :rtype: MeetingSet
        """
        if meetings_file is None:
            meetings_file = path.join(CONFIG.data_dir, f'{CONFIG.site_domain}-meetings.json')
        if not path.isfile(meetings_file):
            raise OSError(f'Meeting data file {meetings_file} not found! Please download first')
        meetings = MeetingSet(meetings_file)
        logger.info(f'Loaded {len(meetings)} meetings from {meetings_file}')
        if getattr(CONFIG, 'attendance_options', []):
            meetings = meetings.by_value('attendance_option').items()
            options = [meeting_set for attendance_option, meeting_set in meetings
                       if attendance_option in CONFIG.attendance_options]
            meetings = reduce(lambda x, y: x + y, options)
        limit = self.args.get('limit', 0)
        if limit:
            meetings = meetings.limit(int(limit))
        return meetings

    @cached_property
    def stylesheets(self):
        """
        Returns a list of CSS stylesheets to include.
        Adds default stylesheet `assets/css/style.css` first and adds others from config.stylesheets

        :rtype: list
        """
        sheets = [asset_join('css', 'style.css')]  # asset css
        if CONFIG.stylesheets:
            for sheet in CONFIG.stylesheets:
                sheet = path.abspath(path.expandvars(sheet))
                if not path.isfile(sheet):
                    raise OSError(f'CSS File not found: {sheet}')
                sheet = path.relpath(sheet, getcwd()).replace('\\', '/')
                sheets.append(sheet)
        logger.info(f'Using stylesheets: {sheets}')
        return sheets

    @cached_property
    def template_dirs(self):
        """
        Returns a list of template directories for jinja2 to search
        Adds default stylesheet `pdf12step/templates` first and adds others from config.stylesheets

        :rtype: list
        """
        dirs = [path.join(BASE_DIR, 'templates')]  # package templates
        if CONFIG.template_dirs:
            for tdir in CONFIG.template_dirs:
                tdir = path.abspath(path.expandvars(tdir))
                if not path.isdir(tdir):
                    raise OSError(f'Template folder not found: {tdir}')
                dirs.append(tdir)
        logger.info(f'Using template dirs: {dirs}')
        return dirs

    @cached_property
    def env(self):
        """
        Returns jinja2 Environment used to render all templates.

        :rtype: jinja2.Environment
        """
        global FSBC
        environ = Environment(
            loader=ChoiceLoader([FileSystemLoader(self.template_dirs), PackageLoader('pdf12step')]),
            autoescape=select_autoescape(),
            bytecode_cache=FSBC,
        )
        logger.info('Loaded template env')
        return environ

    def render(self, template=LAYOUT_TEMPLATE):
        """
        Renders a template by name and returns its content

        :param str template: relative name of template to load
        :rtype: str
        """
        logger.info(f'Renderd {template}')
        return self.env.get_template(template).render(self)

    def prerender(self):
        """
        Prerenders the assets ahead of page render to ensure proper values in assets are set
        """
        for template, dest in ASSET_TEMPLATES.items():
            dest = asset_join(*dest)
            dest_dir = path.dirname(dest)
            makedirs(dest_dir, exist_ok=True)
            with open(dest, 'w') as destfile:
                destfile.write(self.render(template))

    def html(self):
        """
        Gets the weasyprint HTML instance from this ontext

        :rtype: weasyprint.HTML
        """
        return HTML(string=self.render(), base_url=path.dirname(CONFIG.asset_dir), encoding='utf8')

    def pdf(self):
        """
        Returns the PDF content from this  of context

        :rtype: bytes
        """
        document = self.html().render(optimize_size=('images', 'fonts'))
        if CONFIG.even_pages and len(document.pages) % 2:
            note = document.pages[-2]
            document.pages.insert(-1, note)
        content = document.write_pdf()
        logger.info(f'Generated {len(document.pages)} pages')
        logger.info(f'Generated {len(content)//1000}KB of PDF content')
        return content
