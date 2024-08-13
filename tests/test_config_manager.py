"""Test the config_manager module."""

from typing import cast

import hfmc.config.config_manager as manager
from hfmc.config.hfmc_config import (
    CONFIG_FILE,
    DEFAULT_CACHE_DIR,
    DEFAULT_DAEMON_PORT,
    HfmcConfig,
    Peer,
)
from hfmc.utils.yaml import yaml_load


def test_init() -> None:
    """Test default initialization."""
    if CONFIG_FILE.exists():
        CONFIG_FILE.unlink()

    manager.init_config()

    conf = cast(dict, yaml_load(CONFIG_FILE))

    assert conf == {
        "cache_dir": str(DEFAULT_CACHE_DIR),
        "peers": [],
        "daemon_port": DEFAULT_DAEMON_PORT,
    }


def test_save_and_load() -> None:
    """Test saving and loading configuration."""
    custom = {
        "cache_dir": "custom_cache_dir",
        "peers": [{"ip": "127.0.0.1", "port": 8080}],
        "daemon_port": 8080,
    }

    peers = [Peer(ip=p["ip"], port=p["port"]) for p in custom["peers"]]
    cache_dir = custom["cache_dir"]
    daemon_port = custom["daemon_port"]

    conf = HfmcConfig(
        cache_dir=cache_dir,
        peers=peers,
        daemon_port=daemon_port,
    )

    manager.save_config(conf)
    saved = cast(dict, yaml_load(CONFIG_FILE))
    assert saved == custom

    loaded = manager.load_config()
    assert loaded == conf


def test_change_config() -> None:
    """Test set, reset, and get configs."""
    port_1 = 1234
    port_2 = 4321

    ip = "192.168.0.1"
    cache_dir = "new_cache_dir"

    manager.set_config(manager.ConfOpt.CACHE, cache_dir, str)
    manager.set_config(manager.ConfOpt.PORT, port_1, int)
    manager.set_config(
        manager.ConfOpt.PEERS,
        [Peer(ip=ip, port=4321)],
        list,
    )

    assert manager.get_config(manager.ConfOpt.CACHE, str) == cache_dir
    assert manager.get_config(manager.ConfOpt.PORT, int) == port_1
    assert manager.get_config(manager.ConfOpt.PEERS, list) == [
        Peer(ip=ip, port=port_2),
    ]

    manager.reset_config(manager.ConfOpt.CACHE, str)
    manager.reset_config(manager.ConfOpt.PORT, int)
    manager.reset_config(manager.ConfOpt.PEERS, list)

    assert manager.get_config(manager.ConfOpt.CACHE, str) == str(
        DEFAULT_CACHE_DIR,
    )
    assert manager.get_config(manager.ConfOpt.PORT, int) == DEFAULT_DAEMON_PORT
    assert manager.get_config(manager.ConfOpt.PEERS, list) == []
