import os
import threading
import logging
from urllib.parse import urlparse

from weasyprint import LOGGER as wlogger

from pdf12step.adict import AttrDict
from pdf12step.utils import yaml_load

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.abspath(os.getenv('PDF12STEP_DATA_DIR', 'data'))
CONFIG_FILE = os.getenv('PDF12STEP_CONFIG', 'config.yaml')

LEVEL_MAP = {
    0: logging.WARN,
    1: logging.INFO,
    2: logging.DEBUG
}
OPTS = threading.local()
OPTS.logger = logging.getLogger('pdf12step')


def setup_logging(args):
    """
    Sets up the pdf12step and weasyprint logger with given args

    :param dict args: config arguments for verbose & logfile logging settings
    """
    global OPTS
    level = LEVEL_MAP.get(int(args.get('verbose', 0)), logging.DEBUG)
    handler = logging.FileHandler(args['logfile']) if 'logfile' in args and args['logfile'] else logging.StreamHandler()
    formatter = logging.Formatter('%(asctime)s %(levelname)s %(name)s %(message)s')
    handler.setFormatter(formatter)
    handler.setLevel(level)
    for lggr in (wlogger, OPTS.logger):
        lggr.addHandler(handler)
        lggr.setLevel(level)


class Config(AttrDict):
    """
    Config instance that is passed to the template context as `config`
    Defines sane defaults and loads config values from YAML config file
    """
    _defaults = {
        'config_file': CONFIG_FILE,
        'data_dir': DATA_DIR,
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
            OPTS.logger.info(f'Loaded config file {config_file}')
            if not os.path.isfile(config_file):
                raise OSError(f'Configuration file {config_file} not found! Use 12step-init to create one')
            config.update(yaml_load(config_file))
        config.update(args)  # runtime
        OPTS.logger.debug(f'Loaded runtime options {args}')
        for key, value in config.items():
            if value and isinstance(value, dict):
                config[key] = {str(k): str(v) for k, v in value.items()}
        config['site_domain'] = urlparse(config['site_url']).netloc
        return config
