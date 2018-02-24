import flask
from flask import Flask, request
from app.mtga_app import mtga_watch_app
from app.queues import all_die_queue, json_blob_queue, block_read_queue

http_app = Flask(__name__)


@http_app.route('/')
def get_draw_odds():
    if mtga_watch_app.game:
        with mtga_watch_app.game_lock:
            info = mtga_watch_app.game.hero.calculate_draw_odds(mtga_watch_app.game.ignored_iids)
            return flask.jsonify(info)
    return flask.jsonify({"sorry": "no game yet"})


@http_app.route('/die')
def shutdown_server():
    all_die_queue.put("DIE")
    func = request.environ.get('werkzeug.server.shutdown')
    if func is None:
        raise RuntimeError('Not running with the Werkzeug Server')
    func()