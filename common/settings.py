import os

HFFS_HOME_DEFAULT = os.path.join(os.path.expanduser("~"), ".cache/hffs")
HFFS_HOME = os.environ.get("HFFS_HOME", HFFS_HOME_DEFAULT)
HFFS_PEER_CONF = os.path.join(HFFS_HOME, "hffs_peers.conf")
HFFS_MODEL_DIR = os.path.join(HFFS_HOME, "models")
