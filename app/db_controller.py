import logging
from time import sleep
from typing import Optional, Union

import sqlalchemy as sa
import sqlalchemy.engine as engine
import sqlalchemy.ext.asyncio as asa
from sqlalchemy.engine import Result
from sqlalchemy.orm import Session, sessionmaker

import app.exceptions as exceptions
from app.log_lib import get_logger


# noinspection PyBroadException
class SessionContext:
    logger = logging
    __session: Union['Session', 'asa.AsyncSession'] = None

    def __init__(self, engine_: Union['engine.Engine', 'asa.AsyncEngine'], async_mode: bool):
        self.__engine: 'engine.Engine' = engine_
        self.__async_mode: bool = async_mode

    @property
    def session(self) -> Union['Session', 'asa.AsyncSession']:
        if self.__session is None:
            if self.__async_mode:
                raise exceptions.APIError(
                    'AsyncSession have not yet been initialized.')
            else:
                self.__session = Session(self.__engine, expire_on_commit=False)
        return self.__session

    async def execute(self, statement, params=None, *args, **kwargs) -> Result:
        return await self.session.execute(statement, params=params, *args,
                                          **kwargs)

    @session.setter
    def session(self, session: 'asa.AsyncSession'):
        if not self.__async_mode:
            raise exceptions.APIError('Can`t set sync session')
        self.__session = session

    @property
    def async_session_maker(self) -> 'sessionmaker':
        return sessionmaker(
            self.__engine,
            expire_on_commit=False,
            class_=asa.AsyncSession
        )

    def close(self):
        try:
            self.session.commit()
        except Exception as ex:
            self.logger.warning(
                'Session commit error, rollback ...\n{}'.format(ex))
            self.session.rollback()
        finally:
            self.session.close()

    async def a_close(self):
        try:
            await self.session.commit()
        except Exception as ex:
            self.logger.warning(
                'Session commit error, rollback ...\n{}'.format(ex))
            await self.session.rollback()
        finally:
            await self.session.close()

    def commit(self):
        try:
            self.session.commit()
        except Exception as e:
            if hasattr(e, 'detail'):
                raise exceptions.APIError(
                    f'One of arguments are wrong. Details: {e.detail}')
            else:
                raise exceptions.APIError(f'One of arguments are wrong. '
                                          f'Please make sure you are sending right request.')

    async def a_commit(self):
        try:
            await self.session.commit()
        except Exception as e:
            if hasattr(e, 'detail'):
                raise exceptions.APIError(
                    f'One of arguments are wrong. Details: {e.detail}')
            else:
                raise exceptions.APIError(f'One of arguments are wrong. '
                                          f'Please make sure you are sending right request.')

    def flush(self, *args, **kwargs):
        try:
            self.session.flush(*args, **kwargs)
        except Exception as e:
            try:
                details = 'One of arguments are wrong. ' + \
                          e.args[0].split('\n')[-2]
            except Exception:
                details = f'One of arguments are wrong. Please make sure you are sending right request.'
            self.session.rollback()
            raise exceptions.APIError(details)

    async def a_flush(self, *args, **kwargs):
        try:
            await self.session.flush(*args, **kwargs)
        except Exception as e:
            try:
                details = 'One of arguments are wrong. ' + \
                          e.args[0].split('\n')[-2]
            except Exception:
                details = f'One of arguments are wrong. Please make sure you are sending right request.'
            await self.session.rollback()
            raise exceptions.APIError(details)


class WithSessionContextManager:
    def __init__(self, db_controller: 'DBController'):
        self.db_controller = db_controller
        self.sc: Optional[SessionContext] = None
        self.__a_session_cm = None

    def __enter__(self):
        self.sc = self.db_controller.make_sc()
        return self.sc

    async def __aenter__(self):
        self.sc = self.db_controller.make_async_sc()
        self.__a_session_cm = self.sc.async_session_maker()
        self.sc.session = await self.__a_session_cm.__aenter__()
        return self.sc

    def __exit__(self, err_type, err_value, err_traceback):
        self.sc.close()

    async def __aexit__(self, err_type, err_value, err_traceback):
        await self.sc.a_close()
        await self.__a_session_cm.__aexit__(err_type, err_value, err_traceback)


class DBController:
    """Database controller."""
    __engine: 'engine.Engine' = None
    __async_engine: 'asa.AsyncEngine' = None

    def __init__(self, context):
        self.logger = get_logger(self.__class__.__name__)
        self.app_context = context
        self.logger.debug('DBController started.')

    @property
    def engine(self):
        if self.__engine is None:
            self.__engine = sa.create_engine(
                self.app_context.db_config.db_con_string,
                echo=False,
                encoding='utf-8'
            )
        return self.__engine

    @property
    def async_engine(self):
        if self.__async_engine is None:
            self.__async_engine = asa.create_async_engine(
                self.app_context.db_config.async_db_con_string,
                echo=False,
                encoding='utf-8'
            )
        return self.__async_engine

    def make_sc(self) -> SessionContext:
        while self.engine is None:
            sleep(.05)
        return SessionContext(self.__engine, False)

    def make_async_sc(self) -> SessionContext:
        while self.async_engine is None:
            sleep(.05)
        return SessionContext(self.__async_engine, True)

    def with_sc(self) -> WithSessionContextManager:
        return WithSessionContextManager(self)

    def stop(self):
        if self.__engine is not None:
            self.__engine.dispose()
        self.logger.debug('DBController stopped.')
