import re

from project.server.main.matcher import Matcher
from project.server.main.utils import FRENCH_STOP, remove_ref_index

DEFAULT_STRATEGIES = [
    [
        ["paysage_id"],
        ["paysage_acronym", "paysage_name", "paysage_city"],
        ["paysage_acronym", "paysage_name", "paysage_zone_emploi"],
        ["paysage_name", "paysage_acronym"],
        ["paysage_name", "paysage_zone_emploi"],
        ["paysage_name", "paysage_city"],
        ["paysage_acronym", "paysage_zone_emploi"],
        ["paysage_acronym", "paysage_city"],
        ["paysage_acronym", "paysage_city"],
    ]
]

STOPWORDS_STRATEGIES = {"paysage_name": FRENCH_STOP}


# Done here rather than in synonym settings in ES as they seem to cause highlight bugs
def pre_treatment_paysage(query: str = "") -> str:
    # If query starts with a digit that can be a reference index
    query = remove_ref_index(query)
    return query.lower()


def match_paysage(conditions: dict) -> dict:
    strategies = conditions.get("strategies")
    if strategies is None:
        strategies = DEFAULT_STRATEGIES
    if "year" in conditions:
        strategies_copy = []
        for equivalent_strategies in strategies:
            equivalent_strategies_copy = []
            for strategy in equivalent_strategies:
                equivalent_strategies_copy.append(strategy + ["paysage_year"])
            strategies_copy.append(equivalent_strategies_copy)
        strategies = strategies_copy
    matcher = Matcher()
    return matcher.match(
        field="paysages",
        conditions=conditions,
        strategies=strategies,
        stopwords_strategies=STOPWORDS_STRATEGIES,
        pre_treatment_query=pre_treatment_paysage,
    )
