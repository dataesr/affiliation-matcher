from matcher.server.main.init_country import init_country
from matcher.server.main.init_grid import init_grid
from matcher.server.main.init_rnsr import init_rnsr
from matcher.server.main.match_country import get_countries_from_query
from matcher.server.main.match_finess import match_unstructured_finess
from matcher.server.main.match_rnsr import match_rnsr


def create_task_init(args: dict = None) -> dict:
    if args is None:
        args = {}
    matcher_type = args.get('type', 'all').lower()
    if matcher_type == 'all':
        init_rnsr()
        init_country()
        init_grid()
    elif matcher_type == 'rnsr':
        init_rnsr()
    elif matcher_type == 'country':
        init_country()
    elif matcher_type == 'grid':
        init_grid()
    else:
        return {'Error': f'Matcher type {matcher_type} unknown'}


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
    else:
        return {'Error': f'Matcher type {matcher_type} unknown'}


def create_task_rnsr(arg) -> dict:
    year = arg.get('year', 2020)
    query = arg.get('query', None)
    code = arg.get('code', None)
    name = arg.get('name', None)
    city = arg.get('city', None)
    acronym = arg.get('acronym', None)
    supervisor_acronym = arg.get('supervisor_acronym', None)
    supervisor_id = arg.get('supervisor_id', None)
    supervisor_name = arg.get('supervisor_name', None)
    #if code or name or city or acronym or supervisor_acronym or supervisor_id or supervisor_name:
    #    return match_fields(year, code, name, city, acronym, supervisor_id)
    if query:
        return match_rnsr(query)
    else:
        return {'error': 'all inputs are empty'}


def create_task_country(arg) -> dict:
    query = arg.get('query', '')
    return get_countries_from_query(query=query)


def create_task_finess(arg) -> dict:
    query = arg.get('query', '')
    return match_unstructured_finess(query) if query else {'error': 'all inputs are empty'}

