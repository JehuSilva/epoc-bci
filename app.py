from flask_socketio import SocketIO, emit
from flask import Flask, render_template
from threading import Thread, Event
from random import random
from time import sleep

from config import DEBUG, HOST, PORT
from epoc.logger import logger
from epoc.epoc import Epoc

__author__ = 'jehu'

app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret!'
app.config['DEBUG'] = DEBUG


socketio = SocketIO(app, async_mode=None, logger=False, engineio_logger=False)
epoc_backend = Epoc(socket = socketio, display = True)



@app.route('/')
def index():
    return render_template('index.html',title = 'EEG Streaming')

@socketio.on('connect', namespace='/test')
def test_connect():
    # global thread
    logger.info('Client connected, Starting epoc backend')
    socketio.start_background_task(epoc_backend.start)



@socketio.on('disconnect', namespace='/test')
def test_disconnect():
    logger.info('Client disconnected')


if __name__ == '__main__':
    try:
        socketio.run(app, host = HOST, port = PORT)
    except KeyboardInterrupt as e:
        epoc_backend.running = False
        logger.info(e)
    except Exception as e:
        epoc_backend.running = False
        logger.error(e)