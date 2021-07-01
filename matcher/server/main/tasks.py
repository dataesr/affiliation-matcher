from matcher.server.main.load_country import load_country
from matcher.server.main.load_grid import load_grid
from matcher.server.main.load_rnsr import load_rnsr
from matcher.server.main.load_wikidata import load_wikidata
from matcher.server.main.match_country import match_country
from matcher.server.main.match_rnsr import match_rnsr
from matcher.server.main.match_grid import match_grid


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
