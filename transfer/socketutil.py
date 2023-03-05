import socket
import ssl
from io import TextIOWrapper

from url.urlutil import URLComponents, Scheme

class Socket:
    
    def __init__(self, family=socket.AF_INET, type=socket.SOCK_STREAM, proto=socket.IPPROTO_TCP) -> None:
        self.family = family
        self.type = type
        self.proto = proto

        self.socket = socket.socket(
            family=self.family,
            type=self.type,
            proto=self.proto,
        )


    def connect(self, components: URLComponents):
        assert self.family == socket.AF_INET
        self.host = components.getHost()
        self.port = components.getPort()
        self.scheme = components.getScheme()

        self.socket.connect((self.host, self.port))

        if  self.scheme == Scheme.HTTPS:
            ctx = ssl.create_default_context()
            self.socket = ctx.wrap_socket(self.socket, server_hostname=self.host)
    
    def send(self, msg: str|bytes):
        if isinstance(msg, str):
            msg = msg.encode("utf8")
        
        totalSent = 0
        while totalSent < len(msg):
            sent = self.socket.send(msg[totalSent:])
            if sent == 0:
                raise RuntimeError("Socket is so dead")
            totalSent += sent

        assert totalSent == len(msg)
    
    def receive(self) -> TextIOWrapper:
        return self.socket.makefile("r", encoding="utf8", newline="\r\n")
    
    def disconnect(self):
        self.socket.shutdown(socket.SHUT_RDWR)
        self.socket.close()





    