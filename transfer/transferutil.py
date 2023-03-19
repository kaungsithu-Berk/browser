from transfer.socketutil import Socket
from request.request import *
from response.response import *
from url.url import *
from typing import Union

import re, time

__all__ = ['get']

class CacheNode:
    def __init__(self, key, value: dict) -> None:
        self.pre: CacheNode = None
        self.next: CacheNode = None
        self.key = key
        self.value = value

class Cache():
    def __init__(self, capacity=10) -> None:
        self.capacity = capacity
        self.count = 0

        self.cache_hit = 0
        self.cache_access = 0
        
        self.head = CacheNode(0, 0)
        self.tail = CacheNode(0, 0)
        self.head.next = self.tail
        self.head.pre = None
        self.tail.next = None
        self.tail.pre = self.head
        self.map: dict[str, CacheNode] = {}

    def _delete(self, node: CacheNode):
        node.pre.next = node.next
        node.next.pre = node.pre
    
    def _add_to_Head(self, node: CacheNode):
        node.next = self.head.next
        node.next.pre = node
        node.pre = self.head
        node.next = node

    '''
    Cache the http request and the http response in LRU cache. 
    Appropriate is defined as the response is http response with 200
    which contains 'cache-control' header with max-age. For 'cache-control'
    header, only 'no-store' and 'max-age' are supported for now.
    '''
    def _cache_if_appropriate(self, value):
        req, res = value['request'], value['response']

        is_appropriate = isinstance(res, HTTPResponse) and \
            res.get_status_code() == 200 and \
            req.is_get_method() and \
            res.contains_header('cache-control') and \
            'no-store' not in res.get_header_value('cache-control')
        
        if is_appropriate:
            key = req.get_original_url()
            match = re.search(r'max-age=\d+', res.get_header_value('cache-control'))
            if match is None:
                return
            match_gp = match.group()
            max_age = match_gp.replace('max-age=', '')
            age = res.get_header_value('age') if res.contains_header('age') else 0
            value['expires-at'] = int(time.time()) + int(max_age) - int(age)
            self.put(key, value)

    def _is_resource_fresh(self, resource):
        return 'expires-at' in resource and resource['expires-at'] > time.time()
    
    def _cache_miss_get(self, url):
        components = get_url_components(url)
        scheme = components.get_scheme()

        if scheme == Scheme.file:
            resource = _file_get(components)
        else:
            resource = _http_get(components)

        resource = _redirect_if_appropriate(resource)
        self._cache_if_appropriate(resource)

        return resource['request'], resource['response']


    def get(self, key):
        self.cache_access += 1

        if key in self.map.keys():
            node = self.map[key]
            resource = node.value
            if self._is_resource_fresh(resource):
                self._delete(node)
                self._add_to_Head(node)
                self.cache_hit += 1
                return resource['request'], resource['response']
        return self._cache_miss_get(key)

    
    def put(self, key, value):
        if key in self.map.keys():
            node = self.map[key]
            node.value = value
            self._delete(node)
            self._add_to_Head(node)
        else:
            node = CacheNode(key, value)
            self.map[key] = node
            if self.count < self.capacity:
                self.count += 1
                self._add_to_Head(node)
            else:
                self.map.pop(self.tail.pre.key, None)
                self._delete(self.tail.pre)
                self._add_to_Head(node)

CENTRAL_CACHE = Cache()

def get(url) -> Union[HTTPResponse, FileResponse]:
    req, res = CENTRAL_CACHE.get(url)
    return res

REDIRECT_DEPTH = 10

def _redirect_if_appropriate(resource, counter=0):
    if counter >= REDIRECT_DEPTH:
        return resource
    
    req, res = resource['request'], resource['response']
    if isinstance(req, HTTPRequest) and isinstance(res, HTTPResponse):
        if res.is_redirect() and res.contains_header('location'):
            new_url = res.get_header_value('location')
            if new_url.startswith("/"):
                new_url = req.get_scheme() + "://" + req.get_host() + new_url
            components = get_url_components(new_url)
            resource = _http_get(components)
            return _redirect_if_appropriate(resource, counter + 1)
    return resource
    
def _http_get(components: HttpURL) -> dict:
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

    request = FileRequest(components)
    response = create_file_response(request)
    return {'request': request, 'response': response}


    

