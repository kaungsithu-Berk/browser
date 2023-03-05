class ConnectionLog:
    def __init__(self) -> None:
        self.valid_keys = {}
        self.log = {}

    def add(self, key, value):
        assert key in self.valid_keys
        self.log[key] = value

class HttpLog(ConnectionLog):
    def __init__(self) -> None:
        ConnectionLog.__init__()
        self.valid_keys = {"url", "http_request", "http_response"}

class FileLog(ConnectionLog):
    def __init__(self) -> None:
        ConnectionLog.__init__()
        self.valid_keys = {"path", "file_response"}
        