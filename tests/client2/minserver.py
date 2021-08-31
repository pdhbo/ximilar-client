# pylint: disable=missing-module-docstring
import re
import socket
import threading

_transfer_encoding_re = re.compile(r"transfer-encoding: .*chunked", re.IGNORECASE)
_content_length_re = re.compile(r"content-length: (\d+)", re.IGNORECASE)
_chunk_re = re.compile(r"^(\d+)\r\n")


class MinHTTPServer:
    """
    Trivial server, accepting a single connection, storing the
    request verbatim, and replying with the provided string.
    It implements the minimum possible subset of HTTP to be able
    to react to the typical HTTP client.

    Typical usage would be:
        import requests

        def _reply_something(client):
            client.sendall(b"HTTP/1.1 200 OK\r\n\r\n")
            client.sendall(b"Something\r\n\r\n")

        with MinHTTPServer("127.0.0.1", 5000) as server:
            server.reply = _reply_something
            result = requests.get(server.url)
            print(result.text)
            print(server.request)
    """

    def __init__(self, address, port):
        self.address = address
        self.port = port
        self.server = None
        self.server_thread = None
        self.request = ""
        self.request_body = ""
        self.reply = self._default_reply

    def url(self):
        """URL to the server root"""
        return f"http://{self.address}:{self.port}/"

    def __enter__(self):
        self.server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.server.bind((self.address, self.port))
        self.server.listen(1)
        self.server_thread = threading.Thread(target=self._runner, args=())
        self.server_thread.start()
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.server_thread.join()
        self.server.close()
        return False

    def _runner(self):
        client, _ = self.server.accept()
        try:
            while True:
                data = client.recv(1024)
                if data:
                    self.request = self.request + data.decode("utf-8")
                    if "\r\n\r\n" in self.request:
                        self._read_body(client)
                        break
                else:
                    break
            self.reply(client)
        finally:
            client.close()

    def _read_body(self, client):
        header_end = self.request.find("\r\n\r\n") + 4
        self.request_body = self.request[header_end:]
        self.request = self.request[:header_end]
        transfer_encoding = _transfer_encoding_re.search(self.request)
        content_length = _content_length_re.search(self.request)
        if transfer_encoding is not None:
            while "\r\n0\r\n\r\n" not in self.request_body:
                data = client.recv(1024)
                if data:
                    self.request_body = self.request_body + data.decode("utf-8")
                else:
                    break
            self.request_body = self._decode_chunks(self.request_body)
        elif content_length is not None:
            length = int(content_length.group(1)) - len(self.request_body)
            while length > 0:
                data = client.recv(1024)
                if data:
                    self.request_body = self.request_body + data.decode("utf-8")
                    length = length - len(data)
                else:
                    break

    @staticmethod
    def _decode_chunks(chunked_body):
        decoded = ""
        match = _chunk_re.match(chunked_body)
        while match is not None:
            length = int(match.group(1))
            chunked_body = chunked_body[len(match.group(0)) :]
            if length > 0:
                decoded = decoded + chunked_body[:length]
                chunked_body = chunked_body[length + 2 :]
            match = _chunk_re.match(chunked_body)
        return decoded

    @staticmethod
    def _default_reply(client):
        client.sendall(b"HTTP/1.1 200 OK\r\n\r\n")
        client.sendall(b"Hello\r\n\r\n")
