import os
import logging

from weasyprint import LOGGER as wlogger
try:
    from yaml import CLoader as Loader
except ImportError:
    from yaml import Loader

from pdf12step.adict import AttrDict
from pdf12step.log import logger


DATA_DIR = os.path.abspath(os.getenv('PDF12STEP_DATA_DIR', 'data'))
CONFIG_FILE = os.getenv('PDF12STEP_CONFIG', 'config.yaml')

LEVEL_MAP = {
    0: logging.WARN,
    1: logging.INFO,
    2: logging.DEBUG
}


def setup_logging(args):
    """
    Sets up the pdf12step and weasyprint logger with given args

    :param dict args: config arguments for verbose & logfile logging settings
    """
    level = LEVEL_MAP.get(int(args.get('verbose', 0)), logging.DEBUG)
    handler = logging.FileHandler(args['logfile']) if 'logfile' in args and args['logfile'] else logging.StreamHandler()
    formatter = logging.Formatter('%(asctime)s %(levelname)s %(name)s %(message)s')
    handler.setFormatter(formatter)
    handler.setLevel(level)
    for lggr in (wlogger, logger):
        lggr.addHandler(handler)
        lggr.setLevel(level)


def yaml_load(filename):
    """
    Returns the config dict loaded from the given filename

    :param str filename: YAML filename to load
    :rtype: dict
    """
    stream = open(filename)
    loader = Loader(stream)
    try:
        return loader.get_single_data()
    finally:
        stream.close()
        loader.dispose()


class Config(AttrDict):
    """
    Config instance that is passed to the template context as `config`
    Defines sane defaults and loads config values from YAML config file
    """
    _defaults = {
        'config_file': CONFIG_FILE,
        'site_url': None,
        'size': 'Letter',
        'color': 'lightblue',
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
    }

    def load(self, args):
        """
        Loads the config from defaults, file and args in that order

        :param dict args: Args override pass for runtime overrides
        """
        if not isinstance(args, dict):
            args = args.__dict__ if hasattr(args, '__dict__') else dict(args)
        setup_logging(args)
        self.update(self._defaults)  # load sane defaults
        if 'config' not in args or args['config'] is None:
            args['config'] = [self._defaults['config_file']]
        for config_file in args['config']:  # from file
            logger.info(f'Loaded config file {config_file}')
            if not os.path.isfile(config_file):
                raise OSError(f'Configuration file {config_file} not found! Use 12step-init to create one')
            self.update(yaml_load(config_file))
        self.update(args)  # runtime
        logger.debug(f'Loaded runtime options {args}')
        for key, value in self.items():
            if value and isinstance(value, dict):
                self[key] = {str(k): str(v) for k, v in value.items()}
        return self
