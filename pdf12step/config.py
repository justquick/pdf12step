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
        'filtercodes': {},
        'codemap': {},
        'meetingcodes': {},
        'zipcodes': {},
        'stylesheets': [],
        'template_dirs': [],
        'asset_dir': 'assets',
        'qrcode_url': None,
        'notes_pages': 0,
        'even_pages': True,
        'date_fmt': datetime.now().strftime('%B %Y Directory'),
        'sections': ['contact', 'codes', 'misc', 'regions', 'index', 'list', 'readings', 'notes']
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
        for config_file in args['config']:  # from file
            logger.info(f'Loaded config file {config_file}')
            if not os.path.isfile(config_file):
                raise OSError(f'Configuration file {config_file} not found! Use 12step-init to create one')
            config.update(yaml_load(config_file))
        config.update(args)  # runtime
        logger.debug(f'Loaded runtime options {args}')
        for key, value in config.items():
            if value and isinstance(value, dict):
                config[key] = {str(k): str(v) for k, v in value.items()}
        config['site_domain'] = urlparse(config['site_url']).netloc
        return config
