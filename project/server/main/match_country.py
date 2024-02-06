from project.server.main.matcher import Matcher
from project.server.main.utils import ENGLISH_STOP, FRENCH_STOP

STOPWORDS_STRATEGIES = {'grid_name': ENGLISH_STOP + FRENCH_STOP}

COUNTRY_DEFAULT_STRATEGIES = [
    [['ror_id'], ['grid_id'], ['rnsr_id']],
    [['grid_cities_by_region', 'grid_name', 'grid_acronym', 'country_name'],
        ['grid_cities_by_region', 'grid_name', 'country_name'], ['grid_cities_by_region', 'grid_acronym', 'country_name'],
        ['grid_cities_by_region', 'country_name'],
        ['grid_cities_by_region', 'grid_name', 'country_subdivision_name', 'country_alpha3'],
        ['grid_cities_by_region', 'grid_name', 'country_alpha3'],
        ['grid_cities_by_region', 'grid_acronym', 'country_subdivision_name', 'country_alpha3'],
        ['grid_cities_by_region', 'country_subdivision_name', 'country_alpha3']],
    [['grid_acronym', 'country_name'], ['grid_name', 'country_name'], ['country_subdivision_name', 'country_name']],
    [['country_name']],
    [['country_subdivision_name', 'country_alpha3'],
        ['grid_name', 'country_subdivision_name', 'country_subdivision_code']],
    [['grid_name', 'grid_cities_by_region']],
    [['grid_acronym', 'grid_cities_by_region']],
    [['grid_name', 'country_subdivision_name']],
    [['rnsr_code_number'], ['rnsr_acronym', 'rnsr_supervisor_acronym'],
        ['rnsr_name', 'rnsr_zone_emploi', 'country_name'], ['rnsr_name', 'rnsr_city', 'country_name']],
    [['rnsr_code_prefix', 'rnsr_acronym'], ['rnsr_code_prefix', 'rnsr_supervisor_acronym']]
]


def match_country(conditions: dict) -> dict:
    strategies = conditions.get('strategies')
    if strategies is None:
        strategies = COUNTRY_DEFAULT_STRATEGIES
    matcher = Matcher()
    return matcher.match(
            method='country',
            field='country_alpha2',
            conditions=conditions,
            strategies=strategies,
            stopwords_strategies=STOPWORDS_STRATEGIES
        )
