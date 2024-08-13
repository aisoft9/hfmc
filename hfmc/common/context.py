"""Define HFMC context."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import TYPE_CHECKING, List

from hfmc.common.peer import Peer

if TYPE_CHECKING:
    from hfmc.config.hfmc_config import HfmcConfig
    from hfmc.daemon.prober import PeerProber


@dataclass()
class HfmcContext:
    """HFMC context."""

    # properties
    port: int = field()
    model_dir: Path = field()
    etag_dir: Path = field()
    log_dir: Path = field()
    repo_files_dir: Path = field()
    peers: List[Peer] = field()
    peer_prober: PeerProber | None = field(
        default=None,
        init=False,
        repr=False,
    )

    # global context reference
    _instance: HfmcContext | None = field(
        default=None,
        init=False,
        repr=False,
    )

    @classmethod
    def init_with_config(cls, config: HfmcConfig) -> HfmcContext:
        """Create HFMC context from configuration."""
        cls._instance = cls(
            port=config.daemon_port,
            model_dir=Path(config.cache_dir) / "models",
            etag_dir=Path(config.cache_dir) / "etags",
            log_dir=Path(config.cache_dir) / "logs",
            repo_files_dir=Path(config.cache_dir) / "repo_files",
            peers=[Peer(ip=p.ip, port=p.port) for p in config.peers],
        )
        if not cls.get_model_dir().exists():
            cls.get_model_dir().mkdir(parents=True, exist_ok=True)
        if not cls.get_etag_dir().exists():
            cls.get_etag_dir().mkdir(parents=True, exist_ok=True)
        if not cls.get_log_dir().exists():
            cls.get_log_dir().mkdir(parents=True, exist_ok=True)
        if not cls.get_repo_files_dir().exists():
            cls.get_repo_files_dir().mkdir(parents=True, exist_ok=True)
        return cls._instance

    @classmethod
    def get_port(cls) -> int:
        """Get port."""
        if not cls._instance:
            raise ValueError
        return cls._instance.port

    @classmethod
    def get_model_dir(cls) -> Path:
        """Get model dir."""
        if not cls._instance:
            raise ValueError
        return cls._instance.model_dir

    @classmethod
    def get_model_dir_str(cls) -> str:
        """Get model dir in str."""
        return str(cls.get_model_dir())

    @classmethod
    def get_etag_dir(cls) -> Path:
        """Get etag dir."""
        if not cls._instance:
            raise ValueError
        return cls._instance.etag_dir

    @classmethod
    def get_log_dir(cls) -> Path:
        """Get log dir."""
        if not cls._instance:
            raise ValueError
        return cls._instance.log_dir

    @classmethod
    def get_repo_files_dir(cls) -> Path:
        """Get repo file list dir."""
        if not cls._instance:
            raise ValueError
        return cls._instance.repo_files_dir

    @classmethod
    def get_peers(cls) -> List[Peer]:
        """Get peers."""
        if not cls._instance:
            raise ValueError
        return cls._instance.peers

    @classmethod
    def update_peers(
        cls,
        conf: HfmcConfig,
        old_peers: List[Peer],
    ) -> List[Peer]:
        """Load peers from config and then update their states."""
        if not cls._instance:
            raise ValueError

        new_peers = [Peer(ip=p.ip, port=p.port) for p in conf.peers]
        peer_map = {p: p for p in new_peers}

        for peer in old_peers:
            if peer in peer_map:  # peer match by ip and port
                peer_map[peer].alive = peer.alive
                peer_map[peer].epoch = peer.epoch

        cls._instance.peers = list(peer_map.values())

        return cls._instance.peers

    @classmethod
    def get_daemon(cls) -> Peer:
        """Get local daemon."""
        if not cls._instance:
            raise ValueError
        return Peer(ip="127.0.0.1", port=cls._instance.port)

    @classmethod
    def set_peer_prober(cls, peer_prober: PeerProber) -> None:
        """Set peer prober."""
        if not cls._instance:
            raise ValueError
        cls._instance.peer_prober = peer_prober

    @classmethod
    def get_peer_prober(cls) -> PeerProber:
        """Get peer prober."""
        if not cls._instance:
            raise ValueError
        if not cls._instance.peer_prober:
            raise ValueError
        return cls._instance.peer_prober
