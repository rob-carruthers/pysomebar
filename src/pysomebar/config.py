import tomllib
from pathlib import Path

from pydantic import BaseModel

CONFIG_FILE = "./config.toml"


class ModuleConfig(BaseModel):
    enabled: bool = False


class DateModuleConfig(ModuleConfig):
    format: str


class Config(BaseModel):
    date: DateModuleConfig


with Path(CONFIG_FILE).open("rb") as f:
    data = tomllib.load(f)

CONFIG = Config(**data)
