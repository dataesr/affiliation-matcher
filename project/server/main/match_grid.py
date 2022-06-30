from project.server.main.matcher import Matcher
from project.server.main.utils import ENGLISH_STOP, FRENCH_STOP, remove_ref_index

DEFAULT_STRATEGIES_GRID = [
    [['grid_id'], ['ror_id']],
    [['grid_name', 'grid_acronym', 'grid_city', 'grid_country'],
     ['grid_name', 'grid_acronym', 'grid_city', 'grid_country_code']],
    [['grid_name', 'grid_city', 'grid_country'], ['grid_name', 'grid_city', 'grid_country_code']],
    [['grid_acronym', 'grid_city', 'grid_country'], ['grid_acronym', 'grid_city', 'grid_country_code']],
    [['grid_name', 'grid_acronym', 'grid_city'], ['grid_name', 'grid_acronym', 'grid_country'],
     ['grid_name', 'grid_acronym', 'grid_country_code']],
    [['grid_name', 'grid_city']]
]

# Adding extra strategies with grid_cities_by_region instead of grid_city
extended_strategies = []
for s in DEFAULT_STRATEGIES_GRID:
    current_extented_s = []
    for equiv_strategy in s:
        current_extented_s.append(equiv_strategy)
        if 'grid_city' in equiv_strategy:
            current_extented_s.append([c if c != 'grid_city' else 'grid_cities_by_region' for c in equiv_strategy])
        extended_strategies.append(current_extented_s)
DEFAULT_STRATEGIES_GRID = extended_strategies

STOPWORDS_STRATEGIES = {'grid_name': ENGLISH_STOP + FRENCH_STOP}


def get_ancestors(query: str, es, index_prefix: str) -> list:
    index = f'{index_prefix}_grid_parent'
    body = {'query': {'query_string': {'query': query}}, '_source': {'includes': ['query']}}
    hits = es.search(index=index, body=body).get('hits', {}).get('hits', [])
    parents = [hit.get('_source', {}).get('query', {}).get('match_phrase', {}).get('content', {}).get('query')
               for hit in hits]
    ancestors = parents
    for parent in parents:
        ancestors += get_ancestors(query=parent, es=es, index_prefix=index_prefix)
    return list(set(ancestors))


def remove_ancestors(grids: list, es, index_prefix: str) -> list:
    grids_copy = grids.copy()
    for grid in grids:
        ancestors = get_ancestors(query=grid, es=es, index_prefix=index_prefix)
        grids_copy = list(set(grids_copy) - set(ancestors))
    return grids_copy


def match_grid(conditions: dict) -> dict:
    strategies = conditions.get('strategies')
    if strategies is None:
        strategies = DEFAULT_STRATEGIES_GRID
    matcher = Matcher()
    return matcher.match(
        field='grids',
        conditions=conditions,
        strategies=strategies,
        pre_treatment_query=remove_ref_index,
        stopwords_strategies=STOPWORDS_STRATEGIES,
        post_treatment_results=remove_ancestors
    )
