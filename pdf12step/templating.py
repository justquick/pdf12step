import re
from os import path, makedirs
from datetime import datetime
from collections import defaultdict
from functools import reduce
from pprint import pformat

from weasyprint import HTML
from jinja2 import Environment, FileSystemLoader, FileSystemBytecodeCache, select_autoescape, PackageLoader, ChoiceLoader
from markupsafe import Markup
from qrcode import QRCode

from pdf12step.client import Client
from pdf12step.meetings import MeetingSet, DAYS
from pdf12step.cached import cached_property
from pdf12step.log import logger
from pdf12step.config import Config, DATA_DIR


FSBC = FileSystemBytecodeCache()
LAYOUT_TEMPLATE = 'layout.html'
DIR = path.abspath(path.dirname(__file__))
ASSET_TEMPLATES = {
    'assets/img/cover_background.svg': ('img', 'cover_background.svg'),
    'assets/css/style.css': ('css', 'style.css')
}


def slugify(value):
    """
    Turns str into slug value

    :param str value: Regular string to slugify
    """
    value = re.sub(r'[^\w\s-]', '', value.lower()).strip()
    return re.sub(r'[-\s]+', '-', value)


def codify(codemap, filtercodes):
    """
    Filters codes list in values to renamed/ignored list of codes

    :param dict codemap: Mapping of codes to names to use in display
    :param list filtercodes: List of codes to ignore
    """
    def inner(values):
        codes = [codemap.get(code, code)
                 for code in values if code and code not in filtercodes]
        return filter(lambda c: len(c), codes)
    return inner


def link(show):
    """
    Displays an <a> tag for the given url and name
    If show (config.show_links) is False, just returns name

    :param bool show: True if to display <a> tags
    """
    def inner(url, name, id=None):
        if show:
            id = f' id="{id}"' if id is not None else ''
            return Markup(f'<a{id} href="{url}">{name}</a>')
        return name
    return inner


class Context(dict):
    """
    Context for jinja2 templating

    :param dict args: Runtime arguments to inject into template context
    """

    def __init__(self, args):
        dict.__init__(self)
        self.args = args = args if isinstance(args, dict) else args.__dict__
        self.data_dir = args.get('data_dir', DATA_DIR)
        self.asset_dir = args.get('asset_dir', 'assets')
        self.is_flask = args.get('flask', False)
        self.config = config = Config().load(args)
        if args.get('download', False):
            Client(config.site_url).download()
        self.update(
            meetings=self.get_meetings(),
            DAYS=DAYS,
            now=datetime.now(),
            zipcodes_by_region=self.zipcodes_by_region,
            filtered_codes=self.filtered_codes,
            stylesheets=self.stylesheets,
            slugify=slugify,
            codify=codify(config.codemap, config.filtercodes),
            link=link(config.show_links),
            qrcode=self.qrcode,
            config=config
        )
        logger.info('Loaded context config')
        logger.debug(pformat(dict(self)))

    @cached_property
    def qrcode(self):
        if self.config.qrcode_url:
            qr = QRCode(box_size=5)
            qr.add_data(self.config.qrcode_url)
            qr.make(fit=True)
            img = qr.make_image(back_color=self.config.color)
            img_file = path.join(self.asset_dir,  'img', 'qrcode.png')
            dest = path.dirname(img_file)
            if not path.isdir(dest):
                makedirs(dest)
            img.save(img_file)
            return img_file

    @cached_property
    def zipcodes_by_region(self):
        """
        Returns a mapping of region->zipcode for zipcode list in config

        :rtype: dict
        """
        zbr = defaultdict(set)
        for zipcode, region in self.config.zipcodes.items():
            zbr[region].add(zipcode)
        return zbr

    @cached_property
    def filtered_codes(self):
        """
        Returns a list of meeting (code, name) after the codes have been filtered and remapped

        :rtype: list
        """
        codes = []
        for code, name in self.config.meetingcodes.items():
            if code in self.config.filtercodes:
                continue
            code = self.config.codemap.get(code, code)
            codes.append((code, name))
        return codes

    def get_meetings(self):
        """
        Loads list of meetings for main context based on filters/limiting

        :rtype: MeetingSet
        """
        meetings_file = path.join(self.data_dir, 'meetings.json')
        if not path.isfile(meetings_file):
            raise OSError(f'Meeting data file {meetings_file} not found! Please download first')
        meetings = MeetingSet(meetings_file)
        if getattr(self.config, 'attendance_options', []):
            meetings = meetings.by_value('attendance_option').items()
            options = [meeting_set for attendance_option, meeting_set in meetings
                       if attendance_option in self.config.attendance_options]
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
        sheets = ['assets/css/style.css']
        if self.config.stylesheets:
            for sheet in self.config.stylesheets:
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
        if self.config.template_dirs:
            for tdir in self.config.template_dirs:
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
            dest = path.join(self.asset_dir, *dest)
            dest_dir = path.dirname(dest)
            if not path.isdir(dest_dir):
                makedirs(dest_dir)
            with open(dest, 'w') as destfile:
                destfile.write(self.render(template))

    def html(self):
        """
        Gets the weasyprint HTML instance from this ontext

        :rtype: weasyprint.HTML
        """
        return HTML(string=self.render(), base_url=path.dirname(self.asset_dir), encoding='utf8')

    def pdf(self):
        """
        Returns the PDF content from this  of context

        :rtype: bytes
        """
        return self.html().render().write_pdf()
