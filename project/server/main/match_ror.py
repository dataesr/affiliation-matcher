from project.server.main.matcher import Matcher
from project.server.main.utils import ENGLISH_STOP, FRENCH_STOP, remove_ref_index

DEFAULT_STRATEGIES = [
    [['ror_id']],
    [['ror_grid_id']],
    [['ror_name', 'ror_acronym', 'ror_city', 'ror_country'],
     ['ror_name', 'ror_acronym', 'ror_city', 'ror_country_code']],
    [['ror_name', 'ror_city', 'ror_country'], ['ror_name', 'ror_city', 'ror_country_code']],
    [['ror_acronym', 'ror_city', 'ror_country'], ['ror_acronym', 'ror_city', 'ror_country_code']],
    [['ror_name', 'ror_acronym', 'ror_city'], ['ror_name', 'ror_acronym', 'ror_country'],
     ['ror_name', 'ror_acronym', 'ror_country_code']],
    [['ror_name', 'ror_city']],
    # group 6
    [['ror_name_unique']]
]
STOPWORDS_STRATEGIES = {'ror_name': ENGLISH_STOP + FRENCH_STOP}


def match_ror(conditions: dict) -> dict:
    strategies = conditions.get('strategies')
    if strategies is None:
        strategies = DEFAULT_STRATEGIES
    matcher = Matcher()
    return matcher.match(
        field='rors',
        conditions=conditions,
        strategies=strategies,
        pre_treatment_query=remove_ref_index,
        stopwords_strategies=STOPWORDS_STRATEGIES,
    )
