from enum import Enum, auto
from util import *
from typing import Union

__all__ = ['Scheme', 'get_url_components', 'HttpURL', 'FileURL']

class Scheme(Enum):
    http = auto()
    https = auto()
    file = auto()

class HttpURL():
    def __init__(self, url: str) -> None:
        self._original_url = url      
        scheme, url = url.split("://", 1)
        
        try:
            self._scheme = Scheme[scheme.lower()]

        except KeyError:
            print("Unknown scheme: {}".format(scheme))
        
        host, path = url.split("/", 1)
        self._host = host

        path = "/" + path
        self._path = path

        self._port = 80 if self._scheme == Scheme.http else 443
        if ":" in self._host:
            self._host, port = self._host.split(":", 1)
            self._port = int(port)


    def get_scheme(self) -> Scheme:
        return self._scheme

    def get_host(self) -> str:
        return self._host

    def get_path(self) -> str:
        return self._path
 
    def get_port(self) -> int:
        return self._port
    
    def get_original_url(self) -> str:
        return self._original_url    

class FileURL():
    def __init__(self, url: str) -> None:
        scheme, path = url.split("://", 1)
        self._scheme = Scheme[scheme.lower()]
        self._path = path

    def get_scheme(self) -> Scheme:
        return self._scheme

    def get_path(self) -> str:
        return self._path
    
def get_url_components(url: str) -> Union[HttpURL, FileURL]:
    url = _preprocess_url(url)
    scheme = Scheme[url.split("://", 1)[0].lower()]

    if scheme in [Scheme.http, Scheme.https]:
        return HttpURL(url)
    elif scheme == Scheme.file:
        return FileURL(url)

    return None

def _preprocess_url(url: str):
    if len(url.split("://", 1)) < 2:
        url = "http://" + url
    elif len(url.split("://", 1)[0]) == 0:
        url = "http" + url
    
    _, host = url.split("://")

    if len(host.split("/", 1)) < 2:
        url += "/"

    return url
    

        

