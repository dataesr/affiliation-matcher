import re

from matcher.server.main.Matcher import Matcher
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


# Done here rather than in synonym settings in ES as they seem to cause highlight bugs
def pre_treatment_rnsr(query: str = '') -> str:
    # If query starts with a digit that can be a reference index
    query = remove_ref_index(query)
    rgx = re.compile("(?i)(unit. mixte de recherche)( |)(S)( |)([0-9])")
    return rgx.sub("umr\\3\\5", query).lower()


def match_rnsr(query: str = '', strategies: list = None, year: str = None) -> dict:
    if strategies is None:
        strategies = DEFAULT_STRATEGIES
    if year:
        strategies_with_year = [strategy.append('rnsr_year') for strategy in strategies.copy()]
        strategies = strategies_with_year + strategies
    matcher = Matcher()
    return matcher.match(query=query, strategies=strategies, year=year, pre_treatment_query=pre_treatment_rnsr)
