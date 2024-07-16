"""Context Peer definition for HFFS."""

from dataclasses import dataclass, field


@dataclass(order=True, unsafe_hash=True)
class Peer:
    """Peer definition for HFFS."""

    ip: str = field(hash=True)
    port: int = field(hash=True)
    alive: bool = field(compare=False, default=False)
    epoch: int = field(compare=False, default=0)
