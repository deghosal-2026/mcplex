"""
MCPlex configuration models and loader.

Defines the Pydantic schemas for config.yaml and handles file loading
with structured error reporting.  Connector type is validated via an
Enum so a typo like ``type: htt`` is caught immediately rather than
silently dropping the connector's tools.
"""

import logging
from enum import Enum
from pathlib import Path

import yaml
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


class ConnectorType(str, Enum):
    """Valid connector types.  'http' proxies via the generic HTTP handler."""
    native = "native"
    http = "http"


class HttpToolConfig(BaseModel):
    """HTTP-proxy specific configuration for a single tool.

    Fields
    ------
    method : str
        HTTP verb (GET, POST, etc.).
    path : str
        URL path relative to the connector's ``base_url``.
    param_mapping : dict[str, str]
        Maps MCP argument names → backend API parameter names.
    headers : dict[str, str]
        Static headers injected on every request to this tool.
    """
    method: str = "GET"
    path: str
    param_mapping: dict[str, str] = Field(default_factory=dict)
    headers: dict[str, str] = Field(default_factory=dict)


class ToolDef(BaseModel):
    """A single MCP tool exposed to the agent."""
    name: str
    description: str
    parameters: dict
    returns: dict = Field(default_factory=dict)
    permission: str = "read"
    http: HttpToolConfig | None = None


class ConnectorDef(BaseModel):
    """A backend service that provides one or more tools."""
    name: str
    type: ConnectorType = ConnectorType.native
    base_url: str = ""
    tools: list[ToolDef]


class Config(BaseModel):
    """Top-level config holding all connector definitions."""
    connectors: list[ConnectorDef]


def load_config(path: Path) -> Config:
    """Load and validate a YAML config file.

    Returns an empty config if the file exists but is blank.
    Raises on file-not-found or malformed YAML with a logged hint.
    """
    try:
        raw = yaml.safe_load(path.read_text())
    except FileNotFoundError:
        logger.error("Config file not found: %s", path)
        raise
    except yaml.YAMLError as e:
        logger.error("Invalid YAML in config file %s: %s", path, e)
        raise
    if raw is None:
        raw = {"connectors": []}
    return Config(**raw)
