import json
import os
import re

from matcher.server.main.strings import normalize_text

FILE_COUNTRY_KEYWORDS = 'country_keywords.json'
FILE_COUNTRY_FORBIDDEN = 'country_forbidden.json'


def construct_regex(regexes: list = None):
    pattern = '|'.join(['(?<![a-z])' + regex + '(?![a-z])' for regex in regexes])
    return re.compile(pattern)


def construct_regex_simple(regexes: list = None):
    pattern = '|'.join([regex for regex in regexes])
    return re.compile(pattern)


dirname = os.path.dirname(__file__)
with open(os.path.join(dirname, FILE_COUNTRY_KEYWORDS), 'r') as file:
    country_keywords = json.load(file)

with open(os.path.join(dirname, FILE_COUNTRY_FORBIDDEN), 'r') as file:
    country_keywords_forbidden = json.load(file)

country_regex = {}
country_regex_forbidden = {}
for country in country_keywords:
    country_regex[country] = construct_regex(country_keywords[country])

for country in country_keywords_forbidden:
    country_regex_forbidden[country] = construct_regex_simple(country_keywords_forbidden[country])


def get_countries_from_query(query) -> list:
    countries = []
    query = normalize_text(query, remove_sep=False)
    for country in country_keywords:
        if re.search(country_regex[country], query):
            if country in country_regex_forbidden and re.search(country_regex_forbidden[country], query):
                continue
            countries.append(country.upper())
    return list(set(countries))
