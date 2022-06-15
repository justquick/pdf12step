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
from pdf12step.config import BASE_DIR, BASE_TEMPLATE
from pdf12step.utils import slugify, link, codify, qrcode
from pdf12step.log import logger


FSBC = FileSystemBytecodeCache()
ASSET_TEMPLATES = {
    'assets/img/cover_background.svg': ('img', 'cover_background.svg'),
}


def asset_join(asset_dir, *paths):
    return path.join(asset_dir, *paths).replace('\\', '/')


class Context(dict):
    """
    Context for jinja2 templating

    :param dict args: Runtime arguments to inject into template context
    """

    def __init__(self, config, args):
        dict.__init__(self)
        self.config = config
        self.args = args = args if isinstance(args, dict) else args.__dict__
        self.is_flask = args.get('flask', False)
        self.meetings = self.get_meetings()
        self.update(
            meetings=self.meetings,
            DAYS=DAYS,
            now=datetime.now(),
            zipcodes_by_region=self.zipcodes_by_region,
            filtered_codes=self.filtered_codes,
            stylesheets=self.stylesheets,
            slugify=slugify,
            codify=codify(self.config.codemap, self.config.filtercodes),
            link=link(self.config.show_links),
            qrcode=self.qrcode,
            config=config
        )
        logger.info('Loaded context config')
        logger.debug(pformat(dict(self)))

    @cached_property
    def qrcode(self):
        if self.config.qrcode_url:
            img_file = asset_join(self.config.asset_dir, 'img', 'qrcode.png')
            qrcode(self.config.qrcode_url, img_file, back_color=self.config.color)
            logger.info(f'Created QR {img_file}')
            if self.is_flask:
                return path.relpath(img_file, getcwd())
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
            if self.config.filtercodes and code in self.config.filtercodes or code not in self.meetings.types:
                continue
            code = self.config.codemap.get(code, code)
            codes.append((code, name))
        return codes

    def get_meetings(self, meetings_file=None):
        """
        Loads list of meetings for main context based on filters/limiting

        :rtype: MeetingSet
        """
        if meetings_file is None:
            meetings_file = path.join(self.config.data_dir, f'{self.config.site_domain}-meetings.json')
        if not path.isfile(meetings_file):
            raise OSError(f'Meeting data file {meetings_file} not found! Please download first')
        meetings = MeetingSet(meetings_file)
        logger.info(f'Loaded {len(meetings)} meetings from {meetings_file}')
        if getattr(self.config, 'attendance_options', []):
            meetings = meetings.by_value('attendance_option').items()
            options = [meeting_set for attendance_option, meeting_set in meetings
                       if attendance_option in self.config.attendance_options]
            if not options:
                raise ValueError('No meetings found when filtered by attendance_option')
            meetings = reduce(lambda x, y: x + y, options)
        if self.config.filter:
            meetings = MeetingSet(meetings.filter(**self.config.filter))
        if self.config.filtercodes:
            meetings = MeetingSet(meetings.filter_types(self.config.filtercodes))
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
        sheets = self.config.stylesheets if self.config.stylesheets else ['assets/css/font.css', 'assets/css/style.css']
        logger.info(f'Using stylesheets: {sheets}')
        return sheets

    @cached_property
    def template_dirs(self):
        """
        Returns a list of template directories for jinja2 to search
        Adds default stylesheet `pdf12step/templates` first and adds others from config.stylesheets

        :rtype: list
        """
        dirs = []
        if self.config.template_dirs:
            for tdir in self.config.template_dirs:
                tdir = path.abspath(path.expandvars(tdir))
                if not path.isdir(tdir):
                    raise OSError(f'Template folder not found: {tdir}')
                dirs.append(tdir)
        dirs.append(path.join(BASE_DIR, 'templates'))  # package templates
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

    def render(self, template=None):
        """
        Renders a template by name and returns its content

        :param str template: relative name of template to load
        :rtype: str
        """
        if template is None:
            template = self.config.get('base_template', BASE_TEMPLATE)
        logger.info(f'Renderd {template}')
        return self.env.get_template(template).render(self)

    def prerender(self):
        """
        Prerenders the assets ahead of page render to ensure proper values in assets are set
        """
        for template, dest in ASSET_TEMPLATES.items():
            dest = asset_join(self.config.asset_dir, *dest)
            dest_dir = path.dirname(dest)
            makedirs(dest_dir, exist_ok=True)
            with open(dest, 'w') as destfile:
                destfile.write(self.render(template))

    def html(self, template=None):
        """
        Gets the weasyprint HTML instance from this ontext

        :rtype: weasyprint.HTML
        """
        return HTML(string=self.render(template), base_url=path.dirname(self.config.asset_dir), encoding='utf8')

    def pdf(self, template=None):
        """
        Returns the PDF content from this  of context

        :rtype: bytes
        """
        html = self.html(template)
        try:
            document = html.render(optimize_size=('images', 'fonts'))
        except TypeError:
            # older versions of weasyprint
            document = html.render()
        if self.config.even_pages and len(document.pages) % 2 and len(document.pages) > 2:
            note = document.pages[-2]
            document.pages.insert(-1, note)
        content = document.write_pdf(zoom=self.config.zoom)
        logger.info(f'Generated {len(document.pages)} pages')
        logger.info(f'Generated {len(content)//1000}KB of PDF content')
        return content
