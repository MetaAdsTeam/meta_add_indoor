import asyncio
import logging
import pickle
import sys
from concurrent.futures.thread import ThreadPoolExecutor
from datetime import datetime, date
from queue import Queue
from typing import Optional, Any, Callable

from tornado import escape
from tornado.escape import json_decode
from tornado.ioloop import IOLoop
from tornado.web import RequestHandler

from app import utils, exceptions

logger = logging.getLogger(__name__)


class BaseHandler(RequestHandler):
    json_args: dict = {}

    asyncio_loop: asyncio.AbstractEventLoop
    executor: ThreadPoolExecutor
    tasks_queue: Queue

    def initialize(self) -> None:
        self.tasks_queue = self.application.settings['tasks_queue']

    def set_default_headers(self):
        # self.set_header("Access-Control-Allow-Origin", "*")
        # self.set_header("Access-Control-Allow-Headers", "x-requested-with")
        # self.set_header('Access-Control-Allow-Methods', 'POST, GET, OPTIONS')
        # self.set_header("Access-Control-Allow-Headers", "access-control-allow-origin,authorization,content-type")
        pass

    def data_received(self, chunk):
        """Overload of not implemented method to avoid pep8 linter warnings"""

    async def get(self, *args, **kwargs):
        await self.send_json({'msg': 'Not implemented'}, 501)

    async def post(self, *args, **kwargs):
        await self.send_json({'msg': 'Not implemented'}, 501)

    async def put(self, *args, **kwargs):
        await self.send_json({'msg': 'Not implemented'}, 501)

    async def delete(self, *args, **kwargs):
        await self.send_json({'msg': 'Not implemented'}, 501)

    async def options(self, *args, **kwargs):
        # no body
        self.set_status(204)
        await self.finish()

    def _request_summary(self) -> str:
        return "%s [%s] %s " % (
            self.request.method,
            self.remote_ip,
            self.request.uri.removeprefix('/api'),
        )

    def _prepare_json_args(self):
        content_type = self.request.headers.get('Content-Type', '')
        if any((i in content_type for i in ('application/x-json', 'application/json'))):
            # if self.request.headers.get('Content-Type') in ('application/x-json', 'application/json'):
            self.json_args = json_decode(self.request.body) if self.request.body else {}
        else:  # self.request.headers.get('Content-Type') == 'application/x-www-form-urlencoded':
            for k, v in self.request.arguments.items():
                if len(v) == 1:
                    self.json_args[k] = v[0].decode('utf-8')
                elif len(v) > 1:
                    self.json_args[k] = [v[i].decode('utf-8') for i in range(len(v))]

    async def prepare(self):
        self._prepare_json_args()

    @property
    def asyncio_loop(self):
        return IOLoop.current().asyncio_loop  # noqa

    @property
    def executor(self):
        return self.settings['executor']

    async def run_async(self, f, *args, **kwargs) -> Any:

        if asyncio.iscoroutinefunction(f):
            result = await f(*args, **kwargs)
            return result
        return await self.run_in_executor(f, *args, **kwargs)

    async def run_in_executor(self, f: Callable, *args, **kwargs) -> Any:
        return await self.asyncio_loop.run_in_executor(self.executor, lambda: f(*args, **kwargs))

    async def send_json(self, data, status: int = 200) -> None:
        self.set_header('Content-Type', 'application/json')
        self.set_status(status)
        await self.finish(escape.json_encode(data))

    async def send_object(self, obj: Any, status=200):
        self.set_header('Content-Type', 'application/octet-stream')
        self.set_status(status)
        await self.finish(pickle.dumps(obj))

    def send_object_sync(self, obj: Any, status=200):
        self.set_header('Content-Type', 'application/octet-stream')
        self.set_status(status)
        self.finish(pickle.dumps(obj))

    async def send_no_data(self):
        await self.send_json({'msg': 'No data'}, 404)

    async def send_ok(self, status: int = 200):
        await self.send_json({'msg': 'ok'}, status)

    async def send_failed(self):
        await self.send_json({'msg': 'failed'}, 400)

    def get_date_argument(
            self,
            arg_name: str,
            verify: bool = False,
            default: Optional[date] = None,
    ) -> Optional[date]:
        default_str = default.isoformat() if default else None
        ts = self.json_args.get(arg_name) or self.get_argument(arg_name, default_str)
        return utils.date_from_string(ts, verify)

    def get_datetime_json_argument(self, arg_name: str, verify: bool = False) -> Optional[datetime]:
        ts = self.json_args.get(arg_name)
        return utils.datetime_from_string(ts, verify)

    def write_error(self, status_code: int, **kwargs):
        reason: Optional[str] = None
        error_type: Optional[str] = None
        if 'reason' in kwargs.keys():
            reason = kwargs['reason']
        if 'exc_info' in kwargs.keys():
            err_cls, err, traceback = kwargs['exc_info']
            if isinstance(err, exceptions.APIError):
                self.set_status(err.code)
                status_code = err.code
                reason = err.message
                if hasattr(err, 'error_type'):
                    error_type = err.error_type
        if reason is None:
            if self._reason:
                reason = self._reason
            else:
                reason = 'Web server error {}.'.format(status_code)

        if status_code == 500:
            status_code = 400
            self.set_status(400)
            if sys.exc_info()[0] == KeyError:
                reason = f'Argument `{sys.exc_info()[1].args[0]}` is required but not specified.'
            else:
                reason = repr(sys.exc_info()[1])

        logger.warning(f'Handler error! Status: {status_code}, reason: {reason}')
        self.set_header('Content-Type', 'application/json')
        if error_type:
            self.finish(escape.json_encode({'msg': reason, 'type': error_type}))
        else:
            self.finish(escape.json_encode({'msg': reason}))

    @property
    def remote_ip(self):
        return self.request.headers.get("X-Real-Ip") or \
               self.request.headers.get("X-Forwarded-For") or \
               self.request.remote_ip
