from sqlalchemy.orm import Session

import app
import app.data_classes as dc
import app.log_lib as log_lib
import app.models as models


class MS:
    __logger: 'log_lib' = None

    def __init__(self, session: Session, context_: 'app.AddRealityContext' = None):
        self.session = session
        if context_ is None:
            context_ = app.context
        self.context = context_

    @property
    def logger(self) -> 'log_lib.Logger':
        if self.__logger is None:
            self.__logger = log_lib.get_logger(self.__class__.__name__)
        return self.__logger

    def get_authorization_params_by_id(self, device_id: int):
        q_authorization = self.session.query(
            models.Publisher.login,
            models.Publisher.password,
            models.Publisher.platform_id
        ).filter(
            models.Publisher.device_id == device_id
        ).first()

        return dc.User(
            q_authorization.login,
            app.utils.decode_password(q_authorization.password),
            q_authorization.platform_id,
        )
