"""Utils for yaml files."""

from pathlib import Path

import yaml
from pydantic import BaseModel


def yaml_load(file_path: Path) -> dict:
    """Load a yaml file."""
    return yaml.safe_load(file_path.read_text())


def yaml_dump(model: BaseModel) -> str:
    """Dump a model to a yaml string."""
    return yaml.dump(model.model_dump())
