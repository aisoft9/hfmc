#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import configparser

HFFS_HOME_DEFAULT = os.path.join(os.path.expanduser("~"), ".cache/hffs")
HFFS_HOME = os.environ.get("HFFS_HOME", HFFS_HOME_DEFAULT)
HFFS_PEER_CONF = os.path.join(HFFS_HOME, "hffs_peers.conf")
HFFS_MODEL_DIR = os.path.join(HFFS_HOME, "models")
HFFS_ETAG_DIR = os.path.join(HFFS_HOME, "etags")
HFFS_CONF = os.path.join(HFFS_HOME, "hffs.conf")


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
