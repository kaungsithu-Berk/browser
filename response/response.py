from io import BufferedReader
from zlib import decompress
from typing import Union

__all__ = ['HTTPResponse', 'FileResponse', 'create_http_response', 'create_file_response',\
           'Text', 'Tag']

class Response:
        
    def __init__(self, body: str) -> None:
        self.body = Body(body)

    def get_raw_body(self):
        return [Text(self.body)]
    
class HTTPResponse(Response):

    def __init__(self, status_line: str, headers: dict, body: str) -> None:
        Response.__init__(self, body)
        self.status = HTTPStatus(status_line)
        self.header = HTTPHeader(headers)

    def is_redirect(self) -> bool:
        return self.get_status_code() in range(300, 400)

    def get_status_code(self) -> int:
        return self.status.get_status_code()

    def get_status_line(self):
        return self.status.get_status_line()
    
    def contains_header(self, header_name):
        return header_name in self.header._headers
    
    def get_header_value(self, header_name):
        assert self.contains_header(header_name)
        return self.header._headers[header_name]

    # def get_tags_and_texts(self):
    #     out = []
    #     text = ""
    #     in_tag = False
    #     for c in self.body:
    #         if c == "<":
    #             in_tag = True
    #             if text: out.append(Text(text))
    #             text = ""
    #         elif c == ">":
    #             in_tag = False
    #             out.append(Tag(text))
    #             text = ""
    #         else:
    #             text += c
    #     if not in_tag and text:
    #         out.append(Text(text))
    #     return out

class FileResponse(Response):

    def __init__(self, body: str) -> None:
        Response.__init__(self, body)

def create_http_response(stream: BufferedReader) -> HTTPResponse:
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
    def __init__(self, body: str) -> None:
        self.body = body
    
    def __iter__(self):
        return iter(self.body)

    def __str__(self) -> str:
        return self.body
    
    def get_raw_body(self):
        return self.body


class HTTPStatus:
    def __init__(self, status_line: str) -> None:
        self._status_line = status_line
    
    def get_http_response_version(self) -> str:
        return self._status_line.split(" ")[0]

    def get_status_code(self) -> int:
        return int(self._status_line.split(" ")[1])
    
    def get_reason_pharse(self) -> str:
        return self._status_line.split(" ")[2]
    
    def get_status_line(self):
        return self._status_line
    
class HTTPHeader:
    def __init__(self, headers: dict) -> None:
        self._headers = headers

class Text:
    def __init__(self, text, parent) -> None:
        self.text = text
        self.children = []
        self.parent = parent # to avoid isinstance with Element

class Element:
    def __init__(self, tag, parent) -> None:
        self.tag = tag
        self.children = []
        self.parent = parent

class HTMLParser:
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
        return self.finish()

    def _add_text(self, text):
        parent = self.unfinished[-1]
        node = Text(text, parent)
        parent.children.append(node)

    def _add_tag(self, tag):
        if tag.startswith("/"):
            node = self.unfinished.pop()
            parent = self.unfinished[-1]
            parent.children.append(node)
        else:
            parent = self.unfinished[-1]
            node = Element(tag, parent)
            self.unfinished.append(node)

    
    

