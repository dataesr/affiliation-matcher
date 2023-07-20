import re
from project.server.main.matcher import Matcher
from project.server.main.utils import ENGLISH_STOP, FRENCH_STOP, remove_ref_index

DEFAULT_STRATEGIES = [
    [['ror_id']],
    [['ror_grid_id']],
    [['ror_name', 'ror_supervisor_name', 'ror_acronym', 'ror_city_nuts_level2', 'ror_country'],
    ['ror_name', 'ror_supervisor_name', 'ror_acronym', 'ror_city_zone_emploi', 'ror_country']
    ],
    [['ror_name', 'ror_acronym', 'ror_city', 'ror_country'],
     ['ror_name', 'ror_acronym', 'ror_city_zone_emploi', 'ror_country']
    ],
    [['ror_name', 'ror_country', 'ror_web_url']],
    [['ror_name', 'ror_supervisor_name', 'ror_city', 'ror_country'],
     ['ror_name', 'ror_supervisor_name', 'ror_city_zone_emploi', 'ror_country_code']
    ],
    [['ror_name', 'ror_supervisor_name', 'ror_city_nuts_level2', 'ror_country'],
        ['ror_name', 'ror_supervisor_name', 'ror_city_zone_emploi', 'ror_country']
    ],
    [
        ['ror_name', 'ror_city', 'ror_country'],
        ['ror_name', 'ror_city_zone_emploi', 'ror_country'],
    ],
    #[['ror_acronym', 'ror_city', 'ror_country'], ['ror_acronym', 'ror_city', 'ror_country_code']],
    [['ror_name', 'ror_acronym', 'ror_city'], ['ror_name', 'ror_acronym', 'ror_country']],
    [['ror_web_url', 'ror_country']],
    # ['ror_name', 'ror_acronym', 'ror_country_code']
#    [['ror_name', 'ror_country'],
    # ['ror_name', 'ror_country_code']
#    ],
    [['ror_name', 'ror_city'], ['ror_name', 'ror_city_nuts_level2'], ['ror_name', 'ror_city_zone_emploi']],
    [['ror_web_domain', 'ror_country']]
#    ,[['ror_name_unique', 'ror_city_nuts_level2']],
#    [['ror_acronym_unique', 'ror_city_nuts_level2']],
#    [['ror_name_unique', 'ror_country']],
#    [['ror_acronym_unique', 'ror_country']]
]

STOPWORDS_STRATEGIES = {
        'ror_name': ENGLISH_STOP + FRENCH_STOP,
        'ror_supervisor_name': ENGLISH_STOP + FRENCH_STOP
        }

def replace_synonym(query, source, target):
    rgx = re.compile("(?i)(" + source + ")( |,)")
    return rgx.sub(target+" ", query)

# Done here rather than in synonym settings in ES as they seem to cause highlight bugs
def pre_treatment_ror(query: str = '') -> str:
    query = remove_ref_index(query)
    # If query starts with a digit that can be a reference index
    synonyms = [
            ['comput.', 'computer'],
            ['dpt.', 'department'],
            ['eng.', 'engineering'],
            ['inst.', 'institute'],
            ['institut', 'institute'],
            ['mech.', 'mechanics'],
            ['sci.', 'sciences'],
            ['technol.', 'technology'],
            ['univ.', 'university']
            ]
    for synonym in synonyms:
        query = replace_synonym(query, synonym[0], synonym[1])
    return query.lower()

def match_ror(conditions: dict) -> dict:
    strategies = conditions.get('strategies')
    if strategies is None:
        strategies = DEFAULT_STRATEGIES
    matcher = Matcher()
    return matcher.match(
        field='rors',
        conditions=conditions,
        strategies=strategies,
        pre_treatment_query=pre_treatment_ror,
        stopwords_strategies=STOPWORDS_STRATEGIES,
    )
