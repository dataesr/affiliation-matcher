import json
import os
import re

from matcher.server.main.my_elastic import MyElastic
from matcher.server.main.utils import normalize_text

ES_INDEX = 'country'
FILE_COUNTRY_FORBIDDEN = 'country_forbidden.json'


def remove_forbidden_countries(countries: list = None, query: str = '') -> list:
    if countries is None:
        countries = []
    dirname = os.path.dirname(__file__)
    with open(os.path.join(dirname, FILE_COUNTRY_FORBIDDEN), 'r') as file:
        country_forbidden_words = json.load(file)
    for country in countries:
        alpha_2 = country['alpha_2']
        if alpha_2 in country_forbidden_words.keys():
            forbidden_words_regex = ' || '.join(country_forbidden_words[alpha_2])
            if re.search(forbidden_words_regex, normalize_text(text=query, remove_separator=False)):
                countries.remove(country)
    return countries


def get_countries_from_query(query: str = '', strategies: list = None, index: str = ES_INDEX) -> list:
    if strategies is None:
        strategies = [['all_names']]
    es = MyElastic()
    for strategy in strategies:
        strategy_results = None
        for criteria in strategy:
            body = {'query': {'match': {criteria: query}}, '_source': {'includes': ['alpha_2', 'name']},
                    'highlight': {'fields': {criteria: {}}}}
            hits = es.search(index=index, body=body).get('hits', []).get('hits', [])
            criteria_results = [{'alpha_2': hit.get('_source', {}).get('alpha_2').lower(),
                                 'name': hit.get('_source', {}).get('name')} for hit in hits]
            if strategy_results is None:
                strategy_results = criteria_results
            else:
                # Intersection
                strategy_results = [result for result in strategy_results if result in criteria_results]
        # Strategies stopped as soon as a first result is met
        if len(strategy_results) > 0:
            results = remove_forbidden_countries(countries=strategy_results, query=query)
            return results
    return []
