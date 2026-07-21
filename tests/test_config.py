"""
Unit tests for config loading.

Tests cover valid YAML, empty connectors, and malformed input.
"""

import pytest
import yaml

from mcplex.config import load_config, Config


def test_load_config(tmp_path):
    """Load a config with a single native connector."""
    config_data = {
        "connectors": [
            {
                "name": "incidentgpt",
                "tools": [
                    {
                        "name": "incident_query_active",
                        "description": "Query active incidents",
                        "parameters": {"service": {"type": "string"}},
                        "returns": {"type": "object"},
                        "permission": "read",
                    }
                ],
            }
        ]
    }
    config_file = tmp_path / "config.yaml"
    config_file.write_text(yaml.dump(config_data))
    config = load_config(config_file)
    assert isinstance(config, Config)
    assert len(config.connectors) == 1
    assert config.connectors[0].name == "incidentgpt"
    assert config.connectors[0].tools[0].name == "incident_query_active"


def test_load_config_empty_connectors(tmp_path):
    """An empty connectors list is valid."""
    config_file = tmp_path / "config.yaml"
    config_file.write_text(yaml.dump({"connectors": []}))
    config = load_config(config_file)
    assert len(config.connectors) == 0


def test_load_config_empty_file(tmp_path):
    """A blank file produces an empty config (not a crash)."""
    config_file = tmp_path / "config.yaml"
    config_file.write_text("")
    config = load_config(config_file)
    assert len(config.connectors) == 0


def test_load_config_invalid_yaml(tmp_path):
    """Malformed YAML raises an exception."""
    config_file = tmp_path / "config.yaml"
    config_file.write_text("{invalid: yaml: unmatched")
    with pytest.raises(Exception):
        load_config(config_file)


def test_load_config_missing_file(tmp_path):
    """A non-existent path raises FileNotFoundError."""
    with pytest.raises(FileNotFoundError):
        load_config(tmp_path / "does-not-exist.yaml")


def test_load_config_http_connector(tmp_path):
    """An HTTP-proxy connector with http config is parsed correctly."""
    config_data = {
        "connectors": [
            {
                "name": "guardian",
                "type": "http",
                "base_url": "http://guardian:8080",
                "tools": [
                    {
                        "name": "guardian_check_policy",
                        "description": "Check a PR",
                        "parameters": {"repo": {"type": "string"}},
                        "http": {
                            "method": "POST",
                            "path": "/mcp/policy/check",
                            "param_mapping": {"repo": "repo"},
                        },
                        "permission": "read",
                    }
                ],
            }
        ]
    }
    config_file = tmp_path / "config.yaml"
    config_file.write_text(yaml.dump(config_data))
    config = load_config(config_file)
    assert config.connectors[0].type.value == "http"
    assert config.connectors[0].base_url == "http://guardian:8080"
    assert config.connectors[0].tools[0].http is not None
    assert config.connectors[0].tools[0].http.path == "/mcp/policy/check"


def test_load_config_invalid_connector_type(tmp_path):
    """An invalid connector type raises a Pydantic validation error."""
    config_data = {
        "connectors": [
            {"name": "bad", "type": "invalid_type", "tools": []}
        ]
    }
    config_file = tmp_path / "config.yaml"
    config_file.write_text(yaml.dump(config_data))
    with pytest.raises(Exception):
        load_config(config_file)
