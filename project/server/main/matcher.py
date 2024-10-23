import requests
import itertools
from fuzzywuzzy import fuzz

from bs4 import BeautifulSoup

from project import __version__
from project.server.main.elastic_utils import get_index_name
from project.server.main.logger import get_logger
from project.server.main.my_elastic import MyElastic
from project.server.main.utils import remove_stop, normalize_text
from project.server.main.load_rnsr import get_siren
from project.server.main.load_paysage import PAYSAGE_API_URL, PAYSAGE_API_KEY, CATEGORIES

logger = get_logger(__name__)

correspondance = get_siren()

def identity(x: str = '') -> str:
    return x

def check_similarity(str1, str2, pre_treatment_query, threshold = 0.8):
    logs=''
    x1 = pre_treatment_query(normalize_text(text = str1, remove_separator = False, re_order = True, to_lower = True))
    x2 = pre_treatment_query(normalize_text(text = str2, remove_separator = False, re_order = True, to_lower = True))
    r = (fuzz.ratio(x1, x2))/100.0
    if r < threshold:
        logger.debug(f'reject {str1} {str2} match as ratio = {r} < {threshold}')
        return False
    logger.debug(f'accept {str1} {str2} match as ratio = {r} >= {threshold} !')
    return True

def get_highlights_length_by_match(highlights: dict):
    criteria_per_token = {}
    nb_criteria_per_token = {}
    for criterion in highlights:
        values = highlights[criterion]
        all_highlights = ' '.join(values[0])
        matching_tokens = list(set(BeautifulSoup(all_highlights, 'lxml').find_all('em')))
        for m in matching_tokens:
            current_token = m.get_text()
            if current_token not in criteria_per_token:
                criteria_per_token[current_token] = []
            criteria_per_token[current_token].append(criterion)
    for current_token in criteria_per_token:
        criteria_per_token[current_token] = list(set(criteria_per_token[current_token]))
        nb_criteria_per_token[current_token] = len(criteria_per_token[current_token])
    if len(list(nb_criteria_per_token.values())) > 0:
        max_nb_criteria = max(list(nb_criteria_per_token.values()))
        min_nb_criteria = min(list(nb_criteria_per_token.values()))
    else:
        max_nb_criteria = 1
        min_nb_criteria = 1
    return {
        'max': max_nb_criteria,
        'min': min_nb_criteria,
        'token_with_max': [
            {t: criteria_per_token[t]} for t in nb_criteria_per_token if nb_criteria_per_token[t] == max_nb_criteria
        ]
    }


def filter_submatching_results_by_criterion(res: dict, conditions) -> dict:
    logs = res.get('logs')
    results = res.get('results')
    version = res.get('version')
    index_date = res.get('index_date')
    if len(results) == 0:
        return res
    ids_to_remove = []
    for strategy in res['highlights']:
        highlights = res['highlights'][strategy]
        matching_ids = list(highlights.keys())
        if len(matching_ids) < 1:
            logger.debug(f'SHOULD NOT HAPPEN ? not highlights but results {results} in strategy {strategy} for {conditions}')
            continue
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
                logs += f"<br>filter_submatching_results_by_criterion - Remove id1 {id1} because {matching_elements_2} better than {matching_elements_1}"
                ids_to_remove.append(id1)
            if is_inf_or_equal_2 and is_strict_inf_2:
                logs += f"<br>filter_submatching_results_by_criterion - Remove id2 {id2} because {matching_elements_1} better than {matching_elements_2}"
                ids_to_remove.append(id2)
    new_results = [result for result in results if result not in ids_to_remove]
    new_highlights = {}
    for strategy in res['highlights']:
        current_highlights = res['highlights'][strategy]
        new_highlights[strategy] = {k: v for k, v in current_highlights.items() if k in new_results}
    return {
        "highlights": new_highlights,
        "logs": logs,
        "debug": res.get("debug"),
        "results": new_results,
        "version": version,
        "index_date": index_date,
    }


def filter_submatching_results_by_all(res: dict, conditions) -> dict:
    logs = res.get('logs')
    results = res.get('results')
    version = res.get('version')
    index_date = res.get('index_date')
    if len(results) == 0:
        return res
    ids_to_remove = []
    for strategy in res['highlights']:
        highlights = res['highlights'][strategy]
        matching_ids = list(highlights.keys())
        # Create all combinaisons of 2 ids among the matching_ids
        all_id_combinations = itertools.combinations(matching_ids, 2)
        for (id1, id2) in all_id_combinations:
            highlights_length_01 = get_highlights_length_by_match(highlights=highlights[id1])
            highlights_length_02 = get_highlights_length_by_match(highlights=highlights[id2])
            max_1 = highlights_length_01['max']
            max_2 = highlights_length_02['max']
            if max_2 > max_1:
                logs += f"<br>filter_submatching_results_by_all - remove id1 {id1} because {highlights_length_02} better than {highlights_length_01}"
                ids_to_remove.append(id1)
            elif max_1 > max_2:
                logs += f"<br>filter_submatching_results_by_all - remove id1 {id2} because {highlights_length_01} better than {highlights_length_02}"
                ids_to_remove.append(id2)
    new_results = [result for result in results if result not in ids_to_remove]
    new_highlights = {}
    for strategy in res['highlights']:
        current_highlights = res['highlights'][strategy]
        new_highlights[strategy] = {k: v for k, v in current_highlights.items() if k in new_results}
    return {
        "highlights": new_highlights,
        "logs": logs,
        "debug": res.get("debug"),
        "results": new_results,
        "version": version,
        "index_date": index_date,
    }


def clean_highlights(highlights: dict):
    new_highlights = {}
    for strategy in highlights:
        for match_id in highlights[strategy]:
            if match_id not in new_highlights:
                new_highlights[match_id] = {"criterion": {}, "strategies": []}
            if strategy not in new_highlights[match_id]["strategies"]:
                new_highlights[match_id]["strategies"].append(strategy.split(";"))
            for criteria in highlights[strategy][match_id]:
                if criteria not in new_highlights[match_id]["criterion"]:
                    new_highlights[match_id]["criterion"][criteria] = []
                    for highlight in highlights[strategy][match_id][criteria]:
                        highlight = " ".join(highlight)
                        logger.debug(f"highlight: {highlight}")
                        new_highlights[match_id]["criterion"][criteria].append(
                            list(set([tag.text for tag in BeautifulSoup(highlight, "lxml").find_all("em")]))
                        )
    return new_highlights


class Matcher:
    def __init__(self) -> None:
        self.es = MyElastic()

    def enrich_results(self, results, method):
        enriched = []
        for r in results:
            elt = {"id": r}
            for f in ["name", "city", "acronym", "country"]:
                index = f"matcher_{method}_{f}"
                try:
                    data = self.es.search(index=index, body={"query": {"simple_query_string": {"query": r}}})
                    hits = data["hits"]["hits"]
                    elt[f] = []
                    for hit in hits:
                        elt[f].append(list(hit["_source"]["query"].values())[0]["content"]["query"])
                except:
                    pass

            # enrich with paysage categories
            if method == "paysage":
                try:
                    headers = {"X-API-KEY": PAYSAGE_API_KEY}
                    url = f"{PAYSAGE_API_URL}/relations?limit=100&filters[relationTag]=structure-categorie&filters[resourceId]={r}"
                    response = requests.get(url=url, headers=headers)
                    data = response.json().get("data")
                    categories = [
                        {
                            "id": d.get("relatedObjectId"),
                            "label": d.get("relatedObject", {}).get("displayName"),
                            "priority": d.get("relatedObject", {}).get("priority"),
                        }
                        for d in data
                        if d.get("relatedObjectId") in CATEGORIES
                    ]
                    elt["paysage_categories"] = categories
                except:
                    pass

            enriched.append(elt)
        return enriched

    def match(self, method: str = None, conditions: dict = None, strategies: list = None, pre_treatment_query=None,
              field: str = 'ids', stopwords_strategies: dict = None, post_treatment_results=None) -> dict:
        if conditions is None:
            conditions = {}
        if method is None:
            # ex: grids -> grid
            assert(isinstance(field, str))
            assert(field[-1] == 's')
            method = field[:-1]
        assert method in ["grid", "ror", "rnsr", "paysage", "country"]
        if pre_treatment_query is None:
            pre_treatment_query = identity
        if stopwords_strategies is None:
            stopwords_strategies = {}
        verbose = conditions.get('verbose', False)
        index_prefix = conditions.get('index_prefix', 'matcher')
        query = conditions.get('query', '')
        # logs = f'<h1> &#128269; {query}</h1>'
        logs = ""
        debug = {"criterion": {}, "strategies": []}
        logger.debug(f"method {method}")
        logger.debug(f"query {query}")
        # to limit the nb of ES requests
        # avoid call ES if a search on the same criterion has been done for a strategy before
        cache = {}
        index_date = None
        for equivalent_strategies in strategies:
            equivalent_strategies_results = None
            equivalent_strategies_matches = []
            all_hits = {}
            # logs += f'<br/> - Matching equivalent strategies : {equivalent_strategies}<br/>'
            for strategy in equivalent_strategies:
                strategy_results = None
                for criterion in strategy:
                    # TODO : remove index_prefix
                    criterion_without_source = '_'.join(criterion.split('_')[1:])
                    if criterion_without_source in conditions:
                        criterion_query = pre_treatment_query(conditions[criterion_without_source])
                    else:
                        criterion_query = pre_treatment_query(query)
                    if criterion in stopwords_strategies:
                        stopwords = stopwords_strategies[criterion]
                        criterion_query = remove_stop(criterion_query, stopwords)
                    index = get_index_name(index_name=criterion, source='', index_prefix=index_prefix)
                    cache_key = f'{index};{field};{criterion_query}'
                    if cache_key in cache:
                        hits = cache[cache_key]
                    else:
                        body = {
                            'query': {'percolate': {'field': 'query', 'document': {'content': criterion_query}}},
                            '_source': {'includes': [field]},
                            'highlight': {'fields': {'content': {'type': 'unified'}}}
                        }
                        hits = self.es.search(index=index, body=body).get('hits', []).get('hits', [])
                        if hits and (not index_date):
                            index_date = hits[0]['_index'].replace('matcher-', '').split('_')[0][0:8]
                        cache[cache_key] = hits
                    strategy_label = ';'.join(strategy)
                    if strategy_label not in all_hits:
                        all_hits[strategy_label] = {}
                    all_hits[strategy_label][criterion] = hits
                    criteria_results = [hit.get('_source', {}).get(field) for hit in hits]
                    criteria_results_flatten = []
                    for sublist in criteria_results:
                        if isinstance(sublist, list):
                            for item in sublist:
                                if item:
                                    criteria_results_flatten.append(item)
                    # criteria_results = [item for sublist in criteria_results for item in sublist]
                    criteria_results = list(set(criteria_results_flatten))
                    if strategy_results is None:
                        strategy_results = criteria_results
                    else:
                        # Intersection
                        strategy_results = [result for result in strategy_results if result in criteria_results]
                    # logs += f'Criteria : {criterion} : {len(criteria_results)} matches <br/>'
                    debug["criterion"][criterion] = len(criteria_results)
                equivalent_strategies_matches.append(len(strategy_results))
                if equivalent_strategies_results is None:
                    equivalent_strategies_results = strategy_results
                else:
                    # Union
                    equivalent_strategies_results += strategy_results
                    # Remove duplicates
                    equivalent_strategies_results = list(set(equivalent_strategies_results))
                # logs += f'Strategy : {strategy} : {len(strategy_results)} matches <br/>'
                # logs += f'Equivalent strategies have {len(equivalent_strategies_results)} possibilities that match ' \
                # f'one of the strategy<br/>'
            debug["strategies"].append(
                {
                    "equivalent_strategies": [
                        {"criteria": es, "matches": equivalent_strategies_matches[index]}
                        for index, es in enumerate(equivalent_strategies)
                    ],
                    "possibilities": len(equivalent_strategies_results),
                }
            )
            # Strategies stopped as soon as a first result is met for an equivalent_strategies
            all_highlights = {}
            if len(equivalent_strategies_results) > 0:
                for strategy in all_hits:
                    all_highlights[strategy] = {}
                    for matching_criteria in all_hits[strategy]:
                        for hit in all_hits[strategy][matching_criteria]:
                            matching_ids = list(set(hit['_source'][field]) & set(equivalent_strategies_results))
                            for matching_id in matching_ids:
                                if matching_id not in all_highlights[strategy]:
                                    all_highlights[strategy][matching_id] = {}
                                if matching_criteria not in all_highlights[strategy][matching_id]:
                                    all_highlights[strategy][matching_id][matching_criteria] = []
                                current_highlight = hit.get('highlight', {}).get('content', [])
                                if current_highlight not in all_highlights[strategy][matching_id][matching_criteria]:
                                    all_highlights[strategy][matching_id][matching_criteria].append(current_highlight)
                if post_treatment_results:
                    equivalent_strategies_results = post_treatment_results(equivalent_strategies_results, self.es,
                                                                           index_prefix)
                final_res = {
                    "highlights": all_highlights,
                    "logs": logs,
                    "debug": debug,
                    "other_ids": [],
                    "results": equivalent_strategies_results,
                    "index_date": index_date,
                    "version": __version__,
                }
                if method != "paysage":
                    final_res = filter_submatching_results_by_criterion(final_res, conditions)
                    final_res = filter_submatching_results_by_all(final_res, conditions)
                final_res['enriched_results'] = self.enrich_results(final_res['results'], method)
                if 'name' in conditions:
                    similar_results = []
                    input_name = conditions['name']
                    for potential_result in final_res['enriched_results']:
                        is_similar = False
                        potential_names = potential_result.get('name')
                        if not isinstance(potential_names, list):
                            potential_names = []
                        for name in potential_names:
                            current_similar = check_similarity(name, input_name, pre_treatment_query, 0.8)
                            if current_similar:
                                is_similar = True
                                similar_results.append(potential_result['id'])
                                break
                        if is_similar is False:
                            final_res['logs'] += f"<br> removing potential_result['id'] as names potential_result['name'] not similar enough to input name {input_name}"
                    final_res['results'] = similar_results
                    final_res['enriched_results'] = self.enrich_results(final_res['results'], method)
                logs = final_res['logs']
                other_ids = []
                # logs += '<br><hr>Results: '
                for result in final_res['results']:
                    if result in correspondance:
                        for e in correspondance[result]:
                            if e not in other_ids:
                                other_ids.append(e)
                    final_res['other_ids'] = other_ids
                    # if method == 'grid':
                    #     logs += f' <a target="_blank" href="https://grid.ac/institutes/' \
                    #             f'{result}">{result}</a>'
                    # elif method == 'ror':
                    #     logs += f' <a target="_blank" href="https://ror.org/{result}">' \
                    #             f'{result}</a>'
                    # elif method == 'rnsr':
                    #     logs += f' <a target="_blank" href="https://appliweb.dgri.education.fr/rnsr/' \
                    #             f'PresenteStruct.jsp?numNatStruct={result}&PUBLIC=OK">' \
                    #             f'{result}</a>'
                    # elif method == "paysage":
                    #     logs += (
                    #         f' <a target="_blank" href="https://paysage.staging.dataesr.ovh/structures/{result}">'
                    #         f"{result}</a>"
                    #     )
                    # else:
                    #     logs += f' {result}'
                for matching_id in final_res['highlights']:
                    logs += f'<br/><hr>Explanation for {matching_id} :<br/>'
                    for matching_criteria in final_res['highlights'][matching_id]:
                        logs += f'{matching_criteria} : {all_highlights[matching_id][matching_criteria]}<br/>'
                final_res['logs'] = logs
                if not verbose:
                    del final_res['logs']
                final_res["highlights"] = clean_highlights(final_res.get("highlights"))
                return final_res
        logs += '<br/> No results found'
        final_res = {
            'highlights': {},
            'other_ids': [],
            'results': [],
            'index_date': index_date,
            'version': __version__
        }
        if verbose:
            final_res['logs'] = logs
            final_res["debug"] = debug
        else:
            del final_res['highlights']
        final_res['enriched_results'] = self.enrich_results(final_res['results'], method)
        return final_res
