import redis

from flask import Blueprint, current_app, jsonify, render_template, request
from rq import Connection, Queue

from matcher.server.main.logger import get_logger
from matcher.server.main.tasks import create_task_match, create_task_rnsr, create_task_init

logger = get_logger(__name__)
main_blueprint = Blueprint("main", __name__, )


@main_blueprint.route("/", methods=["GET"])
def home():
    return render_template("home.html")


@main_blueprint.route("/init", methods=["GET"])
def run_task_init_rnsr():
    args = request.get_json(force=True)
    logger.debug(args)
    response_object = create_task_init(args=args)
    return jsonify(response_object), 202


@main_blueprint.route("/match_api", methods=["POST"])
def run_task_match():
    args = request.get_json(force=True)
    logger.debug(args)
    response_object = create_task_match(args=args)
    return jsonify(response_object), 202


@main_blueprint.route("/rnsr_match_api", methods=["POST"])
def run_task_rnsr():
    args = request.get_json(force=True)
    logger.debug(args)
    response_object = create_task_rnsr(args)
    # my_arguments = {'url': url, 'title': title}
    # logger.debug(my_arguments)
    # with Connection(redis.from_url(current_app.config["REDIS_URL"])):
    #    q = Queue(default_timeout=21600)
    #    task = q.enqueue(create_task_harvest, args)
    # response_object = {
    #    "status": "success",
    #    "data": {
    #        "task_id": task.get_id()
    #    }
    # }
    return jsonify(response_object), 202


@main_blueprint.route("/tasks/<task_id>", methods=["GET"])
def get_status(task_id):
    with Connection(redis.from_url(current_app.config["REDIS_URL"])):
        q = Queue()
        task = q.fetch_job(task_id)
    if task:
        response_object = {
            "status": "success",
            "data": {
                "task_id": task.get_id(),
                "task_status": task.get_status(),
                "task_result": task.result,
            },
        }
    else:
        response_object = {"status": "error"}
    return jsonify(response_object)
