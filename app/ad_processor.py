import datetime
import time
from queue import Queue, Empty
from threading import Thread

import app.data_classes as dc
from app import campaign_generator
from app.addreality_handler import AddRealityHandler


class AdProcessor:
    def __init__(self, tasks_queue: Queue['dc.TaskWrapper']):
        self.alive = False
        self.tasks_queue = tasks_queue
        self.tasks_processor_thread = Thread(target=self.task_processor)

    def task_processor(self):
        while self.alive:
            try:
                task_wrapper = self.tasks_queue.get_nowait()
                self.handle(task_wrapper)
            except Empty:
                time.sleep(.25)

    def start(self):
        self.alive = True
        self.tasks_processor_thread.start()

    def stop(self):
        self.alive = False
        self.tasks_processor_thread.join()

    def handle(self, task_wrapper: 'dc.TaskWrapper'):

        task_wrapper.task.name = r'C:\Users\admin\Documents\add_reality_2\content\2.png'
        handler = AddRealityHandler(task_wrapper.task.user_data)
        handler.authorization()

        campaigns_to_delete = handler.get_device_info(task_wrapper.task.device_id)
        if task_wrapper.switch_to is True:
            content_id = handler.get_content_id(task_wrapper.task.name)
            if not content_id:
                handler.add_content(task_wrapper.task.name)
                content_id = handler.get_content_id(task_wrapper.task.name)
                if not content_id:
                    return

            received_time = task_wrapper.task.from_time

            while received_time > datetime.datetime.utcnow() + datetime.timedelta(seconds=1):
                time.sleep(.25)

            handler.delete_campaigns(campaigns_to_delete)
            created_campaign = campaign_generator.create_campaign(content_id, task_wrapper.task)
            handler.add_and_start_campaign(created_campaign)
        else:
            handler.delete_campaigns(campaigns_to_delete)
