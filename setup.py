from setuptools import setup
from matcher.server.main import __version__

with open('./README.md', 'r') as f:
    long_description = f.read()

setup(
    name='matcher',
    version=__version__,
    description='Matcher for French publications',
    long_description=long_description,
    long_description_content_type='text/markdown',
    url='https://github.com/dataesr/matcher',
    license='MIT',
    author='Eric Jeangirard, Anne L\'Hôte',
    keywords=['research', 'matching', 'publication'],
    python_requires='>=3.6',
    package_dir={'matcher': 'matcher/server/main'},
    packages=['matcher'],
    install_requires=[
        'beautifulsoup4==4.8.2',
        'elasticsearch==7.8.0',
        'elasticsearch-dsl==7.2.1',
        'Flask==1.1.1',
        'Flask-Bootstrap==3.3.7.1',
        'Flask-Testing==0.7.1',
        'Flask-WTF==0.14.2',
        'geopy==2.1.0',
        'gunicorn==20.0.4',
        'html5lib==1.0.1',
        'lxml==4.6.3',
        'pytest~=6.2.3',
        'pytest-mock==3.5.1',
        'redis==3.3.11',
        'requests==2.19.1',
        'rq==1.1.0',
        'Unidecode==1.0.22'
    ],
    classifiers=[
        # https://pypi.org/pypi?%3Aaction=list_classifiers
        'Development Status :: 3 - Alpha',
        'Framework :: Flask',
        'Framework :: Pytest',
        'Intended Audience :: Developers',
        'Intended Audience :: Education',
        'Intended Audience :: Science/Research',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
        'Topic :: Education',
        'Topic :: Scientific/Engineering',
        'Topic :: Scientific/Engineering :: Information Analysis'
    ],
    zip_safe=True
)
