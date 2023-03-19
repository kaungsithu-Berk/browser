import socket, ssl
from io import BufferedReader
from typing import Union

from url.url import *

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

    def connect(self, components):
        assert self.family == socket.AF_INET
        print(components.get_original_url())
        self.host = components.get_host()
        self.port = components.get_port()
        self.scheme = components.get_scheme()

        self.socket.connect((self.host, self.port))

        if self.scheme == Scheme.https:
            ctx = ssl.create_default_context()
            self.socket = ctx.wrap_socket(self.socket, server_hostname=self.host)
                
    def send(self, msg: Union[str, bytes]):
        if isinstance(msg, str):
            msg = msg.encode("utf8")
        
        totalSent = 0
        while totalSent < len(msg):
            sent = self.socket.send(msg[totalSent:])
            if sent == 0:
                raise RuntimeError("Socket is so dead")
            totalSent += sent

        assert totalSent == len(msg)
    
    def receive(self) -> BufferedReader:
        return self.socket.makefile("rb", newline="\r\n")
    
    def disconnect(self):
        self.socket.shutdown(socket.SHUT_RDWR)
        self.socket.close()





    