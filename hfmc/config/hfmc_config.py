"""HFMC Configuration Class."""

from __future__ import annotations

from enum import Enum
from pathlib import Path
from typing import List

from pydantic import BaseModel, Field

CONFIG_DIR = Path.home() / ".hfmc"
CONFIG_FILE = CONFIG_DIR / "config.yaml"

DEFAULT_CACHE_DIR = Path.home() / ".cache" / "hfmc"
DEFAULT_DAEMON_PORT = 9090


class Peer(BaseModel):
    """Peer definition for HFMC."""

    ip: str = Field(exclude=False, frozen=True)
    port: int = Field(exclude=False, frozen=True)

    def __lt__(self, other: object) -> bool:
        """Return True if self is less than other."""
        if isinstance(other, Peer):
            return self.ip < other.ip or (
                self.ip == other.ip and self.port < other.port
            )
        return NotImplemented

    def __eq__(self, other: object) -> bool:
        """Return True if self is equal to other."""
        if isinstance(other, Peer):
            return self.ip == other.ip and self.port == other.port
        return NotImplemented

    def __hash__(self) -> int:
        """Return the hash value of the Peer."""
        return hash((self.ip, self.port))


class HfmcConfigOption(str, Enum):
    """HFMC configuration options."""

    CACHE: str = "cache_dir"
    PORT: str = "daemon_port"
    PEERS: str = "peers"


class HfmcConfig(BaseModel):
    """Data class for HFMC directory configuration."""

    cache_dir: str = Field(
        description="Directory for storing cache files",
        default=str(DEFAULT_CACHE_DIR),
    )

    peers: List[Peer] = Field(
        description="List of peers",
        default_factory=list,
    )

    daemon_port: int = Field(
        description="Port for the daemon",
        default=DEFAULT_DAEMON_PORT,
    )
