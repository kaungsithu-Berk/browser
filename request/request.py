HTTP_METHODS = {"GET"}

class Request:
    def __init__(self, msg: str) -> None:
        self.msg = msg

    def __str__(self) -> str:
        return self.get_msg()
    
    def get_msg(self):
        return self.msg
    
    def get_encoded_msg(self):
        return self.msg.encode("utf8")
    
def createHTTPRequest(method="GET", path="/", headers={}) -> Request:
    assert method in HTTP_METHODS
    msg = "{} {} HTTP/1.1".format(method, path)

    for header, value in headers.items():
        msg += "\r\n" + "{}: {}".format(header, value)

    msg += "\r\n\r\n"

    return Request(msg)

