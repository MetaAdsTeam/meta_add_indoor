# Add Publisher

import app
from app import models
from app.utils import encode_password

if __name__ == '__main__':
    login = input("login: ")
    password_hash = encode_password(input("password: "))
    device_id = int(input("device_id: "))
    platform_id = int(input("platform_id: "))

    with app.context.sc as sc:
        sc.session.add(models.Publisher(
            login=login,
            password=password_hash,
            device_id=device_id,
            domain=None,
            platform_id=platform_id,
        ))
