"""Settings for HFMC daemon service."""

from aiohttp import ClientTimeout

ApiType = str

API_PREFIX: ApiType = "/hfmc_api/{service}"

API_PEERS_PROBE: ApiType = API_PREFIX.format(service="peers/ping")

API_DAEMON_RUNNING: ApiType = API_PREFIX.format(service="daemon/status")
API_DAEMON_STOP: ApiType = API_PREFIX.format(service="daemon/stop")
API_DAEMON_PEERS_ALIVE: ApiType = API_PREFIX.format(
    service="daemon/peers_alive",
)
API_DAEMON_PEERS_CHANGE: ApiType = API_PREFIX.format(
    service="daemon/peers_change",
)

API_FETCH_FILE_CLIENT: ApiType = "/{repo}/resolve/{revision}/{file_name}"
API_FETCH_FILE_DAEMON: ApiType = "/{user}/{model}/resolve/{revision}/{file_name:.*}"
API_FETCH_REPO_FILE_LIST: ApiType = API_PREFIX.format(
    service="fetch/repo_file_list/{user}/{model}/{revision}"
)


# timeout in sec
TIMEOUT_PEERS = ClientTimeout(total=10)
TIMEOUT_DAEMON = ClientTimeout(total=2)
TIMEOUT_FETCH = ClientTimeout(total=30)
