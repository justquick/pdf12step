import re
import requests
import json
import os
from csv import DictWriter

from pdf12step.adict import AttrDict
from pdf12step.cached import cached_property
from pdf12step.log import logger
from pdf12step.config import DATA_DIR


DEFAULTS = {
    'mode': 'search',
    'distance': 2,
    'view': 'list',
    'distance_units': 'm',
}
NONCE_RE = re.compile('nonce":"([0-9a-fA-F]+)"')


def csv_dump(data, outfile):
    """
    Dumps csv data to a file with default Nones and AttrDefaults to handle missing fields

    :param list data: List of row data to dump
    :param file outfile: File instance to write to
    """
    keys = set()
    [keys.update(item.keys()) for item in data]
    if 'id' in keys:
        keys = ['id'] + list(keys.difference({'id'}))
    with open(outfile, 'w') as csvfile:
        writer = DictWriter(csvfile, keys,  extrasaction='ignore')
        writer.writeheader()
        writer.writerows([AttrDict({key: '|'.join(value) if isinstance(value, list) else value
                                    for key, value in item.items()})
                          for item in data])


def json_dump(data, outfile):
    with open(outfile, 'w') as jsonfile:
        json.dump(data, jsonfile, indent=2)


class Client(object):
    """
    Client that makes HTTP[S] calls to the WP site and fetches the data

    :param str url: Base URL of the WP site to gather data from
    """
    sections = ('meetings',)  # 'locations', 'groups', 'regions') these arent necessary for now

    def __init__(self, site_url=None, api_uri='wordpress/wp-admin/admin-ajax.php', nonce_uri=None):
        if not site_url:
            raise ValueError('Site URL required')
        self.site_url = site_url.rstrip('/')
        self.api_uri = api_uri
        self.nonce_uri = nonce_uri

    @cached_property
    def nonce(self):
        """
        Fetches the nonce on a base page to use in subsequent requests to the WP site
        Bypasses WP CSRF protection

        :rtype: str
        """
        response = requests.get(f'{self.site_url}/{self.nonce_uri}')
        response.raise_for_status()
        content = response.content.decode()
        match = NONCE_RE.search(content, re.M)
        if match:
            return match.groups()[0]

    def _dispatch(self, method, uri, *args, **kwargs):
        logger.debug(f'{method.upper()} {self.site_url}/{uri} {args}')
        method = getattr(requests, method)
        if not uri.startswith(self.site_url):
            uri = f'{self.site_url}/{uri}'
        response = method(uri, *args, **kwargs)
        response.raise_for_status()
        logger.debug(f'GOT {len(response.content)}B {response.headers["Content-Type"].split(";")[0]} in {response.elapsed}')
        return response.json()

    def get(self, *args, **kwargs):
        """Returns a GET request to the given resource"""
        return self._dispatch('get', *args, **kwargs)

    def post(self, *args, **kwargs):
        """Returns a POST request to the given resource"""
        return self._dispatch('post', *args, **kwargs)

    def tsml(self, entity, params=None):
        """
        Returns and loads the data from the named entity TSML endpoint

        :param str entity: Name of the entity to load (eg meetings/locations)
        :rtype: list
        """
        if params is None:
            params = {}
        params['action'] = f'tsml_{entity}'
        return self.get(self.api_uri, params)

    def meetings(self, **params):
        """
        Returns meeting data with the given query params

        :param dict params: Query parameters to use in GET request
        :rtype: list
        """
        data = DEFAULTS.copy()
        data.update(params, action='meetings')
        if self.nonce_uri:
            data['nonce'] = self.nonce
            return self.post(self.api_uri, data)
        return self.tsml('meetings')

    def locations(self):
        """
        Loads locations TSML endpoint data

        :rtype: list
        """
        return self.tsml('locations')

    def groups(self):
        """
        Loads groups TSML endpoint data

        :rtype: list
        """
        return self.tsml('groups')

    def regions(self):
        """
        Loads regions TSML endpoint data

        :rtype: list
        """
        return self.tsml('regions')

    def download(self, *sections, format='json'):
        """
        Downloads all the TSML endpoints meeting data to the DATA_DIR destination.

        :param tuple sections: Specific sections to download (eg meetings)
        :param str format: Which format to load the data in (eg json/csv)
        """
        if not os.path.exists(DATA_DIR):
            logger.warn(f'DATA_DIR not found, creating: {DATA_DIR}')
            os.makedirs(DATA_DIR)
        sections = self.sections if not sections else sections
        for section in sections:
            if not hasattr(self, section):
                raise ValueError(f'Section {section} not known')
            data = getattr(self, section)()
            outfile = os.path.join(DATA_DIR, f'{section}.{format}')
            json_dump(data, outfile) if format == 'json' else csv_dump(data, outfile)
            logger.info(f'Downloaded {outfile}')
