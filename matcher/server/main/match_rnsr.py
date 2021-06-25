from matcher.server.main.my_elastic import MyElastic
from matcher.server.main.utils import remove_ref_index

import re

INDEX_PREFIX = 'rnsr'

def match_rnsr(query_input: str = '', year = None, strategies: list = None) -> dict:
    index_prefix = INDEX_PREFIX
    es = MyElastic()

    # if query starts with a digit that can be a reference index
    query = remove_ref_index(query_input)

    query = pre_treatment_rnsr(query)

    if strategies is None:
        strategies = [
        ['code_number', 'supervisor_acronym', 'supervisor_name', 'city'],
        ['code_number', 'supervisor_name', 'city'],
        ['code_number', 'acronym'],
        ['code_number', 'name'],
        ['code_number', 'supervisor_acronym'],
        ['code_number', 'supervisor_name'],
        ['code_number', 'city'],
        ['acronym', 'name', 'supervisor_name', 'city'],
        ['acronym', 'name', 'supervisor_acronym', 'city'],
        ['acronym', 'supervisor_acronym', 'city'],
        ['acronym', 'supervisor_name', 'city'],
        ['name', 'supervisor_acronym', 'city'],
        ['name', 'supervisor_name', 'city'],
        ['name', 'acronym', 'city'],
        ['name', 'acronym', 'supervisor_acronym'],
        ['name', 'acronym', 'supervisor_name'],
        ['acronym', 'city']
    ]
    if year:
        strategies_with_year = strategies.copy()
        for s in strategies_with_year:
            s.append('year')
        strategies = strategies_with_year + strategies
    logs = f'<h1> &#128269; {query}</h1>'
    for strategy in strategies:
        strategy_results = None
        all_hits = {}
        logs += f'<br/> - Matching strategy : {strategy}<br/>'
        for criteria in strategy:
            criteria_query = query
            if criteria == "year":
                criteria_query = year
            body = {'query': {'percolate': {'field': 'query', 'document': {'content': criteria_query}}},
                    '_source': {'includes': ['ids', 'query.match*.content.query']},
                    'highlight': {'fields': {'content': {'type': 'fvh'}}}}
            hits = es.search(index=f'{INDEX_PREFIX}_{criteria}', body=body).get('hits', []).get('hits', [])
            all_hits[criteria] = hits
            criteria_results = [hit.get('_source', {}).get('ids') for hit in hits]
            criteria_results = [item for sublist in criteria_results for item in sublist]
            criteria_results = list(set(criteria_results))
            if strategy_results is None:
                strategy_results = criteria_results
            else:
                # Intersection
                strategy_results = [result for result in strategy_results if result in criteria_results]
            logs += f'Criteria : {criteria} : {len(criteria_results)} matches <br/>'
        logs += f'Strategy has {len(strategy_results)} possibilities that match all criteria<br/>'
        # Strategies stopped as soon as a first result is met
        all_highlights = {}
        if len(strategy_results) > 0:
            logs += f'<hr>Results: {strategy_results}'

            for matching_criteria in all_hits:
                for hit in all_hits[matching_criteria]:
                    matching_ids = list(set(hit['_source']['ids']) & set(strategy_results))
                    for matching_id in matching_ids:
                        if matching_id not in all_highlights:
                            all_highlights[matching_id] = {}
                        all_highlights[matching_id][matching_criteria] = hit['highlight']['content']

            for matching_id in all_highlights:
                logs += f'<br/><hr>Explanation for {matching_id} :<br/>'
                for matching_criteria in all_highlights[matching_id]:
                    logs += f'{matching_criteria} : {all_highlights[matching_id][matching_criteria]}<br/>'
            break
    return {'results': strategy_results, 'logs': logs, 'highlights': all_highlights}

# done here rather than in synonym settings in es as they seem to cause highlight bugs
def pre_treatment_rnsr(query):
    rgx = re.compile("(?i)(unit. mixte de recherche)( |)(S)( |)([0-9])")
    return rgx.sub("umr\\3\\5", query).lower()

