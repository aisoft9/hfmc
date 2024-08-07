"""Initialize, load, and save configuration settings."""

from __future__ import annotations

from typing import TypeVar, cast

from hffs.utils.yaml import yaml_dump, yaml_load

from .hffs_config import (
    CONFIG_DIR,
    CONFIG_FILE,
    HffsConfig,
)
from .hffs_config import (
    HffsConfigOption as ConfOpt,
)

DEFAULT_CONFIG = HffsConfig()


def init_config() -> None:
    """Initialize HFFS configuration."""
    if not CONFIG_DIR.exists():
        CONFIG_DIR.mkdir(parents=True, exist_ok=True)

    if not CONFIG_FILE.exists():
        CONFIG_FILE.touch()

    # create yaml files based on the configuration settings
    CONFIG_FILE.write_text(yaml_dump(DEFAULT_CONFIG))


def load_config() -> HffsConfig:
    """Load HFFS configuration."""
    if not CONFIG_FILE.exists():
        init_config()

    conf_dict = yaml_load(CONFIG_FILE)
    return HffsConfig.model_validate(conf_dict)


def save_config(config: HffsConfig) -> None:
    """Save HFFS configuration."""
    if not CONFIG_FILE.exists():
        init_config()

    CONFIG_FILE.write_text(yaml_dump(config))


def get_config_yaml() -> str:
    """Get HFFS configuration in yaml format."""
    return CONFIG_FILE.read_text()


T = TypeVar("T")


def get_config(opt: ConfOpt, _: type[T]) -> T:
    """Get a specific configuration option."""
    config = load_config()
    return cast(T, getattr(config, opt.value))


def set_config(opt: ConfOpt, value: T, _: type[T]) -> T:
    """Set a specific configuration option."""
    config = load_config()
    setattr(config, opt.value, cast(T, value))
    save_config(config)
    return value


def reset_config(opt: ConfOpt, conf_type: type[T]) -> T:
    """Reset a specific configuration option."""
    value = cast(T, getattr(DEFAULT_CONFIG, opt.value))
    return set_config(opt, value, conf_type)