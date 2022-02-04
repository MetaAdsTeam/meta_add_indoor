import signal
from concurrent.futures import ThreadPoolExecutor
from queue import Queue

from tornado.web import Application
from tornado.ioloop import IOLoop

from app.ad_processor import AdProcessor
from app.handlers import TurnOff, TurnOn

from app.log_lib import get_logger

logger = get_logger('API')


class App:

    def __init__(self, port: int = 4000):
        self.alive = False
        self.tasks_queue = Queue()
        self.executor = ThreadPoolExecutor()
        self.application = Application(
            self.urls,
            tasks_queue=self.tasks_queue,
            executor=self.executor
        )
        self.server = self.application.listen(port)
        self.ad_processor = AdProcessor(self.tasks_queue)

    @property
    def urls(self):
        return [
            ("/turn_on", TurnOn),
            ("/turn_off", TurnOff),
        ]

    def start(self):
        logger.info('Starting application...')
        self.alive = True
        self.add_signals()
        self.ad_processor.start()
        IOLoop.current().start()

    def stop(self):
        logger.info('Stopping application...')
        IOLoop.current().stop()
        self.server.stop()
        self.ad_processor.stop()
        logger.info('Stopped.')

    def add_signals(self):
        # Base SIG handlers
        for sig in (signal.SIGTERM, signal.SIGINT):
            signal.signal(sig, lambda signum, stack: IOLoop.current().add_callback_from_signal(self.stop))


if __name__ == '__main__':
    app = App()
    app.start()
