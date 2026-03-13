"""Tests for TopicNode tree model."""

import tempfile
from pathlib import Path

import yaml

from mqtt_manager.models.topic_tree import TopicNode


SAMPLE_TOPICS = {
    "topics": {
        "home": {
            "{room}": {
                "temperature": {
                    "description": "Temp in C",
                    "example_payload": '{"value": 22.5}',
                },
                "humidity": {
                    "description": "Humidity %",
                },
            }
        },
        "devices": {
            "{device_id}": {
                "status": None,
                "command": None,
            }
        },
    }
}


def _write_yaml(data: dict) -> Path:
    tmp = tempfile.NamedTemporaryFile(suffix=".yaml", delete=False, mode="w")
    yaml.dump(data, tmp)
    tmp.flush()
    return Path(tmp.name)


def test_load_from_yaml():
    path = _write_yaml(SAMPLE_TOPICS)
    root = TopicNode.from_yaml(path)
    assert len(root.children) == 2
    names = [c.name for c in root.children]
    assert "home" in names
    assert "devices" in names


def test_topic_path():
    path = _write_yaml(SAMPLE_TOPICS)
    root = TopicNode.from_yaml(path)
    # home -> {room} -> temperature
    home = next(c for c in root.children if c.name == "home")
    room = home.children[0]
    temp = next(c for c in room.children if c.name == "temperature")
    assert temp.topic_path() == "home/{room}/temperature"


def test_description():
    path = _write_yaml(SAMPLE_TOPICS)
    root = TopicNode.from_yaml(path)
    home = next(c for c in root.children if c.name == "home")
    room = home.children[0]
    temp = next(c for c in room.children if c.name == "temperature")
    assert temp.description == "Temp in C"


def test_add_remove_child():
    root = TopicNode("(root)")
    child = root.add_child("test")
    assert len(root.children) == 1
    assert child.name == "test"
    root.remove_child(child)
    assert len(root.children) == 0


def test_to_yaml_roundtrip():
    path = _write_yaml(SAMPLE_TOPICS)
    root = TopicNode.from_yaml(path)
    yaml_str = root.to_yaml()
    data = yaml.safe_load(yaml_str)
    assert "topics" in data
    assert "home" in data["topics"]
    assert "devices" in data["topics"]
