from typing import Optional

import sqlalchemy as sa

import app.models as models


class Publisher(models.Base):
    """
    Dashboard users table
    """
    __tablename__ = 'publishers'

    id = sa.Column(sa.Integer, primary_key=True)
    login = sa.Column(sa.String(), nullable=False)
    password = sa.Column(sa.LargeBinary, nullable=False)
    device_id = sa.Column(sa.Integer(), unique=True, nullable=False)
    domain = sa.Column(sa.String())
    platform_id = sa.Column(sa.Integer(), nullable=False)

    def __init__(
            self,
            login: str,
            password: str,
            device_id: int,
            domain: Optional[str],
            platform_id: int,
    ):
        self.login = login
        self.password = password
        self.device_id = device_id
        self.domain = domain
        self.platform_id = platform_id
