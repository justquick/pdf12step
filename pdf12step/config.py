import os
from datetime import datetime
from urllib.parse import urlparse

from pdf12step.adict import AttrDict
from pdf12step.utils import yaml_load
from pdf12step.log import logger, setup_logging

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.abspath(os.getenv('PDF12STEP_DATA_DIR', 'data'))
ASSET_DIR = os.path.abspath(os.getenv('PDF12STEP_ASSET_DIR', 'assets'))
CONFIG_FILE = os.getenv('PDF12STEP_CONFIG', 'config.yaml')
BASE_TEMPLATE = os.getenv('PDF12STEP_BASE_TEMPLATE', 'layout.html')
LIST_TEMPLATE = os.getenv('PDF12STEP_LIST_TEMPLATE', 'list_2sections.html')
DEFAULT_CODES = {
    '11': '11th Step Meditation',
    '12x12': '12 Steps & 12 Traditions',
    'A': 'Secular',
    'ABSI': 'As Bill Sees It',
    'AL': 'Concurrent with Alateen',
    'AL-AN': 'Concurrent with Al-Anon',
    'ASL': 'American Sign Language',
    'B': 'Big Book',
    'BA': 'Babysitting Available',
    'BE': 'Newcomer',
    'BI': 'Bisexual',
    'BRK': 'Breakfast',
    'C': 'Closed',
    'CAN': 'Candlelight',
    'CF': 'Child-Friendly',
    'D': 'Discussion',
    'DB': 'Digital Basket',
    'DD': 'Dual Diagnosis',
    'DR': 'Daily Reflections',
    'EN': 'English',
    'FF': 'Fragrance Free',
    'FR': 'French',
    'G': 'Gay',
    'GR': 'Grapevine',
    'H': 'Birthday',
    'HE': 'Hebrew',
    'ITA': 'Italian',
    'JA': 'Japanese',
    'KOR': 'Korean',
    'L': 'Lesbian',
    'LGBTQ': 'LGBTQ',
    'LIT': 'Literature',
    'LS': 'Living Sober',
    'M': 'Men',
    'MED': 'Meditation',
    'N': 'Native American',
    'NDG': 'Indigenous',
    'O': 'Open',
    'OUT': 'Outdoor',
    'P': 'Professionals',
    'POC': 'People of Color',
    'POL': 'Polish',
    'POR': 'Portuguese',
    'PUN': 'Punjabi',
    'RUS': 'Russian',
    'S': 'Spanish',
    'SEN': 'Seniors',
    'SM': 'Smoking Permitted',
    'SP': 'Speaker',
    'ST': 'Step Study',
    'T': 'Transgender',
    'TC': 'Location Temporarily Closed',
    'TR': 'Tradition Study',
    'W': 'Women',
    'X': 'Wheelchair Access',
    'XB': 'Wheelchair-Accessible Bathroom',
    'XT': 'Cross Talk Permitted',
    'Y': 'Young People'
}


class Config(AttrDict):
    """
    Config instance that is passed to the template context as `config`
    Defines sane defaults and loads config values from YAML config file
    """
    _defaults = {
        'config_file': CONFIG_FILE,
        'data_dir': DATA_DIR,
        'section_group1': 'day_display',
        'section_group2': 'region_display',
        'base_template': BASE_TEMPLATE,
        'list_template': LIST_TEMPLATE,
        'site_url': None,
        'site_domain': None,
        'api_url': None,
        'nonce_url': None,
        'size': 'Letter',
        'color': 'lightblue',
        'header_color': 'lightblue',
        'author': 'Recovery Intergroup Council',
        'description': '',
        'address': '',
        'phone': '',
        'fax': '',
        'email': '',
        'website': '',
        'show_links': True,
        'filter': {},
        'filtercodes': {},
        'codemap': {},
        'meetingcodes': DEFAULT_CODES,
        'zipcodes': {},
        'stylesheets': [],
        'template_dirs': [],
        'asset_dir': ASSET_DIR,
        'qrcode_url': None,
        'notes_pages': 0,
        'even_pages': True,
        'date_fmt': datetime.now().strftime('%B %Y Directory'),
        'sections': ['contact', 'codes', 'misc', 'regions', 'index', 'list_2sections', 'readings', 'notes'],
        'zoom': 1
    }

    @classmethod
    def load(cls, args):
        """
        Loads the config from defaults, file and args in that order

        :param dict args: Args override pass for runtime overrides
        """
        config = {}
        if not isinstance(args, dict):
            args = args.__dict__ if hasattr(args, '__dict__') else dict(args)
        setup_logging(args)
        config.update(cls._defaults)  # load sane defaults
        if 'config' not in args or args['config'] is None:
            args['config'] = [cls._defaults['config_file']]
        for config_opt in args['config']:
            logger.info(f'Loaded config option "{config_opt}"')
            config.update(yaml_load(config_opt))
        config.update(args)  # runtime
        logger.debug(f'Loaded runtime options {args}')
        for key, value in config.items():
            if value and isinstance(value, dict):
                config[key] = {str(k): str(v) for k, v in value.items()}
        config['site_domain'] = urlparse(config['site_url']).netloc
        meetingcodes = config['meetingcodes'].copy()
        meetingcodes.update(DEFAULT_CODES)
        config['meetingcodes'] = meetingcodes
        return config
