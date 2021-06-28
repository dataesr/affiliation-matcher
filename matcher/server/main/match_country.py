from matcher.server.main.my_elastic import MyElastic


def match_country(query: str = '', strategies: list = None) -> dict:
    if strategies is None:
        strategies = [['all_names']]
    es = MyElastic()
    for strategy in strategies:
        strategy_results = None
        logs = f'Matched strategy : {strategy}<br/>'
        for criteria in strategy:
            logs += f'Criteria : {criteria}<br/>'
            body = {'query': {'percolate': {'field': 'query', 'document': {'content': query}}},
                    '_source': {'includes': ['country_alpha2']},
                    'highlight': {'fields': {'content': {'type': 'fvh'}}}}
            hits = es.search(index=criteria, body=body).get('hits', []).get('hits', [])
            highlights = [hit.get('highlight', {}).get('content') for hit in hits]
            logs += '<br /><br />'.join(['<br />'.join(highlight) for highlight in highlights]) + '<br />'
            criteria_results = [hit.get('_source', {}).get('country_alpha2') for hit in hits]
            criteria_results = [item for sublist in criteria_results for item in sublist]
            criteria_results = list(set(criteria_results))
            if strategy_results is None:
                strategy_results = criteria_results
            else:
                # Intersection
                strategy_results = [result for result in strategy_results if result in criteria_results]
        # Strategies stopped as soon as a first result is met
        if len(strategy_results) > 0:
            return {'results': strategy_results, 'logs': logs}
    return {'results': [], 'logs': 'No results found'}
