from os import path, makedirs
from datetime import datetime
from collections import defaultdict
from functools import reduce
from pprint import pformat

from weasyprint import HTML
from jinja2 import (Environment, FileSystemLoader, FileSystemBytecodeCache,
                    select_autoescape, PackageLoader, ChoiceLoader)

from pdf12step.meetings import MeetingSet, DAYS
from pdf12step.cached import cached_property
from pdf12step.config import OPTS
from pdf12step.utils import slugify, link, codify, qrcode


FSBC = FileSystemBytecodeCache()
LAYOUT_TEMPLATE = 'layout.html'
DIR = path.abspath(path.dirname(__file__))
BASE_CSS = 'assets/css/style.css'
ASSET_TEMPLATES = {
    'assets/img/cover_background.svg': ('img', 'cover_background.svg'),
    BASE_CSS: ('css', 'style.css')
}


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
            codify=codify(OPTS.config.codemap, OPTS.config.filtercodes),
            link=link(OPTS.config.show_links),
            qrcode=self.qrcode,
            config=OPTS.config
        )
        OPTS.logger.info('Loaded context config')
        OPTS.logger.debug(pformat(dict(self)))

    @cached_property
    def qrcode(self):
        if OPTS.config.qrcode_url:
            img_file = path.join(OPTS.config.asset_dir,  'img', 'qrcode.png')
            qrcode(OPTS.config.qrcode_url, img_file, back_color=OPTS.config.color)
            OPTS.logger.info(f'Created QR {img_file}')
            return img_file

    @cached_property
    def zipcodes_by_region(self):
        """
        Returns a mapping of region->zipcode for zipcode list in config

        :rtype: dict
        """
        zbr = defaultdict(set)
        for zipcode, region in OPTS.config.zipcodes.items():
            zbr[region].add(zipcode)
        return zbr

    @cached_property
    def filtered_codes(self):
        """
        Returns a list of meeting (code, name) after the codes have been filtered and remapped

        :rtype: list
        """
        codes = []
        for code, name in OPTS.config.meetingcodes.items():
            if code in OPTS.config.filtercodes:
                continue
            code = OPTS.config.codemap.get(code, code)
            codes.append((code, name))
        return codes

    def get_meetings(self, meetings_file=None):
        """
        Loads list of meetings for main context based on filters/limiting

        :rtype: MeetingSet
        """
        if meetings_file is None:
            meetings_file = path.join(OPTS.config.data_dir, f'{OPTS.config.site_domain}-meetings.json')
        if not path.isfile(meetings_file):
            raise OSError(f'Meeting data file {meetings_file} not found! Please download first')
        meetings = MeetingSet(meetings_file)
        OPTS.logger.info(f'Loaded {len(meetings)} meetings from {meetings_file}')
        if getattr(OPTS.config, 'attendance_options', []):
            meetings = meetings.by_value('attendance_option').items()
            options = [meeting_set for attendance_option, meeting_set in meetings
                       if attendance_option in OPTS.config.attendance_options]
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
        sheets = [BASE_CSS]
        if OPTS.config.stylesheets:
            for sheet in OPTS.config.stylesheets:
                sheet = path.abspath(path.expandvars(sheet))
                if not path.isfile(sheet):
                    raise OSError(f'CSS File not found: {sheet}')
                sheets.append(sheet)
        return sheets

    @cached_property
    def template_dirs(self):
        """
        Returns a list of template directories for jinja2 to search
        Adds default stylesheet `pdf12step/templates` first and adds others from config.stylesheets

        :rtype: list
        """
        dirs = [path.join(DIR, 'templates')]
        if OPTS.config.template_dirs:
            for tdir in OPTS.config.template_dirs:
                tdir = path.abspath(path.expandvars(tdir))
                if not path.isdir(tdir):
                    raise OSError(f'Template folder not found: {tdir}')
                dirs.append(tdir)
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
        OPTS.logger.info('Loaded template env')
        return environ

    def render(self, template=LAYOUT_TEMPLATE):
        """
        Renders a template by name and returns its content

        :param str template: relative name of template to load
        :rtype: str
        """
        OPTS.logger.info(f'Renderd {template}')
        return self.env.get_template(template).render(self)

    def prerender(self):
        """
        Prerenders the assets ahead of page render to ensure proper values in assets are set
        """
        for template, dest in ASSET_TEMPLATES.items():
            dest = path.join(OPTS.config.asset_dir, *dest)
            dest_dir = path.dirname(dest)
            makedirs(dest_dir, exist_ok=True)
            with open(dest, 'w') as destfile:
                destfile.write(self.render(template))

    def html(self):
        """
        Gets the weasyprint HTML instance from this ontext

        :rtype: weasyprint.HTML
        """
        return HTML(string=self.render(), base_url=path.dirname(OPTS.config.asset_dir), encoding='utf8')

    def pdf(self):
        """
        Returns the PDF content from this  of context

        :rtype: bytes
        """
        return self.html().render().write_pdf()
