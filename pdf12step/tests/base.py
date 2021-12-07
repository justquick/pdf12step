from os import path

DATA_DIR = path.join(path.dirname(__file__), 'data')
CONFIG_FILE = path.join(DATA_DIR, 'test.config.yml')
ENV = {
    'PDF12STEP_DATA_DIR': DATA_DIR,
    'PDF12STEP_CONFIG': CONFIG_FILE
}


def contains_parts(content, parts):
    for part in parts:
        assert part in content
