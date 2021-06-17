from matcher.server.main.my_elastic import MyElastic

ES_INDEX = 'country'


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
            return strategy_results
    return []
