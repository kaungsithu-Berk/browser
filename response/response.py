from io import BufferedReader
from zlib import decompress
from typing import Union

__all__ = ['HTTPResponse', 'FileResponse', 'create_http_response', 'create_file_response',\
           'Text', 'Element', 'HTMLParser']

class Response:
    """
    The base class for all responses. All responses have a body. (?)
    """
    def __init__(self, body: str) -> None:
        self.body = Body(body)

    def get_raw_body(self):
        return self.body.get_raw_body()
    
class HTTPResponse(Response):
    """
    Represents an HTTP response using status line, headers, and the response body.
    """
    def __init__(self, status_line: str, headers: dict, body: str) -> None:
        Response.__init__(self, body)
        self.status = HTTPStatus(status_line)
        self.header = HTTPResponseHeader(headers)

    def is_redirect(self) -> bool:
        """
        Returns if the response is a redirect.
        """
        return self.get_status_code() in range(300, 400)

    def get_status_code(self) -> int:
        """
        Returns the status code of the response.
        """
        return self.status.get_status_code()

    def get_status_line(self):
        """
        Returns the status line.
        """
        return self.status.get_status_line()
    
    def contains_header(self, header_name):
        """
        Returns if the response contains a header
        """
        return header_name in self.header._headers
    
    def get_header_value(self, header_name):
        """
        Returns the value of the header in the repsonse
        """
        assert self.contains_header(header_name)
        return self.header._headers[header_name]

class FileResponse(Response):

    def __init__(self, body: str) -> None:
        Response.__init__(self, body)

def create_http_response(stream: BufferedReader) -> HTTPResponse:
    """
    Create an HTTP response object by reading the buffered stream (possibly from the socket)

    The function parses the headers first.
    Then if the transfer-encoding is chuncked, the body is read accordingly.
    Also, if the body is content-encoded with gzip, it is decompressed accordingly.
    """
    headers = {}
    status_line = stream.readline().decode('utf8')
    while True:
        line = stream.readline().decode('utf8')
        if line == "\r\n": break
        header, value = line.split(":", 1)
        headers[header.lower()] = value.strip()

    if 'transfer-encoding' in headers and headers['transfer-encoding'] == 'chunked':
        chunks = []
        while True:
            length = stream.readline().decode('utf8')
            length = int(length.replace('\r\n', ''), 16)
            chunk = stream.read(length)
            chunks.append(chunk)
            stream.readline()
            if length == 0:
                break
        body = b''.join(chunks)
    else:
        body = stream.read()

    if 'content-encoding' in headers and headers['content-encoding'] == 'gzip':
        body = decompress(body, wbits=31).decode('utf8')
    else:
        body = body.decode('utf8')
    stream.close()
    return HTTPResponse(status_line, headers, body)

def create_file_response(stream: Union[BufferedReader, list[str]]) -> FileResponse:
    """
    Creates a FileResponse object based on the stream.
    The stream could be a file content or the result of the call to the directory list.
    """
    body = ""
    if isinstance(stream, BufferedReader):
        body = stream.read()
        stream.close()
    elif isinstance(stream, list):
        body = stream.__str__()[1:-1]
        body = body.replace(", ", "\r\n")
    return FileResponse(body)

# HELPER CLASSES

class Body:
    """
    Represents the body of a response.
    """
    def __init__(self, body: str) -> None:
        self.body = body
    
    def __iter__(self):
        return iter(self.body)

    def __str__(self) -> str:
        return self.body
    
    def get_raw_body(self):
        return self.body


class HTTPStatus:
    """
    Represents the status line of the http response.
    """
    def __init__(self, status_line: str) -> None:
        self._status_line = status_line
    
    def get_http_response_version(self) -> str:
        """
        Returns http version. For example, "HTTP/1.1"
        """
        return self._status_line.split(" ")[0]

    def get_status_code(self) -> int:
        """
        Returns the status code of the response.
        """
        return int(self._status_line.split(" ")[1])
    
    def get_reason_pharse(self) -> str:
        """
        Returns the status reason associated with the status code.
        """
        return self._status_line.split(" ")[2]
    
    def get_status_line(self):
        """
        Returns the whole status line.
        """
        return self._status_line
    
class HTTPResponseHeader:
    """
    HTTP response headers.
    """
    def __init__(self, headers: dict) -> None:
        self._headers = headers

#############################################
#           Helper Classes to parse HTML    #
#############################################

class Text:
    """
    A text string in html. It has a parent who is a tag in html.
    The children attribute is added to avoid isinstance calls in the 
    clients.
    """
    def __init__(self, text, parent) -> None:
        self.text = text
        self.children = [] # to avoid isinstance with Element
        self.parent = parent

    def __repr__(self):
        return repr(self.text)

class Element:
    """
    A tag in the html. It has children of Element or Text.
    It could also have a parent of Element.
    """
    def __init__(self, tag, attributes, parent) -> None:
        self.tag = tag
        self.attributes = attributes
        self.children = []
        self.parent = parent

    def __repr__(self):
        return "<" + repr(self.tag) + ">"

SELF_CLOSING_TAGS = [
    "area", "base", "br", "col", "embed", "hr", "img", "input",
    "link", "meta", "param", "source", "track", "wbr",
]

HEAD_TAGS = [
    "base", "basefont", "bgsound", "noscript",
    "link", "meta", "title", "style", "script",
]


class HTMLParser:
    """
    
    """
    def __init__(self, body):
        self.body = body
        self.unfinished = []

    def parse(self):
        text = ""
        in_tag = False
        for c in self.body:
            if c == "<":
                in_tag = True
                if text: self._add_text(text)
                text = ""
            elif c == ">":
                in_tag = False
                self._add_tag(text)
                text = ""
            else:
                text += c
        if not in_tag and text:
            self._add_text(text)
        return self._finish()

    def _add_text(self, text):
        if text.isspace(): return
        self._add_implicit_tags(None)
        parent = self.unfinished[-1]
        node = Text(text, parent)
        parent.children.append(node)

    def _add_tag(self, tag):
        tag, attributes = self._get_attributes(tag)
        if tag.startswith("!"): return
        self._add_implicit_tags(tag)
        if tag.startswith("/"):
            if len(self.unfinished) == 1: return
            node = self.unfinished.pop()
            parent = self.unfinished[-1]
            parent.children.append(node)
        elif tag in SELF_CLOSING_TAGS:
            parent = self.unfinished[-1]
            node = Element(tag,attributes, parent)
            parent.children.append(node)
        else:
            parent = self.unfinished[-1] if self.unfinished else None
            node = Element(tag, attributes, parent)
            self.unfinished.append(node)

    def _finish(self):
        if len(self.unfinished) == 0:
            self._add_tag("html")
        while len(self.unfinished) > 1:
            node = self.unfinished.pop()
            parent = self.unfinished[-1]
            parent.children.append(node)
        return self.unfinished.pop()
    
    def _get_attributes(self, text):
        parts = text.split()
        tag = parts[0].lower()
        attributes = {}
        for pair in parts[1:]:
            if "=" in pair:
                key, value = pair.split("=", 1)
                if len(value) > 2 and value[0] in ["'", "\""]:
                    value = value[1:-1]
                attributes[key.lower()] = value
            else:
                attributes[pair.lower()] = ""
        return tag, attributes

    def _add_implicit_tags(self, tag):
        while True:
            open_tags = [node.tag for node in self.unfinished]
            if open_tags == [] and tag != "html":
                self._add_tag("html")
            elif open_tags == ["html"] and tag not in ["head", "body", "/html"]:
                if tag in HEAD_TAGS:
                    self._add_tag("head")
                else:
                    self._add_tag("body")
            elif open_tags == ["html", "head"] and \
                tag not in ["/head"] + HEAD_TAGS:
                self._add_tag("/head")
            else:
                break
            



    
    

