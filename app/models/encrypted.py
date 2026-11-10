import json
from typing import Any

import sqlalchemy as sa
from cryptography.fernet import Fernet
from sqlalchemy.engine import Dialect


class Encrypted(sa.TypeDecorator[Any]):
    impl = sa.Text
    cache_ok = True

    def __init__(self, encryption_key: str, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self.encryption_key = encryption_key
        self.fernet = Fernet(encryption_key.encode())

    def process_bind_param(self, value: Any, dialect: Dialect) -> str | None:
        if value is None:
            return None
        return self.fernet.encrypt(json.dumps(value).encode()).decode()

    def process_result_value(self, value: str | None, dialect: Dialect) -> Any:
        if value is None:
            return None
        return json.loads(self.fernet.decrypt(value.encode()))
