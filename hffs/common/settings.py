#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import logging
import os
import configparser
import sys


HFFS_ROOT_DEFAULT = os.path.join(os.path.expanduser("~"), ".cache/hffs_root")
HFFS_ROOT = os.environ.get("HFFS_ROOT", HFFS_ROOT_DEFAULT)
HFFS_ROOT_HOME_CONF = os.path.join(HFFS_ROOT, "home.conf")


def save_home_path(home_path):
    def save_home_path_to_conf(conf_path, home_dir):
        config = configparser.ConfigParser()
        config["DEFAULT"] = {"home_path": home_dir}

        with open(conf_path, "w") as f:
            config.write(f)

    if not os.path.exists(HFFS_ROOT):
        os.makedirs(HFFS_ROOT, exist_ok=True)

    save_home_path_to_conf(HFFS_ROOT_HOME_CONF, home_path)


def get_home_path():
    def load_home_path_from_conf(conf_path):
        config = configparser.ConfigParser()

        if not os.path.exists(conf_path):
            raise LookupError("Home path not set")

        config.read(conf_path)
        return config["DEFAULT"]["home_path"]

    env_home_path = os.environ.get("HFFS_HOME")

    if env_home_path:
        return env_home_path

    try:
        conf_home_path = load_home_path_from_conf(HFFS_ROOT_HOME_CONF)
    except LookupError:
        return HFFS_HOME_DEFAULT
    except Exception:
        _ = 1 + 1   # do nothing, workaround warning python:S2737
        raise

    return conf_home_path


def reset_home_path():
    save_home_path(HFFS_HOME_DEFAULT)


HFFS_HOME_DEFAULT = os.path.join(os.path.expanduser("~"), ".cache/hffs")
HFFS_HOME = get_home_path()
HFFS_PEER_CONF = os.path.join(HFFS_HOME, "hffs_peers.conf")
HFFS_MODEL_DIR = os.path.join(HFFS_HOME, "models")
HFFS_ETAG_DIR = os.path.join(HFFS_HOME, "etags")
HFFS_NOSHARE_CONF = os.path.join(HFFS_HOME, "hffs_noshare.json")
HFFS_TOKEN_ENV_KEY = "HF_TOKEN"
HFFS_CONF = os.path.join(HFFS_HOME, "hffs.conf")
HFFS_LOG_DIR = os.path.join(HFFS_HOME, "logs")
HFFS_EXEC_NAME = "hffs"


HFFS_API_PING = "/hffs_api/ping"
HFFS_API_ALIVE_PEERS = "/hffs_api/alive_peers"
HFFS_API_PEER_CHANGE = "/hffs_api/peer_change"
HFFS_API_STATUS = "/hffs_api/status"
HFFS_API_STOP = "/hffs_api/stop"


def save_local_service_port(port):
    config = configparser.ConfigParser()
    config["DEFAULT"] = {"SERVICE_PORT": str(port)}

    with open(HFFS_CONF, "w") as f:
        config.write(f)


def load_local_service_port():
    config = configparser.ConfigParser()

    if not os.path.exists(HFFS_CONF):
        raise LookupError("Service port not found, have service start?")

    config.read(HFFS_CONF)
    return int(config["DEFAULT"]["SERVICE_PORT"])
