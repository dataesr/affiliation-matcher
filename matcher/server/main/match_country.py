import pycountry
import re

from matcher.server.main.my_elastic import MyElastic
from matcher.server.main.strings import normalize_text

ES_INDEX = 'country'


def get_regex_from_country_by_fields(es: MyElastic = None, index: str = '', country: str = '', fields: list = None,
                                     is_complex: bool = False):
    country = country.lower()
    results = es.search(index=index, body={'query': {'ids': {'values': [country]}}})
    regexes = []
    for field in fields:
        try:
            values = results['hits']['hits'][0]['_source'][field]
        except KeyError:
            values = []
        values = values if type(values) == list else [values]
        regexes = regexes + values
    if is_complex:
        pattern = '|'.join(['(?<![a-z])' + normalize_text(regex, remove_sep=False) + '(?![a-z])' for regex in regexes])
    else:
        pattern = '|'.join([normalize_text(regex, remove_sep=False) for regex in regexes])
    return re.compile(pattern, re.IGNORECASE | re.UNICODE) if pattern != '' else None


def get_countries_from_query(query: str = '', strategies: list = None) -> list:
    if strategies is None:
        strategies = ['info']
    countries = []
    es = MyElastic()
    query = normalize_text(query, remove_sep=False)
    for country in pycountry.countries:
        country = country.alpha_2.lower()
        keywords_regex = get_regex_from_country_by_fields(es, ES_INDEX, country, strategies, True)
        if keywords_regex is not None and re.search(keywords_regex, query):
            stop_words_regex = get_regex_from_country_by_fields(es, ES_INDEX, country, ['stop_words'], False)
            if stop_words_regex is not None and re.search(stop_words_regex, query):
                continue
            else:
                countries.append(country)
    return list(set(countries))
