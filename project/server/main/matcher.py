import itertools

from bs4 import BeautifulSoup

from project.server.main.elastic_utils import get_index_name
from project.server.main.logger import get_logger
from project.server.main.my_elastic import MyElastic
from project.server.main.utils import remove_stop

logger = get_logger(__name__)


def identity(x: str = '') -> str:
    return x


def get_highlights_length_by_grid(highlights: dict) -> int:
    values = list(highlights.values())
    values_flat = [j for sub in values for i in sub for j in i]
    all_highlights = ' '.join(values_flat)
    return len(set(BeautifulSoup(all_highlights, 'lxml').find_all('em')))


def filter_submatching_results_by_all(res: dict) -> dict:
    highlights = res['highlights']
    logs = res['logs']
    results = res['results']
    if len(results) == 0:
        return res
    ids_to_remove = []
    matching_ids = list(highlights.keys())
    # Create all combinaisons of 2 ids among the matching_ids
    all_id_combinations = itertools.combinations(matching_ids, 2)
    for (id1, id2) in all_id_combinations:
        highlights_length_01 = get_highlights_length_by_grid(highlights=highlights[id1])
        highlights_length_02 = get_highlights_length_by_grid(highlights=highlights[id2])
        if highlights_length_01 < highlights_length_02:
            ids_to_remove.append(id1)
        elif highlights_length_02 < highlights_length_01:
            ids_to_remove.append(id2)
    new_results = [result for result in results if result not in ids_to_remove]
    return {'highlights': {k: v for k, v in highlights.items() if k in new_results}, 'logs': logs,
            'results': new_results}


def filter_submatching_results_by_criterion(res: dict) -> dict:
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
        is_inf_or_equal_1, is_inf_or_equal_2, is_strict_inf_1, is_strict_inf_2 = True, True, False, False
        for criterion in criteria:
            matching_elements_1 = set(BeautifulSoup(str(highlights[id1].get(criterion, '')), 'lxml').find_all('em'))
            matching_elements_2 = set(BeautifulSoup(str(highlights[id2].get(criterion, '')), 'lxml').find_all('em'))
            is_inf_or_equal_1 = is_inf_or_equal_1 and matching_elements_1 <= matching_elements_2
            is_inf_or_equal_2 = is_inf_or_equal_2 and matching_elements_2 <= matching_elements_1
            is_strict_inf_1 = is_strict_inf_1 or matching_elements_1 < matching_elements_2
            is_strict_inf_2 = is_strict_inf_2 or matching_elements_2 < matching_elements_1
        if is_inf_or_equal_1 and is_strict_inf_1:
            ids_to_remove.append(id1)
        if is_inf_or_equal_2 and is_strict_inf_2:
            ids_to_remove.append(id2)
    new_results = [result for result in results if result not in ids_to_remove]
    return {'highlights': {k: v for k, v in highlights.items() if k in new_results}, 'logs': logs,
            'results': new_results}


class Matcher:
    def __init__(self) -> None:
        self.es = MyElastic()

    def match(self, method: str = None, conditions: dict = None, strategies: list = None, pre_treatment_query=None,
              field: str = 'ids', stopwords_strategies: dict = None, post_treatment_results=None) -> dict:
        if conditions is None:
            conditions = {}
        if pre_treatment_query is None:
            pre_treatment_query = identity
        if stopwords_strategies is None:
            stopwords_strategies = {}
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
                    if criterion in stopwords_strategies:
                        stopwords = stopwords_strategies[criterion]
                        criterion_query = remove_stop(criterion_query, stopwords)
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
                logs += f'Equivalent strategies have {len(equivalent_strategies_results)} possibilities that match ' \
                        f'one of the strategy<br/>'
            # Strategies stopped as soon as a first result is met for an equivalent_strategies
            all_highlights = {}
            if len(equivalent_strategies_results) > 0:
                logs += '<hr>Results: '
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
                if post_treatment_results:
                    equivalent_strategies_results = post_treatment_results(equivalent_strategies_results, self.es,
                                                                           index_prefix)
                final_res = {'results': equivalent_strategies_results, 'highlights': all_highlights, 'logs': logs}
                final_res = filter_submatching_results_by_criterion(final_res)
                final_res = filter_submatching_results_by_all(final_res)
                for result in final_res['results']:
                    if method == 'grid':
                        logs += f' <a target="_blank" href="https://grid.ac/institutes/' \
                                f'{result}">{result}</a>'
                    elif method == 'ror':
                        logs += f' <a target="_blank" href="https://ror.org/{result}">' \
                                f'{result}</a>'
                    elif method == 'rnsr':
                        logs += f' <a target="_blank" href="https://appliweb.dgri.education.fr/rnsr/' \
                                f'PresenteStruct.jsp?numNatStruct={result}&PUBLIC=OK">' \
                                f'{result}</a>'
                    else:
                        logs += f' {result}'
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
