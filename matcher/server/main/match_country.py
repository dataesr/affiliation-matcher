import json
import os
import re

from elasticsearch import Elasticsearch
from elasticsearch_dsl import Q, Search
from matcher.server.main.config import config
from matcher.server.main.strings import normalize_text

ES_INDEX = 'country'
FILE_COUNTRY_KEYWORDS = 'country_keywords.json'
FILE_COUNTRY_FORBIDDEN = 'country_forbidden.json'

def construct_keywords_regex(es: Elasticsearch = None, index: str = '', country: str = ''):
    search = Search(using=es, index=index).query('bool', must=[Q('match', category='keyword'),
                                                               Q('match', country=country.lower())])[0:10000]
    regexes = [hit.regex for hit in search]
    pattern = '|'.join(['(?<![a-z])' + regex + '(?![a-z])' for regex in regexes])
    return re.compile(pattern) if pattern != '' else None


def construct_forbidden_regex(es: Elasticsearch = None, index: str = '', country: str = ''):
    search = Search(using=es, index=index).query('bool', must=[Q('match', category='forbidden'),
                                                               Q('match', country=country.lower())])[0:10000]
    regexes = [hit.regex for hit in search]
    pattern = '|'.join([regex for regex in regexes])
    return re.compile(pattern) if pattern != '' else None


es = Elasticsearch(config['ELASTICSEARCH_HOST'])
dirname = os.path.dirname(__file__)
with open(os.path.join(dirname, FILE_COUNTRY_KEYWORDS), 'r') as file:
    country_keywords = json.load(file)

with open(os.path.join(dirname, FILE_COUNTRY_FORBIDDEN), 'r') as file:
    country_keywords_forbidden = json.load(file)

country_regex = {}
country_regex_forbidden = {}
for country in country_keywords:
    country_regex[country] = construct_keywords_regex(es, ES_INDEX, country)

for country in country_keywords_forbidden:
    country_regex_forbidden[country] = construct_forbidden_regex(es, ES_INDEX, country)


def get_countries_from_query(query: str = '') -> list:
    countries = []
    query = normalize_text(query, remove_sep=False)
    for country in country_keywords:
        if country_regex[country] is None or re.search(country_regex[country], query):
            if country in country_regex_forbidden and re.search(country_regex_forbidden[country], query):
                continue
            countries.append(country.upper())
    return list(set(countries))
