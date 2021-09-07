from matcher.server.main.matcher import Matcher

DEFAULT_STRATEGIES = [
    [['ror_name', 'ror_acronym', 'ror_city', 'ror_country']]
]


def match_ror(conditions: dict) -> dict:
    strategies = conditions.get('strategies', DEFAULT_STRATEGIES)
    matcher = Matcher()
    return matcher.match(conditions=conditions, strategies=strategies)