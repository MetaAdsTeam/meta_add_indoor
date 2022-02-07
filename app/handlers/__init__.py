import datetime

import app.data_classes as dc
from .base import BaseHandler


class TurnOn(BaseHandler):
    async def post(self):
        task_name = self.json_args['name']
        from_time = self.get_datetime_json_argument('start_date')
        to_time = self.get_datetime_json_argument('end_date')
        task = dc.TaskWrapper(dc.AdTaskConfig(task_name, from_time, to_time), True)
        self.tasks_queue.put(task)
        await self.send_ok()


class TurnOff(BaseHandler):
    async def post(self):
        task_name = self.json_args['name']
        from_time = self.get_datetime_json_argument('start_date')
        to_time = self.get_datetime_json_argument('end_date')
        task = dc.TaskWrapper(dc.AdTaskConfig(task_name, from_time, to_time), False)
        self.tasks_queue.put(task)
        await self.send_ok()
