import time
from project.server.main.match_rnsr import match_unstructured
from project.server.main.init_rnsr import init_es

def create_task_match(arg):
    type_match = arg.get('type', 'rnsr')
    year = arg.get('year', 2020)
    query = arg.get('query', '')
    if type_match.lower() == 'rnsr':
        return create_task_rnsr(arg)
    return {'error': 'type {} unknown'.format(type_match)}

def create_task_rnsr(arg):
    year = arg.get('year', 2020)
    query = arg.get('query', '')
    return match_unstructured(year, query)

def create_task_init_rnsr():
    return init_es()

def test_sleep(task_type):
    time.sleep(int(task_type) * 10)
    return True
