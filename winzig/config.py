import os
from pathlib import Path


class Config:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialize()

        return cls._instance

    def _initialize(self):
        if os.getenv("DEVELOPMENT"):
            self.sqlite_url = "sqlite+aiosqlite:///sqlite.db"
            return

        self.winzig_dir = Path.home() / ".winzig"
        self.winzig_dir.mkdir(parents=True, exist_ok=True)
        self.sqlite_url = f"sqlite+aiosqlite:///{self.winzig_dir / 'sqlite.db'}"
