from transfer.socketutil import Socket
from request.request import *
from response.response import *
from response.responseutil import *
from url.urlutil import *

class Cache():

    class Node:
        def __init__(self, key, value) -> None:
            self.pre = None
            self.next = None
            self.key = key
            self.value = value

    def __init__(self, capacity=10) -> None:
        self.capacity = capacity
        self.count = 0

        self.cache_hit = 0
        self.cache_access = 0
        
        self.head = self.Node(0, 0)
        self.tail = self.Node(0, 0)
        self.head.next = self.tail
        self.head.pre = None
        self.tail.next = None
        self.tail.pre = self.head
        self.map = {}

    def delete(self, node: Node):
        node.pre.next = node.next
        node.next.pre = node.pre
    
    def addToHead(self, node: Node):
        node.next = self.head.next
        node.next.pre = node
        node.pre = self.head
        node.next = node

    def get(self, key) -> bool:
        self.cache_access += 1
        result = None
        if key in self.map.keys():
            node = self.map[key]
            result = node.value
            self.delete(node)
            self.addToHead(node)
            self.cache_hit += 1

        if result is None:
            result = cache_miss_get(key)
            self.put(key, result)
        return result
    
    def put(self, key, value):
        if key in self.map.keys():
            node = self.map[key]
            node.value = value
            self.delete(node)
            self.addToHead(node)
        else:
            node = self.Node(key, value)
            self.map[key] = node
            if self.count < self.capacity:
                self.count += 1
                self.addToHead(node)
            else:
                self.map.pop(self.tail.pre.key, None)
                self.delete(self.tail.pre)
                self.addToHead(node)

    def printCacheStats(self):
        print("Access: ", self.cache_access, ", Hits: ", self.cache_hit)


CENTRAL_CACHE = Cache()

def get(url) -> Response:
    CENTRAL_CACHE.printCacheStats()
    return CENTRAL_CACHE.get(url)

def cache_miss_get(url) -> Response:
    components = getLocationComponents(url)
    scheme = components.getScheme()

    if scheme == Scheme.FILE:
        return fileGet(components.getPath())
    
    return httpGet(components)


def httpGet(components: URLComponents) -> HTTPResponse:
    httpSocket = Socket()
    httpSocket.connect(components)
    httpSocket.send(createHTTPRequest(method="GET", path=components.getPath(), \
                                      headers={"Host": components.getHost(),\
                                                "Connection": "close",\
                                                "User-Agent": "Awesome Browser"}).get_encoded_msg())
    response = createHTTPResponse(httpSocket.receive())
    httpSocket.disconnect()
    return response

def fileGet(path) -> FileResponse:
    print(path)
    f = open(path)
    return createFileResponse(f)


    

