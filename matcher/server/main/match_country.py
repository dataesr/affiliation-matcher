from matcher.server.main.Matcher import Matcher

DEFAULT_STRATEGIES = [['all_names']]


def match_country(query: str = '', strategies: list = None) -> dict:
    if strategies is None:
        strategies = DEFAULT_STRATEGIES
    matcher = Matcher()
    return matcher.match(query=query, strategies=strategies, field='country_alpha2')
