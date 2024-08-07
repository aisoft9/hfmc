"""Test HffsContext."""

from pytest import fixture

from hffs.common.context import HffsContext
from hffs.common.peer import Peer as ContextPeer
from hffs.config.hffs_config import HffsConfig, Peer


@fixture()
def test_config() -> HffsConfig:
    """Return a test HffsConfig."""
    return HffsConfig(
        cache_dir="test_cache_dir",
        peers=[Peer(ip="127.0.0.1", port=8081)],
        daemon_port=8088,
    )


def test_port(test_config: HffsConfig) -> None:
    """Test get port."""
    context = HffsContext.init_with_config(test_config)
    assert context.port == test_config.daemon_port


def test_model_dir(test_config: HffsConfig) -> None:
    """Test get model dir."""
    context = HffsContext.init_with_config(test_config)
    assert str(context.model_dir) == "test_cache_dir/models"


def test_etag_dir(test_config: HffsConfig) -> None:
    """Test get etag dir."""
    context = HffsContext.init_with_config(test_config)
    assert str(context.etag_dir) == "test_cache_dir/etags"


def test_log_dir(test_config: HffsConfig) -> None:
    """Test log dir."""
    context = HffsContext.init_with_config(test_config)
    assert str(context.log_dir) == "test_cache_dir/logs"


def test_get_peers(test_config: HffsConfig) -> None:
    """Test get peers."""
    context = HffsContext.init_with_config(test_config)
    assert len(context.peers) == 1

    act_peer = context.peers[0]
    exp_peer = test_config.peers[0]
    assert act_peer.ip == exp_peer.ip
    assert act_peer.port == exp_peer.port
    assert act_peer.alive is False
    assert act_peer.epoch == 0


def test_update_peers() -> None:
    """Test update peers."""
    num_peers = 2
    ip_1, ip_2, ip_3 = "127.0.0.1", "127.0.0.2", "127.0.0.3"
    port_1, port_2, port_3 = 8081, 8082, 8083

    old_conf = HffsConfig(
        peers=[
            Peer(ip=ip_1, port=port_1),
            Peer(ip=ip_2, port=port_2),
        ],
    )
    old_context = HffsContext.init_with_config(old_conf)
    assert len(old_context.peers) == num_peers

    old_context.peers[0].alive = True
    old_context.peers[0].epoch = 42

    new_conf = HffsConfig(
        peers=[
            Peer(ip=ip_1, port=port_1),
            Peer(ip=ip_3, port=port_3),
        ],
    )

    new_peers = HffsContext.update_peers(new_conf, old_context.peers)

    assert len(new_peers) == num_peers
    assert ContextPeer(ip=ip_1, port=port_1, alive=True, epoch=42) in new_peers
    assert ContextPeer(ip=ip_3, port=port_3, alive=False, epoch=0) in new_peers