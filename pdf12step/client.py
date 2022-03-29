import re
import requests
import os

from pdf12step.cached import cached_property
from pdf12step.config import DATA_DIR, OPTS
from pdf12step.utils import csv_dump, json_dump


DEFAULTS = {
    'mode': 'search',
    'distance': 2,
    'view': 'list',
    'distance_units': 'm',
}
NONCE_RE = re.compile('nonce":"([0-9a-fA-F]+)"')


class Client(object):
    """
    Client that makes HTTP[S] calls to the WP site and fetches the data

    :param str url: Base URL of the WP site to gather data from
    """
    sections = ('meetings',)  # 'locations', 'groups', 'regions') these arent necessary for now
    nonce_url = api_url = None

    def __init__(self, site_url, api_url, nonce_url=None):
        if not site_url:
            raise ValueError('Site URL required, please set site_url in your config')
        if not api_url:
            raise ValueError('API URL required, please set api_url in your config')
        self.site_url = site_url = site_url.rstrip('/')
        if nonce_url:
            self.nonce_url = nonce_url if nonce_url.startswith('http') else f'{site_url}/{nonce_url}'
        if api_url:
            self.api_url = api_url if api_url.startswith('http') else f'{site_url}/{api_url}'

    @cached_property
    def nonce(self):
        """
        Fetches the nonce on a base page to use in subsequent requests to the WP site
        Bypasses WP CSRF protection

        :rtype: str
        """
        response = requests.get(self.nonce_url)
        response.raise_for_status()
        content = response.content.decode()
        match = NONCE_RE.search(content, re.M)
        if match:
            return match.groups()[0]

    def _dispatch(self, method, url, *args, **kwargs):
        if not url.startswith('http'):
            url = f'{self.site_url}/{url}'
        OPTS.logger.debug(f'{method.upper()} {url} {args}')
        method = getattr(requests, method)
        response = method(url, *args, **kwargs)
        response.raise_for_status()
        OPTS.logger.debug(f'GOT {len(response.content)}B {response.headers["Content-Type"].split(";")[0]} in {response.elapsed}')
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
        return self.get(self.api_url, params)

    def meetings(self, **params):
        """
        Returns meeting data with the given query params

        :param dict params: Query parameters to use in GET request
        :rtype: list
        """
        data = DEFAULTS.copy()
        data.update(params, action='meetings')
        if self.nonce_url:
            data['nonce'] = self.nonce
            return self.post(self.api_url, data)
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

    def download(self, sections=None, format='json', data_dir=DATA_DIR, prefix=None):
        """
        Downloads all the TSML endpoints meeting data to the DATA_DIR destination.

        :param tuple sections: Specific sections to download (eg meetings)
        :param str format: Which format to load the data in (eg json/csv)
        """
        if sections is None:
            sections = self.sections
        if not os.path.exists(data_dir):
            OPTS.logger.warn(f'data dir not found, creating: {data_dir}')
            os.makedirs(data_dir)
        sections = self.sections if not sections else sections
        for section in sections:
            if not hasattr(self, section):
                raise ValueError(f'Section {section} not known')
            data = getattr(self, section)()
            fname = f'{prefix}-{section}.{format}' if prefix else f'{section}.{format}'
            outfile = os.path.join(data_dir, fname)
            json_dump(data, outfile) if format == 'json' else csv_dump(data, outfile)
            OPTS.logger.info(f'Downloaded {outfile}')
