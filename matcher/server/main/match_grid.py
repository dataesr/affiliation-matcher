from matcher.server.main.matcher import Matcher
from matcher.server.main.utils import ENGLISH_STOP, remove_ref_index

DEFAULT_STRATEGIES = [
    [['grid_name', 'grid_acronym', 'grid_city', 'grid_country'],
     ['grid_name', 'grid_acronym', 'grid_city', 'grid_country_code']],
    [['grid_name', 'grid_city', 'grid_country'], ['grid_name', 'grid_city', 'grid_country_code']],
    [['grid_acronym', 'grid_city', 'grid_country'], ['grid_acronym', 'grid_city', 'grid_country_code']],
    [['grid_name', 'grid_acronym', 'grid_city'], ['grid_name', 'grid_acronym', 'grid_country'],
     ['grid_name', 'grid_acronym', 'grid_country_code']],
    [['grid_name', 'grid_city']]
]
STOPWORDS_STRATEGIES = {'grid_name': ENGLISH_STOP}


def get_ancestors(grid: str, es, index_prefix: str) -> list:
    index = f'{index_prefix}_grid_parent'
    body = {'query': {'query_string': {'query': grid}}, '_source': {'includes': ['query']}}
    hits = es.search(index=index, body=body).get('hits', []).get('hits', [])
    parents = [hit.get('_source', {}).get('query', {}).get('match_phrase', {}).get('content', {}).get('query')
               for hit in hits]
    ancestors = parents
    for parent in parents:
        ancestors += get_ancestors(grid=parent, es=es, index_prefix=index_prefix)
    ancestors = list(set(ancestors))
    return ancestors


def remove_ancestors(grids: list, es, index_prefix: str) -> list:
    grids_copy = grids.copy()
    for grid in grids:
        ancestors = get_ancestors(grid=grid, es=es, index_prefix=index_prefix)
        grids_copy = list(set(grids_copy) - set(ancestors))
    return grids_copy


def match_grid(conditions: dict) -> dict:
    strategies = conditions.get('strategies')
    if strategies is None:
        strategies = DEFAULT_STRATEGIES
    matcher = Matcher()
    return matcher.match(method='grid', conditions=conditions, strategies=strategies,
                         pre_treatment_query=remove_ref_index, stopwords_strategies=STOPWORDS_STRATEGIES,
                         post_treatment_results=remove_ancestors)
