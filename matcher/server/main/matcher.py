import itertools

from bs4 import BeautifulSoup

from matcher.server.main.elastic_utils import get_index_name
from matcher.server.main.logger import get_logger
from matcher.server.main.my_elastic import MyElastic

logger = get_logger(__name__)


def identity(x: str = '') -> str:
    return x


def filter_submatching_results(res: dict) -> dict:
    highlights = res['highlights']
    logs = res['logs']
    results = res['results']
    if len(results) == 0:
        return res
    ids_to_remove = []
    matching_ids = list(highlights.keys())
    all_id_combinations = itertools.combinations(matching_ids, 2)
    criteria = highlights[matching_ids[0]].keys()
    for (id1, id2) in all_id_combinations:
        for criterion in criteria:
            matching_elements_1 = BeautifulSoup(str(highlights[id1][criterion]), 'lxml').find_all('em')
            matching_elements_2 = BeautifulSoup(str(highlights[id2][criterion]), 'lxml').find_all('em')
            if set(matching_elements_1) < set(matching_elements_2):
                logs += f'<br> Removing {id1} as its {criterion} is included in the same for {id2}'
                ids_to_remove.append(id1)
            elif set(matching_elements_2) < set(matching_elements_1):
                logs += f'<br> Removing {id2} as its {criterion} is included in the same for {id1}'
                ids_to_remove.append(id2)
    new_results = [r for r in results if r not in ids_to_remove]
    return {'highlights': {k: v for k, v in highlights.items() if k in new_results}, 'logs': logs,
            'results': new_results}


class Matcher:
    def __init__(self) -> None:
        self.es = MyElastic()

    def match(self, conditions: dict, strategies: list, pre_treatment_query=None, field: str = 'ids')\
            -> dict:
        if conditions is None:
            conditions = {}
        if pre_treatment_query is None:
            pre_treatment_query = identity
        verbose = conditions.get('verbose', False)
        index_prefix = conditions.get('index_prefix', 'matcher')
        query = conditions.get('query', '')
        logs = f'<h1> &#128269; {query}</h1>'
        for strategy in strategies:
            strategy_results = None
            all_hits = {}
            logs += f'<br/> - Matching strategy : {strategy}<br/>'
            for criterion in strategy:
                criterion_without_source = '_'.join(criterion.split('_')[1:])
                if criterion_without_source in conditions:
                    criterion_query = conditions[criterion_without_source]
                else:
                    criterion_query = pre_treatment_query(query)
                body = {'query': {'percolate': {'field': 'query', 'document': {'content': criterion_query}}},
                        '_source': {'includes': [field]},
                        'highlight': {'fields': {'content': {'type': 'unified'}}}}
                index = get_index_name(index_name=criterion, source='', index_prefix=index_prefix)
                hits = self.es.search(index=index, body=body).get('hits', []).get('hits', [])
                all_hits[criterion] = hits
                criteria_results = [hit.get('_source', {}).get(field) for hit in hits]
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
                        matching_ids = list(set(hit['_source'][field]) & set(strategy_results))
                        for matching_id in matching_ids:
                            if matching_id not in all_highlights:
                                all_highlights[matching_id] = {}
                            if matching_criteria not in all_highlights[matching_id]:
                                all_highlights[matching_id][matching_criteria] = []
                            current_highlight = hit.get('highlight', {}).get('content', [])
                            if current_highlight not in all_highlights[matching_id][matching_criteria]:
                                all_highlights[matching_id][matching_criteria].append(current_highlight)
                final_res = {'results': strategy_results, 'highlights': all_highlights, 'logs': logs}
                final_res = filter_submatching_results(final_res)
                logs = final_res['logs']
                for matching_id in final_res['highlights']:
                    logs += f'<br/><hr>Explanation for {matching_id} :<br/>'
                    for matching_criteria in final_res['highlights'][matching_id]:
                        logs += f'{matching_criteria} : {all_highlights[matching_id][matching_criteria]}<br/>'
                final_res['logs'] = logs
                if not verbose:
                    del final_res['logs']
                return final_res
        logs += '<br/> No results found'
        final_res = {'results': [], 'highlights': {}}
        if verbose:
            final_res['logs'] = logs
        return final_res
