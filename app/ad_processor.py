import time
from queue import Queue, Empty
from threading import Thread

import app.data_classes as dc
from app import campaign_generator
from app.main import AddRealityHandler


class AdProcessor:
    def __init__(self, tasks_queue: Queue['dc.AdTaskConfig']):
        self.alive = False
        self.tasks_queue = tasks_queue
        self.tasks_processor_thread = Thread(target=self.task_processor)
        self.handler = AddRealityHandler()

    def task_processor(self):
        while self.alive:
            try:
                task = self.tasks_queue.get_nowait()
                self.handle(task)
            except Empty:
                time.sleep(.25)

    def start(self):
        self.alive = True
        self.tasks_processor_thread.start()

    def stop(self):
        self.alive = False
        self.tasks_processor_thread.join()

    def handle(self, task: 'dc.AdTaskConfig'):
        self.handler.authorization()
        content_id = self.handler.get_content_id(task.name)
        if not content_id:
            self.handler.add_content(task.name)
            content_id = self.handler.get_content_id(task.name)

        created_campaign = campaign_generator.create_campaign(content_id, task)
        self.handler.add_and_start_campaign(created_campaign)
