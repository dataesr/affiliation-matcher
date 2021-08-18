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
    # Create all combinaisons of 2 ids among the matching_ids
    all_id_combinations = itertools.combinations(matching_ids, 2)
    criteria_01 = highlights[matching_ids[0]].keys()
    criteria_02 = highlights[matching_ids[1]].keys() if len(matching_ids) > 1 else []
    criteria = list(set(list(criteria_01) + list(criteria_02)))
    for (id1, id2) in all_id_combinations:
        res1, res2 = True, True
        for criterion in criteria:
            matching_elements_1 = set(BeautifulSoup(str(highlights[id1].get(criterion, '')), 'lxml').find_all('em'))
            matching_elements_2 = set(BeautifulSoup(str(highlights[id2].get(criterion, '')), 'lxml').find_all('em'))
            res1 = res1 and matching_elements_1 <= matching_elements_2
            res2 = res2 and matching_elements_2 <= matching_elements_1
        if res1:
            ids_to_remove.append(id1)
        if res2:
            ids_to_remove.append(id2)
    new_results = [result for result in results if result not in ids_to_remove]
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
        for equivalent_strategies in strategies:
            equivalent_strategies_results = None
            all_hits = {}
            logs += f'<br/> - Matching equivalent strategies : {equivalent_strategies}<br/>'
            for strategy in equivalent_strategies:
                strategy_results = None
                for criterion in strategy:
                    # TODO : remove index_prefix
                    criterion_without_source = '_'.join(criterion.split('_')[1:])
                    if criterion_without_source in conditions:
                        criterion_query = conditions[criterion_without_source]
                    else:
                        criterion_query = pre_treatment_query(query)
                    body = {
                        'query': {'percolate': {'field': 'query', 'document': {'content': criterion_query}}},
                        '_source': {'includes': [field]},
                        'highlight': {'fields': {'content': {'type': 'unified'}}}
                    }
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
                if equivalent_strategies_results is None:
                    equivalent_strategies_results = strategy_results
                else:
                    # Union
                    equivalent_strategies_results += strategy_results
                    # Remove duplicates
                    equivalent_strategies_results = list(set(equivalent_strategies_results))
                logs += f'Strategy : {strategy} : {len(strategy_results)} matches <br/>'
                logs += f'Equivalent strategies has {len(equivalent_strategies_results)} possibilities that match ' \
                        f'one of the strategy<br/>'
            # Strategies stopped as soon as a first result is met for an equivalent_strategies
            all_highlights = {}
            if len(equivalent_strategies_results) > 0:
                logs += f'<hr>Results: {equivalent_strategies_results}'
                for matching_criteria in all_hits:
                    for hit in all_hits[matching_criteria]:
                        matching_ids = list(set(hit['_source'][field]) & set(equivalent_strategies_results))
                        for matching_id in matching_ids:
                            if matching_id not in all_highlights:
                                all_highlights[matching_id] = {}
                            if matching_criteria not in all_highlights[matching_id]:
                                all_highlights[matching_id][matching_criteria] = []
                            current_highlight = hit.get('highlight', {}).get('content', [])
                            if current_highlight not in all_highlights[matching_id][matching_criteria]:
                                all_highlights[matching_id][matching_criteria].append(current_highlight)
                final_res = {'results': equivalent_strategies_results, 'highlights': all_highlights, 'logs': logs}
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
