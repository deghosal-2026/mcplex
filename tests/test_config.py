import yaml

from mcplex.config import load_config, Config


def test_load_config(tmp_path):
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
    config_file = tmp_path / "config.yaml"
    config_file.write_text(yaml.dump({"connectors": []}))
    config = load_config(config_file)
    assert len(config.connectors) == 0


def test_load_config_invalid_yaml(tmp_path):
    config_file = tmp_path / "config.yaml"
    config_file.write_text("{invalid: yaml: unmatched")
    import pytest
    with pytest.raises(Exception):
        load_config(config_file)
