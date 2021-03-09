from flask_socketio import SocketIO, emit
from flask import Flask, render_template
from threading import Thread, Event
from random import random
from time import sleep


from epoc.logger import logger
from epoc.epoc import Epoc

__author__ = 'jehu'

app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret!'
app.config['DEBUG'] = True


socketio = SocketIO(app, async_mode=None, logger=False, engineio_logger=False)
epoc_backend = Epoc(socket = socketio, display = True)

# #random number Generator Thread
# thread = Thread()
# thread_stop_event = Event()

# def randomNumberGenerator():
#     print("Making random numbers")
#     while not thread_stop_event.isSet():
#         number = round(random()*10, 3)
#         print(number)
#         socketio.emit('newnumber', {'number': number}, namespace='/test')
#         socketio.sleep(0.05)


@app.route('/')
def index():
    return render_template('index.html',title = 'EEG Streaming')

@socketio.on('connect', namespace='/stream')
def test_connect():
    # global thread
    logger.info('Client connected')

    #Start the random number generator thread only if the thread has not been started before.
    # try:
    #     if not thread.isAlive():
    #         print("Starting Thread")
    #         thread = socketio.start_background_task(randomNumberGenerator)
    # except Exception as e:
    #     print(e)

    epoc_backend.start()


@socketio.on('disconnect', namespace='/stream')
def test_disconnect():
    logger.info('Client disconnected')


if __name__ == '__main__':
    try:
        socketio.run(app)
    except KeyboardInterrupt as e:
        logger.info(e)
    except Exception as e:
        logger.error(e)