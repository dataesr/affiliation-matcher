import datetime
from project.server.main.affiliation_matcher import check_matcher_health, enrich_and_filter_publications_by_country,\
    get_matches
from project.server.main.load_country import load_country
from project.server.main.load_grid import load_grid
from project.server.main.load_rnsr import load_rnsr
from project.server.main.load_ror import load_ror
from project.server.main.load_wikidata import load_wikidata
from project.server.main.load_paysage import load_paysage
from project.server.main.logger import get_logger
from project.server.main.match_country import match_country
from project.server.main.match_grid import match_grid
from project.server.main.match_rnsr import match_rnsr
from project.server.main.match_ror import match_ror
from project.server.main.match_paysage import match_paysage
from project.server.main.my_elastic import MyElastic

logger = get_logger(__name__)


def create_task_enrich_filter(args: dict = None) -> dict:
    check_matcher_health()
    publications = args.get('publications', {})
    countries_to_keep = args.get('countries_to_keep', {})
    if not isinstance(publications, list):
        logger.debug('No valid publications args')
    if not isinstance(countries_to_keep, list):
        logger.debug('No valid countries_to_keep args')
    return enrich_and_filter_publications_by_country(publications=publications, countries_to_keep=countries_to_keep)


def create_task_affiliations_list(args: dict = None) -> dict:
    check_matcher_health()
    affiliations = args.get('affiliations', [])
    logger.debug(f'Start matching {len(affiliations)} affiliations ...')
    if not isinstance(affiliations, list):
        logger.debug('No valid affiliations args')
    res = []
    match_types = args.get('match_types', ['grid', 'rnsr'])
    for aff in affiliations:
        res.append({'query': aff, 'matches': get_matches(aff, match_types)})
    logger.debug(f'End matching {len(affiliations)} affiliations.')
    return res


def create_task_load(args: dict = None) -> dict:
    if args is None:
        args = {}
    matcher_type = args.get('type', 'all').lower()
    index_prefix = args.get('index_prefix', 'matcher').lower()
    es = MyElastic()
    es.delete_non_dated_indices(index_prefix=index_prefix)
    today = datetime.datetime.today().strftime('%Y%m%d%H%M%S')
    index_prefix_dated = f'{index_prefix}-{today}'
    # the indices are created with the datetime in the name
    result = {}
    if matcher_type == 'all':
        result.update(load_country(index_prefix=index_prefix_dated))
        result.update(load_grid(index_prefix=index_prefix_dated))
        result.update(load_rnsr(index_prefix=index_prefix_dated))
        result.update(load_ror(index_prefix=index_prefix_dated))
        result.update(load_paysage(index_prefix=index_prefix_dated))
    elif matcher_type == 'country':
        result.update(load_country(index_prefix=index_prefix_dated))
    elif matcher_type == 'grid':
        result.update(load_grid(index_prefix=index_prefix_dated))
    elif matcher_type == 'rnsr':
        result.update(load_rnsr(index_prefix=index_prefix_dated))
    elif matcher_type == 'ror':
        result.update(load_ror(index_prefix=index_prefix_dated))
    elif matcher_type == 'wikidata':
        result.update(load_wikidata(index_prefix=index_prefix_dated))
    elif matcher_type == "paysage":
        result.update(load_paysage(index_prefix=index_prefix_dated))
    else:
        result = {'Error': f'Matcher type {matcher_type} unknown'}
    # An alias is the put on the newly created indices
    for idx in list(es.indices.get('*').keys()):
        if idx.startswith(index_prefix_dated):
            current_alias = idx.replace(index_prefix_dated, index_prefix)
            es.update_index_alias(my_alias=current_alias, new_index=idx)
    return result


def create_task_match(args: dict = None) -> dict:
    if args is None:
        args = {}
    matcher_type = args.get('type', 'rnsr').lower()
    if matcher_type == 'country':
        result = match_country(args)
    elif matcher_type == 'grid':
        result = match_grid(args)
    elif matcher_type == 'rnsr':
        result = match_rnsr(args)
    elif matcher_type == 'ror':
        result = match_ror(args)
    elif matcher_type == "paysage":
        result = match_paysage(args)
    else:
        result = {'Error': f'Matcher type {matcher_type} unknown'}
    return result
