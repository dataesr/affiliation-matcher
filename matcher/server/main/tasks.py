from matcher.server.main.load_country import load_country
from matcher.server.main.load_grid import load_grid
from matcher.server.main.load_rnsr import load_rnsr
from matcher.server.main.load_wikidata import load_wikidata
from matcher.server.main.match_country import match_country
from matcher.server.main.match_rnsr import match_rnsr
from matcher.server.main.match_grid import match_grid
from matcher.server.main.affiliation_matcher import enrich_and_filter_publications_by_country, check_matcher_health 
from matcher.server.main.logger import get_logger


logger = get_logger(__name__)

def create_task_enrich_filter(args: dict = None) -> dict:
    check_matcher_health()
    publications = args.get('publications')
    countries_to_keep = args.get('countries_to_keep')
    if not isinstance(publications, list):
        logger.debug("no valid publications args")
    if not isinstance(countries_to_keep, list):
        logger.debug("no valid countries_to_keep args")
    return enrich_and_filter_publications_by_country(publications, countries_to_keep)

def create_task_load(args: dict = None) -> dict:
    if args is None:
        args = {}
    matcher_type = args.get('type', 'all').lower()
    res = {}
    if matcher_type == 'all':
        res.update(load_country())
        res.update(load_grid())
        res.update(load_rnsr())
    elif matcher_type == 'country':
        res.update(load_country())
    elif matcher_type == 'grid':
        res.update(load_grid())
    elif matcher_type == 'rnsr':
        res.update(load_rnsr())
    elif matcher_type == 'wikidata':
        res.update(load_wikidata())
    else:
        return {'Error': f'Matcher type {matcher_type} unknown'}
    return res

def create_task_match(args: dict = None) -> dict:
    if args is None:
        args = {}
    matcher_type = args.get('type', 'rnsr').lower()
    if matcher_type == 'rnsr':
        return match_rnsr(args)
    elif matcher_type == 'country':
        return match_country(args)
    elif matcher_type == 'grid':
        return match_grid(args)
    else:
        return {'Error': f'Matcher type {matcher_type} unknown'}
