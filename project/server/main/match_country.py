from project.server.main.matcher import Matcher
from project.server.main.utils import ENGLISH_STOP, FRENCH_STOP, remove_ref_index

STOPWORDS_STRATEGIES = {'grid_name': ENGLISH_STOP + FRENCH_STOP}

DEFAULT_STRATEGIES = [
    # group 1
    [['grid_cities_by_region', 'grid_name', 'grid_acronym', 'country_name'],
        ['grid_cities_by_region', 'grid_name', 'country_name'], ['grid_cities_by_region', 'grid_acronym', 'country_name'],
        ['grid_cities_by_region', 'country_name'],
        ['grid_cities_by_region', 'grid_name', 'country_subdivision_name', 'country_alpha3'],
        ['grid_cities_by_region', 'grid_name', 'country_alpha3'],
        ['grid_cities_by_region', 'grid_acronym', 'country_subdivision_name', 'country_alpha3'],
        ['grid_cities_by_region', 'country_subdivision_name', 'country_alpha3']],
    # group 2
    [['grid_acronym', 'country_name'], ['grid_name', 'country_name'], ['country_subdivision_name', 'country_name']],
    # group 3
    [['country_name']],
    # group 4
    [['country_subdivision_name', 'country_alpha3'],
        ['grid_name', 'country_subdivision_name', 'country_subdivision_code']],
    # group 5
    [['grid_name', 'grid_cities_by_region']],
    # group 6
    [['grid_name', 'grid_acronym']],
    # group 7
    [['rnsr_acronym', 'rnsr_zone_emploi'], ['rnsr_acronym', 'rnsr_city']],
    # group 7
    [['grid_acronym', 'grid_cities_by_region']],
    # group 8
    [['grid_name', 'country_subdivision_name']],
    # group 9
    [['rnsr_code_number'], ['rnsr_acronym', 'rnsr_supervisor_acronym'], ['rnsr_acronym', 'rnsr_zone_emploi'], ['rnsr_acronym', 'rnsr_city'],
        ['rnsr_name', 'rnsr_zone_emploi'], ['rnsr_name', 'rnsr_city']],
    #group 10
    [['rnsr_code_prefix', 'rnsr_acronym'], ['rnsr_code_prefix', 'rnsr_supervisor_acronym'], ['rnsr_code_prefix', 'rnsr_zone_emploi']]
]


def match_country(conditions: dict) -> dict:
    strategies = conditions.get('strategies')
    if strategies is None:
        strategies = DEFAULT_STRATEGIES
    matcher = Matcher()
    return matcher.match(
            method='country',
            field='country_alpha2',
            conditions=conditions,
            strategies=strategies,
            stopwords_strategies=STOPWORDS_STRATEGIES
            )
