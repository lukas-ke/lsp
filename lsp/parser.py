import sys
import json

from . util import parse_header, header_end


class Parser:
    """Parses LSP header and content."""
    def __init__(self, log):
        self.content = []
        self.log = log.prefixed("[Parser]")

    def _quit(self, msg):
        self.log.info(f"Quitting: {msg}")
        exit(1)

    def _read_header(self, stream):
        content = []
        while True:
            # Read the header character-by-character
            data = stream.read(1)
            if len(data) == 0:
                self._quit("Handle closed")

            content.append(data)
            if data == b"\n":
                if content[-4:] == header_end:
                    return parse_header(b"".join(content[:-2]), self.log)

    def _read_content(self, length):
        raw_content = sys.stdin.buffer.read(length)
        return json.loads(raw_content.decode("utf-8"))

    def read(self):
        header = self._read_header(sys.stdin.buffer)
        self.log.info(f"Header: {str(header)}")
        length = int(header[b"Content-Length"])
        self.log.info(f"Length: {length}")
        content = self._read_content(length)
        assert(type(content) == dict)
        self.log.info(str(content))
        return content

    def read_response(self, stream):
        header = self._read_header(stream)
        length = int(header[b"Content-Length"])
        raw_content = stream.read(length)
        return json.loads(raw_content.decode("utf-8"))
