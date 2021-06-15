import re

import pycountry

from matcher.server.main.my_elastic import MyElastic
from matcher.server.main.utils import normalize_text

ES_INDEX = 'country'


def get_regex_from_country_by_fields(es: MyElastic = None, index: str = '', country: str = '', fields: list = None,
                                     is_complex: bool = False):
    country = country.lower()
    results = es.search(index=index, body={'query': {'match': {'alpha_2': country}}})
    regexes = []
    for field in fields:
        try:
            values = results['hits']['hits'][0]['_source'][field]
        except (KeyError, IndexError):
            values = []
        values = values if type(values) == list else [values]
        regexes = regexes + values
    if is_complex:
        pattern = '|'.join(
            ['(?<![a-z])' + normalize_text(regex, remove_separator=False) + '(?![a-z])' for regex in regexes])
    else:
        pattern = '|'.join([normalize_text(regex, remove_separator=False) for regex in regexes])
    return re.compile(pattern, re.IGNORECASE | re.UNICODE) if pattern != '' else None


def get_countries_from_query(query: str = '', criteria: list = None) -> list:
    if criteria is None:
        criteria = ['names']
    countries = []
    es = MyElastic()
    query = normalize_text(query, remove_separator=False)
    for country in pycountry.countries:
        is_country_matched = True
        country = country.alpha_2.lower()
        for criterion in criteria:
            keywords_regex = get_regex_from_country_by_fields(es, ES_INDEX, country, [criterion], True)
            is_country_matched = is_country_matched and keywords_regex and bool(re.search(keywords_regex, query))
        stop_words_regex = get_regex_from_country_by_fields(es, ES_INDEX, country, ['stop_words'], False)
        if stop_words_regex and re.search(stop_words_regex, query):
            continue
        if is_country_matched:
            countries.append(country)
    return list(set(countries))
