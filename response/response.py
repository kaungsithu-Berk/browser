class Response:

    class Body:
        def __init__(self, body: str) -> None:
            self.body = body
        
        def __iter__(self):
            return iter(self.body)
    
        def __str__(self) -> str:
            return self.body
        
        def getRawBody(self):
            return self.body
        
    def __init__(self, body: str) -> None:
        self.body = self.Body(body)

    def getRawBody(self):
        return self.body.getRawBody()
    
class HTTPResponse(Response):

    class Status:
        def __init__(self, status_line: str) -> None:
            
            statuses = status_line.split(" ")
            self.http_version = statuses[0]
            self.status_code = statuses[1]
            self.reason_phrase = statuses[2]
        
        def getHTTPVersion(self) -> str:
            return self.http_version

        def getStatusCode(self) -> int:
            return int(self.status_code)
        
        def getReasonPhrase(self) -> int:
            return self.reason_phrase
        
    class Header:
        def __init__(self, headers: dict) -> None:
            self.headers = headers

    def __init__(self, status_line: str, headers: dict, body: str) -> None:
        Response.__init__(self, body)
        self.status = self.Status(status_line)
        self.header = self.Header(headers)  


    def getBodyWithoutTags(self):
        in_angle = False
        result = ""
        for c in self.body:
            if c == "<":
                in_angle = True
            elif c == ">":
                in_angle = False
            elif not in_angle:
                result += c
        return result

class FileResponse(Response):

    def __init__(self, body: str) -> None:
        Response.__init__(self, body)

    
    

