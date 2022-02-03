import app.data_classes as dc
from .base import BaseHandler


class UserPanel(BaseHandler):
    async def post(self):
        task_name = self.json_args['name']
        task = dc.AdTaskConfig(task_name)
        self.tasks_queue.put(task)
        await self.send_ok()


class CampaignsHandler(BaseHandler):
    async def get(self):
        await self.render(
            'select_user.html'
        )
