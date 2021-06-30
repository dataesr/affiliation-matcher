from matcher.server.main.matcher import Matcher
from matcher.server.main.utils import remove_ref_index


DEFAULT_STRATEGIES = [
    ['grid_name', 'grid_acronym', 'grid_city', 'grid_country'],
    ['grid_name', 'grid_city', 'grid_country'],
    ['grid_acronym', 'grid_city', 'grid_country'],
    ['grid_name', 'grid_country'],
    ['grid_name', 'grid_city']
]


def match_grid(query: str = '', strategies: list = None, country_code: str = None) -> dict:
    if strategies is None:
        strategies = DEFAULT_STRATEGIES
    condition = {'condition': 'grid_country', 'value': country_code}
    matcher = Matcher()
    return matcher.match(query=query, strategies=strategies, condition=condition, pre_treatment_query=remove_ref_index)
