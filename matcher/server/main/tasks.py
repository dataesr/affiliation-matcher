from matcher.server.main.load_country import load_country
from matcher.server.main.load_grid import load_grid
from matcher.server.main.load_rnsr import load_rnsr
from matcher.server.main.load_wikidata import load_wikidata
from matcher.server.main.match_country import match_country
from matcher.server.main.match_finess import match_unstructured_finess
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
        return create_task_rnsr(args)
    elif matcher_type == 'finess':
        return create_task_finess(args)
    elif matcher_type == 'country':
        return create_task_country(args)
    elif matcher_type == 'grid':
        return create_task_grid(args)
    else:
        return {'Error': f'Matcher type {matcher_type} unknown'}


def create_task_rnsr(arg) -> dict:
    year = arg.get('year')
    query = arg.get('query')
    code = arg.get('code_number')
    name = arg.get('name')
    city = arg.get('city')
    acronym = arg.get('acronym')
    supervisor_acronym = arg.get('supervisor_acronym')
    supervisor_id = arg.get('supervisor_id')
    supervisor_name = arg.get('supervisor_name')
    #if code or name or city or acronym or supervisor_acronym or supervisor_id or supervisor_name:
    #    return match_fields(year, code, name, city, acronym, supervisor_id)
    if query:
        return match_rnsr(query = query, year = year, index_prefix = arg.get('index_prefix', ''))
    else:
        return {'error': 'all inputs are empty'}


def create_task_country(arg) -> dict:
    query = arg.get('query', '')
    return match_country(query=query, index_prefix = arg.get('index_prefix', ''))

def create_task_grid(arg) -> dict:
    query = arg.get('query', '')
    return match_grid(query=query)


def create_task_finess(arg) -> dict:
    query = arg.get('query', '')
    return match_unstructured_finess(query) if query else {'error': 'all inputs are empty'}
