

class Peer:
    def __init__(self, ip, port) -> None:
        self._ip = ip
        self._port = int(port)
        self._alive = False
        self._epoch = 0

    @property
    def ip(self):
        return self._ip

    @property
    def port(self):
        return self._port

    def is_alive(self):
        return self._alive

    def set_alive(self, alive):
        self._alive = alive

    def set_epoch(self, epoch):
        self._epoch = epoch

    def get_epoch(self):
        return self._epoch

    def __lt__(self, value):
        if not isinstance(value, Peer):
            raise TypeError()
        if self.ip < value.ip:
            return True
        elif self.port < value.port:
            return True
        else:
            return False

    def __eq__(self, value: object) -> bool:
        return isinstance(value, Peer) and self.ip == value.ip and self.port == value.port

    def __hash__(self) -> int:
        return hash((self.ip, self.port))

    def __repr__(self) -> str:
        return f"{self.ip}:{self.port}"

    def to_dict(self):
        return {
            "ip": self.ip,
            "port": self.port
        }

    @classmethod
    def from_dict(cls, data):
        return cls(data["ip"], data["port"])

    @classmethod
    def print_peers(cls, peers):
        return [f"{p}" for p in peers]
