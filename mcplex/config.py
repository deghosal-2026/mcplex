import yaml
from pathlib import Path
from pydantic import BaseModel


class ToolDef(BaseModel):
    name: str
    description: str
    parameters: dict
    returns: dict
    permission: str = "read"


class ConnectorDef(BaseModel):
    name: str
    tools: list[ToolDef]


class Config(BaseModel):
    connectors: list[ConnectorDef]


def load_config(path: Path) -> Config:
    raw = yaml.safe_load(path.read_text())
    return Config(**raw)
