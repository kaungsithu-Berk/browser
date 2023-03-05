import enum
from util import *

class Scheme(enum.Enum):
    HTTP = enum.auto()
    HTTPS = enum.auto()
    FILE = enum.auto()

NON_FILE = [Scheme.HTTP, Scheme.HTTPS]

class URLComponents():
    
    def __init__(self, path="/"):
        self.path = path

    def getScheme(self) -> Scheme:
        #return self.components["scheme"]
        raiseNotDefined()

    def getHost(self) -> str:
        # assert self.getScheme() in NON_FILE, \
        #     "No host argument for {} scheme".format(self.getScheme())
        # return self.components["host"]
        raiseNotDefined()

    def getPath(self) -> str:
        # return self.components["path"]
        raiseNotDefined()

    def getPort(self) -> int:
        # assert self.getScheme() in NON_FILE, \
        #     "No port argument for {} scheme".format(self.getScheme())
        # return self.components["port"]
        raiseNotDefined()
    
class HttpURL(URLComponents):
    def __init__(self, url: str) -> None:      
        scheme, url = url.split("://", 1)

        assert scheme.upper() in [definedScheme.name for definedScheme in Scheme],\
            "Unknown scheme: {}".format(scheme)
        self.scheme = Scheme[scheme.upper()]
        
        host, path = url.split("/", 1)
        self.host = host

        path = "/" + path
        self.path = path

        self.port = 80 if self.scheme == Scheme.HTTP else 443
        if ":" in host:
            self.host, port = host.split(":", 1)
            self.port = int(port)


    def getScheme(self) -> Scheme:
        return self.scheme

    def getHost(self) -> str:
        return self.host

    def getPath(self) -> str:
        return self.path
 
    def getPort(self) -> int:
        return self.port
    

class FileURL(URLComponents):
    def __init__(self, url) -> None:
        self.scheme, self.path = url.split("://", 1)

    def getScheme(self) -> Scheme:
        return self.scheme

    def getPath(self) -> str:
        return self.path
    
def getLocationComponents(url: str) -> URLComponents:
    scheme = Scheme[url.split("://")[0].upper()]

    components = URLComponents()
    if scheme in NON_FILE:
        components = HttpURL(url)
    elif scheme == Scheme.FILE:
        components = FileURL(url)

    return components
    

        

