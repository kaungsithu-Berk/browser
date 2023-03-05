from io import TextIOWrapper
from response.response import HTTPResponse, FileResponse

def createHTTPResponse(stream: TextIOWrapper) -> HTTPResponse:
    headers = {}
    status_line = stream.readline() # read the frist status line
    while True:
        line = stream.readline()
        if line == "\r\n": break
        header, value = line.split(":", 1)
        headers[header.lower()] = value.strip()
    
    assert "transfer-encoding" not in headers
    assert "content-encoding" not in headers

    body = stream.read()
    stream.close()
    return HTTPResponse(status_line, headers, body)

def createFileResponse(stream: TextIOWrapper) -> FileResponse:
    body = stream.read()
    stream.close()
    return FileResponse(body=body)