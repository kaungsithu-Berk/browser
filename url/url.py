from enum import Enum, auto
from util import *
from typing import Union

__all__ = ['Scheme', 'get_url_components', 'HttpURL', 'FileURL']


class Scheme(Enum):
    """
    Instead of saving the scheme as a string, it is represented as 
    an Enum and all classes should have the scheme of this type, not string.
    """
    http = auto()
    https = auto()
    file = auto()

class HttpURL():
    """
        Define the split version of url string if the scheme is http/https.
        When port number is not provided, default port number for http/https are 
        used: 80 and 443 respectively. 
    """
    def __init__(self, url: str) -> None:
        self._original_url = url      
        scheme, url = url.split("://", 1)
        self._scheme = Scheme[scheme.lower()]

        host, path = url.split("/", 1)
        self._host = host

        path = "/" + path
        self._path = path

        self._port = 80 if self._scheme == Scheme.http else 443

        if ":" in self._host:
            self._host, port = self._host.split(":", 1)
            try:
                self._port = int(port)
            except ValueError:
                raise ValueError("Invalid port in the URL: {}".format(port))

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
    """
    Get the [scheme]URL objects from the url string.

    The function will raise 
    1. KeyError if the scheme is not supported by the browser
    2. ValueError if the provided port number is not valid.
    """
    url = _preprocess_url(url)
    scheme = Scheme[url.split("://", 1)[0].lower()]
    if scheme in [Scheme.http, Scheme.https]:
        return HttpURL(url)
    elif scheme == Scheme.file:
        return FileURL(url)

def _preprocess_url(url: str):
    """
    Preprocess (see below) the url string that does not properly include a scheme and a path.
    If the scheme is not supported, raise KeyError.

    Preprocessing:
    1. If there is no "://" string, prepend http scheme and "://" string.
    2. Otherwise, if there is no scheme, just prepend http scheme.
    3. Add a path "/" if there is no path.

    The resulting url does not guarantee a valid url address but it should be able to 
    pass to the point of connection.
    """
    url_split = url.split("://", 1)

    # The split being less than 2 means there is no :// string.
    # Otherwise, check for the empty scheme.
    if len(url_split) < 2:
        url = "http://" + url
    elif len(url_split[0]) == 0:
        url = "http" + url
    
    scheme, host = url.split("://", 1)

    try:
        Scheme[scheme.lower()]
    except KeyError:
        raise KeyError("Invalid scheme in the URL: {}".format(scheme.lower()))

    if len(host.split("/", 1)) < 2:
        url += "/"

    return url    

        

