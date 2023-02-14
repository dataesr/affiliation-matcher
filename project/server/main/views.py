import io
import pandas as pd
import redis

from flask import Blueprint, current_app, jsonify, render_template, request
from rq import Connection, Queue

from project.server.main.logger import get_logger
from project.server.main.tasks import create_task_enrich_filter, create_task_affiliations_list,\
    create_task_load, create_task_match

logger = get_logger(__name__)
main_blueprint = Blueprint('main', __name__, )
default_timeout = 21600


@main_blueprint.route('/', methods=['GET'])
def home():
    return render_template('home.html')


@main_blueprint.route('/load', methods=['GET'])
def run_task_load():
    args = request.args
    logger.debug(args)
    response_object = create_task_load(args=args)
    return jsonify(response_object), 202


@main_blueprint.route('/match', methods=['POST'])
def run_task_match():
    if request.files.get('file') is None:
        args = request.get_json(force=True)
        logger.debug(args)
        response = create_task_match(args=args)
        return jsonify(response), 202
    else:
        args = request.form.to_dict(flat=True)
        decoded_file = request.files.get('file').read().decode('utf-8')
        df_input = pd.read_csv(io.StringIO(decoded_file), header=None)
        queries = []
        results = []
        for _, row in df_input.iterrows():
            query = row[0]
            args['query'] = query
            elt = {}
            elt['query'] = query
            response = create_task_match(args=args)
            if len(response.get('enriched_results')) > 0:
                for f in ['id', 'name', 'acronym', 'city']:
                    elt[f'result_{f}'] = response['enriched_results'][0].get(f)
            results.append(elt)
        df_output = pd.DataFrame(results)
        return jsonify({'logs': df_output.to_csv(index=False)}), 202


@main_blueprint.route('/enrich_filter', methods=['POST'])
def run_task_enrich_filter():
    args = request.get_json(force=True)
    logger.debug(args)
    queue = 'matcher'
    if 'queue' in args and args['queue'] != 'matcher':
        queue = 'matcher_short'
    with Connection(redis.from_url(current_app.config['REDIS_URL'])):
        q = Queue(queue, default_timeout=default_timeout)
        task = q.enqueue(create_task_enrich_filter, args)
    response_object = {'status': 'success', 'data': {'task_id': task.get_id()}}
    return jsonify(response_object), 202


@main_blueprint.route('/match_list', methods=['POST'])
def run_task_affiliations_list():
    args = request.get_json(force=True)
    logger.debug(args)
    queue = 'matcher'
    if 'queue' in args and args['queue'] != 'matcher':
        queue = 'matcher_short'
    with Connection(redis.from_url(current_app.config['REDIS_URL'])):
        q = Queue(queue, default_timeout=default_timeout)
        task = q.enqueue(create_task_affiliations_list, args)
    response_object = {'status': 'success', 'data': {'task_id': task.get_id()}}
    return jsonify(response_object), 202


@main_blueprint.route('/tasks/<task_id>', methods=['GET'])
def get_status(task_id):
    for queue in ['matcher', 'matcher_short']:
        with Connection(redis.from_url(current_app.config['REDIS_URL'])):
            q = Queue(queue)
            task = q.fetch_job(task_id)
        if task:
            response_object = {
                'status': 'success',
                'data': {
                    'task_id': task.get_id(),
                    'task_status': task.get_status(),
                    'task_result': task.result,
                }
            }
            return jsonify(response_object), 202
    response_object = {'status': 'error'}
    return jsonify(response_object), 202
