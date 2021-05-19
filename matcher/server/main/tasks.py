from matcher.server.main.init_country import init_country
from matcher.server.main.init_finess import init_es_finess
from matcher.server.main.init_rnsr import init_rnsr
from matcher.server.main.match_country import get_countries_from_query
from matcher.server.main.match_finess import match_unstructured_finess
from matcher.server.main.match_rnsr import match_unstructured, match_fields


def create_task_match(arg) -> dict:
    type_match = arg.get('type', 'rnsr').lower()
    if type_match == 'rnsr':
        return create_task_rnsr(arg)
    elif type_match == 'finess':
        return create_task_finess(arg)
    elif type_match == 'country':
        return create_task_country(arg)
    else:
        return {'error': 'type {type_match} unknown'.format(type_match=type_match)}


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
    if code or name or city or acronym or supervisor_acronym or supervisor_id or supervisor_name:
        return match_fields(year, code, name, city, acronym, supervisor_id)
    elif query:
        return match_unstructured(year, query)
    else:
        return {'error': 'all inputs are empty'}


def create_task_init_rnsr() -> None:
    return init_rnsr()


def create_task_country(arg) -> dict:
    query = arg.get('query', '')
    logs = get_countries_from_query(query)
    return {'logs': logs}


def create_task_init_country():
    return init_country()


def create_task_finess(arg) -> dict:
    query = arg.get('query')
    return match_unstructured_finess(query) if query else {'error': 'all inputs are empty'}


def create_task_init_finess() -> dict:
    return init_es_finess()
