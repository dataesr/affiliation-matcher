import re

from project.server.main.matcher import Matcher
from project.server.main.utils import remove_ref_index

DEFAULT_STRATEGIES = [
    [['rnsr_code_number', 'rnsr_supervisor_acronym', 'rnsr_supervisor_name', 'rnsr_zone_emploi']],
    [['rnsr_code_number', 'rnsr_supervisor_name', 'rnsr_zone_emploi']],
    [['rnsr_code_number', 'rnsr_acronym']],
    [['rnsr_code_number', 'rnsr_name']],
    [['rnsr_code_number', 'rnsr_supervisor_acronym']],
    [['rnsr_code_number', 'rnsr_supervisor_name']],
    [['rnsr_code_number', 'rnsr_zone_emploi']],
    [['rnsr_acronym', 'rnsr_name', 'rnsr_supervisor_name', 'rnsr_zone_emploi']],
    [['rnsr_acronym', 'rnsr_name', 'rnsr_supervisor_acronym', 'rnsr_zone_emploi']],
    [['rnsr_acronym', 'rnsr_name', 'rnsr_zone_emploi']],
    [['rnsr_acronym', 'rnsr_supervisor_acronym', 'rnsr_zone_emploi']],
    [['rnsr_acronym', 'rnsr_supervisor_name', 'rnsr_zone_emploi']],
    [['rnsr_name', 'rnsr_supervisor_acronym', 'rnsr_zone_emploi']],
    [['rnsr_name', 'rnsr_supervisor_name', 'rnsr_zone_emploi']],
    [['rnsr_name', 'rnsr_acronym', 'rnsr_supervisor_acronym']],
    [['rnsr_name', 'rnsr_acronym', 'rnsr_supervisor_name']],
    [['rnsr_name', 'rnsr_zone_emploi']],
    [['rnsr_acronym', 'rnsr_zone_emploi']],
    [['rnsr_name', 'rnsr_acronym']],
    [['rnsr_acronym', 'rnsr_city']]
]


# Done here rather than in synonym settings in ES as they seem to cause highlight bugs
def pre_treatment_rnsr(query: str = '') -> str:
    # If query starts with a digit that can be a reference index
    query = remove_ref_index(query)
    rgx = re.compile("(?i)(unit. mixte de recherche)( |)(S)( |)([0-9])")
    return rgx.sub("umr\\3\\5", query).lower()


def match_rnsr(conditions: dict) -> dict:
    strategies = conditions.get('strategies')
    if strategies is None:
        strategies = DEFAULT_STRATEGIES
    if 'year' in conditions:
        strategies_copy = []
        for equivalent_strategies in strategies:
            equivalent_strategies_copy = []
            for strategy in equivalent_strategies:
                equivalent_strategies_copy.append(strategy + ['rnsr_year'])
            strategies_copy.append(equivalent_strategies_copy)
        strategies = strategies_copy
    matcher = Matcher()
    return matcher.match(method='rnsr', conditions=conditions, strategies=strategies,
                         pre_treatment_query=pre_treatment_rnsr)
