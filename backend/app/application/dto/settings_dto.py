from dataclasses import dataclass
from typing import List, Optional

@dataclass(frozen=True)
class DatabaseSettings:
    host: str
    port: int
    name: str
    user: str
    password: str
    pool_size: int = 20

@dataclass(frozen=True)
class ApiSettings:
    host: str
    port: int
    title: str
    version: str
    base_path: str
    cors_origins: List[str]

@dataclass(frozen=True)
class AppSettings:
    environment: str
    debug: bool
    log_level: str
    database: DatabaseSettings
    api: ApiSettings
