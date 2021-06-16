from matcher.server.main.my_elastic import MyElastic
from matcher.server.main.utils import normalize_text

ES_INDEX = 'country'


def get_countries_from_query(query: str = '', strategies: list = None, index: str = ES_INDEX) -> list:
    if strategies is None:
        strategies = [['names']]
    es = MyElastic()
    normalized_query = normalize_text(query, remove_separator=False)
    for strategy in strategies:
        strategy_results = None
        for criteria in strategy:
            body = {'query': {'match': {criteria: normalized_query}}, '_source': {'includes': ['alpha_2']},
                    'highlight': {'fields': {criteria: {}}}}
            hits = es.search(index=index, body=body).get('hits', []).get('hits', [])
            criteria_results = [hit.get('_source', {}).get('alpha_2').lower() for hit in hits]
            if strategy_results is None:
                strategy_results = criteria_results
            else:
                # Union
                strategy_results = list(set(strategy_results) & set(criteria_results))
        # Strategies stopped as soon as a first result is met
        if len(strategy_results) > 0:
            return strategy_results
    return []
