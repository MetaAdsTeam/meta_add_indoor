import app.data_classes as dc
from .base import BaseHandler


class TurnOn(BaseHandler):
    async def post(self):
        task_name = self.json_args['name']
        from_time = self.json_args['from_time']
        to_time = self.json_args['to_time']
        task = dc.TaskWrapper(dc.AdTaskConfig(task_name, from_time, to_time), True)
        self.tasks_queue.put(task)
        await self.send_ok()


class TurnOff(BaseHandler):
    async def post(self):
        task_name = self.json_args['name']
        from_time = self.json_args['from_time']
        to_time = self.json_args['to_time']
        task = dc.TaskWrapper(dc.AdTaskConfig(task_name, from_time, to_time), False)
        self.tasks_queue.put(task)
        await self.send_ok()
