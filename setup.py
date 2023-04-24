from setuptools import setup, find_packages

from pdf12step import __version__ as pkg

with open('README.md', 'r', encoding='utf-8') as fh:
    long_description = fh.read()

setup(
    name=pkg.__name__,
    version=pkg.__version__,
    author=pkg.__author__,
    author_email=pkg.__author_email__,
    url=pkg.__url__,
    license=pkg.__license__,
    license_files=('LICENSE',),
    description=pkg.__description__,
    long_description=long_description,
    long_description_content_type='text/markdown',
    python_requires='>=3.6',
    project_urls={
        'Documentation': 'https://pdf12step.readthedocs.io/',
        'Source': 'https://github.com/justquick/pdf12step',
        'Bug Tracker': 'https://github.com/justquick/pdf12step/issues',
        'Wordpress Plugin': 'https://wordpress.org/plugins/12-step-meeting-list/',
    },
    classifiers=[
        'Development Status :: 4 - Beta',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
        'Programming Language :: Python :: 3.10',
        'Programming Language :: Python :: 3.11',
        'License :: OSI Approved :: BSD License',
        'Operating System :: OS Independent',
        'Framework :: Flask',
        'Environment :: Console',
        'Topic :: Documentation :: Sphinx',
        'Topic :: Multimedia :: Graphics :: Presentation',
        'Topic :: Text Processing :: Markup :: HTML'
    ],
    package_data={
        'pdf12step': [
            'templates/*',
            'templates/assets/css/*',
            'templates/assets/img/*',
            'templates/includes/*',
            'templates/includes/sections/*',
            'tests/data/*',
        ]
    },
    packages=find_packages(),
    install_requires=[
        'requests',
        'weasyprint',
        'pyyaml',
        'Flask',
        'Flask-WeasyPrint',
        'qrcode',
        'click',
    ],
    entry_points={
        'console_scripts': [
            '12step=pdf12step.cli:cli',
        ]
    }
)
