import re

from matcher.server.main.my_elastic import MyElastic
from matcher.server.main.utils import remove_ref_index

DEFAULT_STRATEGIES = [
    ['rnsr_code_number', 'rnsr_supervisor_acronym', 'rnsr_supervisor_name', 'rnsr_city'],
    ['rnsr_code_number', 'rnsr_supervisor_name', 'rnsr_city'],
    ['rnsr_code_number', 'rnsr_acronym'],
    ['rnsr_code_number', 'rnsr_name'],
    ['rnsr_code_number', 'rnsr_supervisor_acronym'],
    ['rnsr_code_number', 'rnsr_supervisor_name'],
    ['rnsr_code_number', 'rnsr_city'],
    ['rnsr_acronym', 'rnsr_name', 'rnsr_supervisor_name', 'rnsr_city'],
    ['rnsr_acronym', 'rnsr_name', 'rnsr_supervisor_acronym', 'rnsr_city'],
    ['rnsr_acronym', 'rnsr_supervisor_acronym', 'rnsr_city'],
    ['rnsr_acronym', 'rnsr_supervisor_name', 'rnsr_city'],
    ['rnsr_name', 'rnsr_supervisor_acronym', 'rnsr_city'],
    ['rnsr_name', 'rnsr_supervisor_name', 'rnsr_city'],
    ['rnsr_name', 'rnsr_acronym', 'rnsr_city'],
    ['rnsr_name', 'rnsr_acronym', 'rnsr_supervisor_acronym'],
    ['rnsr_name', 'rnsr_acronym', 'rnsr_supervisor_name'],
    ['rnsr_acronym', 'rnsr_city']
]


def match_rnsr(query: str = '', strategies: list = None, year: str = None) -> dict:
    es = MyElastic()
    if strategies is None:
        strategies = DEFAULT_STRATEGIES
    if year:
        strategies_with_year = [strategy.append('rnsr_year') for strategy in strategies.copy()]
        strategies = strategies_with_year + strategies
    logs = f'<h1> &#128269; {query}</h1>'
    for strategy in strategies:
        strategy_results = None
        all_hits = {}
        logs += f'<br/> - Matching strategy : {strategy}<br/>'
        for criterion in strategy:
            criterion_query = year if criterion == 'rnsr_year' else pre_treatment_rnsr(query)
            body = {'query': {'percolate': {'field': 'query', 'document': {'content': criterion_query}}},
                    '_source': {'includes': ['ids', 'query.match*.content.query']},
                    'highlight': {'fields': {'content': {'type': 'fvh'}}}}
            hits = es.search(index=criterion, body=body).get('hits', []).get('hits', [])
            all_hits[criterion] = hits
            criteria_results = [hit.get('_source', {}).get('ids', []) for hit in hits]
            criteria_results = [item for sublist in criteria_results for item in sublist]
            criteria_results = list(set(criteria_results))
            if strategy_results is None:
                strategy_results = criteria_results
            else:
                # Intersection
                strategy_results = [result for result in strategy_results if result in criteria_results]
            logs += f'Criteria : {criterion} : {len(criteria_results)} matches <br/>'
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
                        all_highlights[matching_id][matching_criteria] = hit.get('highlight', {}).get('content', [])
            for matching_id in all_highlights:
                logs += f'<br/><hr>Explanation for {matching_id} :<br/>'
                for matching_criteria in all_highlights[matching_id]:
                    logs += f'{matching_criteria} : {all_highlights[matching_id][matching_criteria]}<br/>'
            return {'results': strategy_results, 'logs': logs, 'highlights': all_highlights}
    return {'results': [], 'logs': 'No results found', 'highlights': {}}


# done here rather than in synonym settings in ES as they seem to cause highlight bugs
def pre_treatment_rnsr(query: str = '') -> str:
    # if query starts with a digit that can be a reference index
    query = remove_ref_index(query)
    rgx = re.compile("(?i)(unit. mixte de recherche)( |)(S)( |)([0-9])")
    return rgx.sub("umr\\3\\5", query).lower()
