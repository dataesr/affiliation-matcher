from matcher.server.main.matcher import Matcher

DEFAULT_STRATEGIES = [
                ['grid_city', 'grid_name', 'grid_acronym', 'country_all_names'],
                ['grid_city', 'grid_name', 'country_all_names'],
                ['grid_city', 'grid_acronym', 'country_all_names'],
                ['grid_city', 'country_all_names'],
                ['grid_city', 'grid_name', 'country_alpha3'],
                ['grid_city', 'grid_acronym', 'country_alpha3'],
                ['grid_city', 'country_alpha3'],
                ['country_all_names']
                ]


def match_country(query: str = '', strategies: list = None) -> dict:
    if strategies is None:
        strategies = DEFAULT_STRATEGIES
    matcher = Matcher()
    return matcher.match(query=query, strategies=strategies, field='country_alpha2')