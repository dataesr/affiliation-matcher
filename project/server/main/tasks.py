import time
from project.server.main.match_rnsr import match_unstructured
from project.server.main.init_rnsr import init_es

def create_task_match(arg):
    type_match = arg.get('type', 'rnsr')
    
    if type_match.lower() == 'rnsr':
        return create_task_rnsr(arg)
    return {'error': 'type {} unknown'.format(type_match)}

def create_task_rnsr(arg):
    year = arg.get('year', 2020)
    query = arg.get('query', None)
    
    code = arg.get('code', None)
    name = arg.get('name', None)
    city = arg.get('city', None)
    acronym = arg.get('acronym', None)

    supervisor_acronym = arg.get('supervisor_acronym', None)
    supervisor_id = arg.get('supervisor_id', None)
    supervisor_name = arg.get('supervisor_name', None)
    
    return match_unstructured(year, query, code, name, city, acronym, supervisor_acronym, supervisor_id, supervisor_name)

def create_task_init_rnsr():
    return init_es()

def test_sleep(task_type):
    time.sleep(int(task_type) * 10)
    return True
