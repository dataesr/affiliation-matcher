from matcher.server.main.matcher import Matcher

DEFAULT_STRATEGIES = [
                ['grid_city', 'grid_name', 'grid_acronym', 'country_all_names'],
                ['grid_city', 'grid_name', 'country_all_names'],
                ['grid_city', 'grid_acronym', 'country_all_names'],
                ['grid_city', 'country_all_names'],
                ['grid_city', 'grid_name', 'country_subdivisions', 'country_alpha3'],
                ['grid_city', 'grid_name', 'country_alpha3'],
                ['grid_city', 'grid_acronym', 'country_subdivisions', 'country_alpha3'],
                ['grid_city', 'country_subdivisions', 'country_alpha3'],
                ['grid_name', 'country_all_names'],
                ['country_subdivisions', 'country_all_names'],
                ['country_all_names'],
                ['country_subdivisions', 'country_alpha3'],
                ['grid_name', 'country_subdivisions', 'country_subdivisions_code']
                ]


def match_country(query: str = '', strategies: list = None, index_prefix: str = '') -> dict:
    if strategies is None:
        strategies = DEFAULT_STRATEGIES
    matcher = Matcher()
    return matcher.match(query=query, strategies=strategies, field='country_alpha2', index_prefix=index_prefix)
