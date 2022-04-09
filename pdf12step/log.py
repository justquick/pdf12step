import logging
import sys

from weasyprint import LOGGER as wlogger

LEVEL_MAP = {
    0: logging.WARN,
    1: logging.INFO,
    2: logging.DEBUG
}


logger = logging.getLogger('pdf12step')


def setup_logging(args):
    """
    Sets up the pdf12step and weasyprint logger with given args

    :param dict args: config arguments for verbose & logfile logging settings
    """
    level = LEVEL_MAP.get(int(args.get('verbose', 0)), logging.DEBUG)
    if 'logfile' in args and args['logfile']:
        if args['logfile'] == '-':
            handler = logging.StreamHandler(sys.stdout)
        else:
            logging.FileHandler(args['logfile'])
    else:
        handler = logging.StreamHandler(sys.stderr)
    formatter = logging.Formatter('%(asctime)s %(levelname)s %(name)s %(message)s')
    handler.setFormatter(formatter)
    handler.setLevel(level)
    for lggr in (wlogger, logger):
        lggr.addHandler(handler)
        lggr.setLevel(level)
