from enum import Enum, auto
import os

from url.url import *

__all__ = ["HTTPRequest", "FileRequest"]

class HTTPRequest():
    """
    Represents a http request based on url (components), http method, and headers
    """

    def __init__(self, components: HttpURL, method="GET", headers={}) -> None:
        self._method = HTTPMethods[method.upper()]
        self._components = components
        self._headers = headers
        
        self._msg = "{} {} HTTP/1.1".format(self._method.name, self._components.get_path())

        for header, value in self._headers.items():
            self._msg += "\r\n" + "{}: {}".format(header, value)

        self._msg += "\r\n\r\n"

    def __str__(self) -> str:
        return self.get_http_request_text()
    
    def get_scheme(self):
        return self._components.get_scheme()
    
    def get_host(self):
        return self._components.get_host()
    
    def get_original_url(self) -> str:
        return self._components.get_original_url()
    
    def get_http_request_text(self) -> str:
        return self._msg
    
    def get_http_request_bytes(self) -> bytes:
        """
        Return the encoded version (bytes) of http message that
        can be sent through a socket.
        """
        return self._msg.encode("utf8")
    
    def is_get_method(self):
        return self._method == HTTPMethods.GET
    

class FileRequest():
    def __init__(self, components: FileURL) -> None:
        self._components = components

    def is_dir(self) -> bool:
        return os.path.isdir(self._components.get_path())
    
    def get_scheme(self) -> Scheme:
        return self._components.get_scheme()

    def get_path(self) -> str:
        return self._components.get_path()
    


class HTTPMethods(Enum):
    GET = auto()