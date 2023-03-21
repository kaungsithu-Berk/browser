from transfer.socketutil import Socket
from request.request import *
from response.response import *
from url.url import *
from typing import Union

import re, time

__all__ = ['get']

class CacheNode:
    """
    A slot in the LRU cache because the cache will be designed as a circular doubly linked list.
    pre  : The previous cache slot in the cache
    next : The next cache slot in the cache
    key  : Identifier for the value (see class Cache)
    value: What the cache stores for this specific key. In cache implementation, it is
           a dictionary of request.request.HTTPRequest object and response.response.HTTPResponse
           object. If the cache has expiration time, the remaining time is also added to the dictionary.
    """
    def __init__(self, key, value: dict) -> None:
        self.pre: CacheNode = None
        self.next: CacheNode = None
        self.key = key
        self.value = value

class Cache:
    """
    The LRU cache with 'capacity' slots. Cache nodes 'head' and 'tail' are to facilitate 
    the access to the first and last "actual" cache nodes in the cache. 
    
    The further from the head node, the less the node is recently used 
    with the head.next being the most recent and the tail.next being
    the least recently used.

    The attribute 'self.map' saves a dictionary of (url, corresponding cache nodes) to provide 
    fast access to any cache node in the cache rather than simple first and last cache nodes that
    is provided by the 'self.head' and 'self.tail'. Cache nodes also need to keep their own keys
    because we need the key to find in the map after we identify the least recently used cache node
    through tail.pre (see self.put(key, value)).
    """
    def __init__(self, capacity=10) -> None:
        self.capacity = capacity
        self.count = 0 # current capacity

        self.cache_hit = 0
        self.cache_access = 0
        
        self.head = CacheNode(None, None)
        self.tail = CacheNode(None, None)

        self.head.next = self.tail
        self.head.pre = None
        self.tail.next = None
        self.tail.pre = self.head
        self.map: dict[str, CacheNode] = {}

    def get(self, key) -> tuple:
        """
        Retrieve the cache node using the key while updating 
        according to the LRU policy.
        If the cache misses or the cache nodes expires, the cache retrieves
        the resources from the internet with self._cache_miss_get(key).
        """
        self.cache_access += 1

        if key in self.map.keys():
            node = self.map[key]
            value = node.value
            if self._is_resource_fresh(value):
                self.cache_hit += 1
                self._delete(node)
                self._add_to_head(node)
                return value['request'], value['response']
        return _cache_miss_get(key)
    
    def put(self, key, value):
        """
        Put the key-value pair in the self.map and to the next of the head.
        If the self.map is full, remove the least recently used cache node.
        """
        if key in self.map.keys():
            node = self.map[key]
            node.value = value
            self._delete(node)
            self._add_to_head(node)
        else:
            node = CacheNode(key, value)
            self.map[key] = node
            if self.count < self.capacity:
                self._add_to_head(node)
            else:
                self.map.pop(self.tail.pre.key, None)
                self._delete(self.tail.pre)
                self._add_to_head(node)
    
    def _is_resource_fresh(self, resource):
        """
        Return if the cache node has not expired.
        """
        return 'expires-at' in resource and resource['expires-at'] > time.time()

    def _delete(self, node: CacheNode):
        """
        Delete a cache slot from the cache by changing its 
        pointers.
        """
        node.pre.next = node.next
        node.next.pre = node.pre
        self.count -= 1
    
    def _add_to_head(self, node: CacheNode):
        """
        Move the node to head.next effectively making it the most recent
        used cache node. The subsequent cache nodes' recent usages are moved back
        inherently.

        WARNING: This function only changes the next's and pre's of the input node and
        the head. node.pre.next and node.next.pre are still pointing to the node. 
        Call self._delete(node) if neccessary.
        """
        node.next = self.head.next
        self.head.next.pre = node
        
        node.pre = self.head
        self.head.next = node
        self.count += 1

"""
The cache of the browser
"""
CENTRAL_CACHE = Cache()

def get(url) -> Union[HTTPResponse, FileResponse]:
    """
    Use the browser cache to get the resources at the url.
    The cache miss cases are handled in the Cache class.
    """
    _, res = CENTRAL_CACHE.get(url)
    return res



################################################
#               HELPER METHODS                 #
################################################


def _cache_miss_get(url):
    """
    The key/url is not in the self.map.
    Fetch the response from the internet using the url while 
    redirecting and/or caching the response according to the LRU policy.
    """
    components = get_url_components(url)
    scheme = components.get_scheme()

    if scheme == Scheme.file:
        value = _file_get(components)
    elif scheme in [Scheme.http, Scheme.https]:
        value = _http_get(components)

    value = _redirect_if_appropriate(value)
    _cache_if_appropriate(value)

    return value['request'], value['response']


def _cache_if_appropriate(value):
    """
    Cache the http request and the http response in LRU cache if appropriate.

    Appropriate in current implementation is defined as
    1. The request and the response are through HTTP connection AND
    2. The request is a GET method AND
    3. The response is an http response with 200 status code AND
    4. The response contains cache-control header without "no-store" value. 
    
    For cache-control header, only "no-store" and "max-age" values are supported.
    """
    req, res = value['request'], value['response']

    is_appropriate = isinstance(req, HTTPRequest) and \
        isinstance(res, HTTPResponse) and \
        res.get_status_code() == 200 and \
        req.is_get_method() and \
        res.contains_header('cache-control') and \
        'no-store' not in res.get_header_value('cache-control')
    
    if is_appropriate:
        key = req.get_original_url()

        match = re.search(r'max-age=\d+', res.get_header_value('cache-control'))
        if match is None: return
        match_gp = match.group()

        max_age = match_gp.replace('max-age=', '')
        age = res.get_header_value('age') if res.contains_header('age') else 0
        value['expires-at'] = int(time.time()) + int(max_age) - int(age)

        CENTRAL_CACHE.put(key, value)


REDIRECT_DEPTH = 10

def _redirect_if_appropriate(value, counter=0):
    """
    Redirect based on the http response headers up to REDIRECT_DEPTH depths.
    The new url is either completely in the "location" header or we have to reuse
    the original hostname using the path in the "location" header. 
    """
    if counter >= REDIRECT_DEPTH:
        return value
    
    req, res = value['request'], value['response']
    if isinstance(req, HTTPRequest) and isinstance(res, HTTPResponse):
        if res.is_redirect() and res.contains_header('location'):
            new_url = res.get_header_value('location')
            if new_url.startswith("/"):
                new_url = req.get_scheme() + "://" + req.get_host() + new_url
            components = get_url_components(new_url)
            value = _http_get(components)
            return _redirect_if_appropriate(value, counter + 1)
        
    return value
    
def _http_get(components: HttpURL) -> dict:
    """
    Return a (request, response) tuple from http connection. 
     
    The socket is created usign the HttpURL object.

    The request is created using the HttpURL object and a set of headers ("Host",
    "Connetion", "User-Agent", "Accept-Encoding").

    The request is received through Socket object and created as a 
    response.response.HTTPResponse object.
    """
    httpSocket = Socket()
    httpSocket.connect(components)

    headers = {"Host": components.get_host(),\
                "Connection": "close",\
                "User-Agent": "Awesome Browser",\
                "Accept-Encoding": "gzip"}
    request = HTTPRequest(components, headers=headers)

    httpSocket.send(request.get_http_request_bytes())
    response = create_http_response(httpSocket.receive())
    httpSocket.disconnect()
    return {'request': request, 'response': response}

def _file_get(components: FileURL) -> dict:

    """
    Return a (request, response) tuple from disk.    
    """
    request = FileRequest(components)
    response = create_file_response(request)
    return {'request': request, 'response': response}


    

