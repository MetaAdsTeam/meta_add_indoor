import app.data_classes as dc
from .base import BaseHandler


class TurnOn(BaseHandler):
    async def post(self, device_id):
        device_id = int(device_id)
        user_data = self.ms.get_authorization_params_by_id(device_id)
        filename = self.json_args['name']
        from_time = self.get_datetime_json_argument('start_date')
        to_time = self.get_datetime_json_argument('end_date')
        task = dc.TaskWrapper(dc.AdTaskConfig(filename, device_id, user_data, from_time, to_time), True)
        self.tasks_queue.put(task)
        await self.send_ok()


class TurnOff(BaseHandler):
    async def post(self, device_id):
        device_id = int(device_id)
        user_data = self.ms.get_authorization_params_by_id(device_id)
        filename = self.json_args['name']
        from_time = self.get_datetime_json_argument('start_date')
        to_time = self.get_datetime_json_argument('end_date')
        task = dc.TaskWrapper(dc.AdTaskConfig(filename, device_id, user_data, from_time, to_time), False)
        self.tasks_queue.put(task)
        await self.send_ok()
