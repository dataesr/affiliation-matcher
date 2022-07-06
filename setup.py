from setuptools import find_packages, setup

from project import __version__

with open('./README.md', 'r') as f:
    long_description = f.read()

setup(
    name='affiliation-matcher',
    version=__version__,
    description='Matcher for affiliations',
    long_description=long_description,
    long_description_content_type='text/markdown',
    url='https://github.com/dataesr/affiliation-matcher',
    license='MIT',
    author='Eric Jeangirard, Anne L\'Hôte',
    author_email='eric.jeangirard@recherche.gouv.fr, anne.lhote@enseignementsup.gouv.fr',
    keywords=['research', 'matching', 'affiliation'],
    python_requires='>=3.6',
    packages=find_packages(),
    package_data={'': ['*.json']},
    test_suite='pytest',
    install_requires=[
        'beautifulsoup4==4.8.2',
        'elasticsearch==7.8.0',
        'elasticsearch-dsl==7.2.1',
        'Flask==1.1.1',
        'Flask-Bootstrap==3.3.7.1',
        'geopy==2.1.0',
        'lxml==4.9.1',
        'pandas==0.25.3',
        'pycountry==20.7.3',
        'redis==3.3.11',
        'requests==2.20.0',
        'rq==1.1.0',
        'xlrd==1.1.0',
        'XlsxWriter==1.0.4'
    ],
    tests_require=[
        'pytest==6.2.3',
        'pytest-mock==3.5.1',
        'requests-mock==1.9.2'
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
