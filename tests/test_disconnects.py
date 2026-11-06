"""Client disconnects must not turn into server errors or repeated actions."""
import io
import json
from types import SimpleNamespace
import unittest

from studyforge.gui import make_handler


class DisconnectTests(unittest.TestCase):
    def test_header_and_body_disconnects_do_not_retry_or_break_requests(self):
        for method in ("GET", "POST"):
            for error in (BrokenPipeError, ConnectionResetError):
                for failed_write in (1, 2):
                    with self.subTest(method=method, error=error, write=failed_write):
                        actions, statuses = [], []

                        class Controller:
                            def handle(self, command_name, **params):
                                actions.append(command_name)
                                return {"saved": True}

                        class Socket:
                            def __init__(self, request, fail=None):
                                self.request, self.fail = request, fail
                                self.writes = 0
                                self.output = bytearray()

                            def makefile(self, *args, **kwargs):
                                return io.BytesIO(self.request)

                            def sendall(self, data):
                                self.writes += 1
                                if self.writes == self.fail:
                                    raise error("browser closed its connection")
                                self.output.extend(data)

                        class Handler(make_handler(Controller(), "test-token")):
                            def send_response(self, code, message=None):
                                statuses.append(code)
                                super().send_response(code, message)

                        server = SimpleNamespace(server_port=8766)
                        if method == "GET":
                            request = b"GET / HTTP/1.0\r\nHost: 127.0.0.1:8766\r\n\r\n"
                        else:
                            body = json.dumps({"action": "save", "params": {}}).encode()
                            request = (b"POST /api/action HTTP/1.0\r\nHost: 127.0.0.1:8766\r\n"
                                       b"Content-Type: application/json\r\nX-StudyForge-Token: test-token\r\n"
                                       + f"Content-Length: {len(body)}\r\n\r\n".encode() + body)
                        handler = Handler(Socket(request, failed_write), ("127.0.0.1", 12345), server)
                        self.assertTrue(handler.close_connection)
                        self.assertEqual(statuses, [200], "A disconnect must not trigger a second error response")
                        self.assertEqual(actions, ["save"] if method == "POST" else [])

                        # The same boundary still serves subsequent connections.
                        healthy = Socket(b"GET / HTTP/1.0\r\nHost: 127.0.0.1:8766\r\n\r\n")
                        Handler(healthy, ("127.0.0.1", 12346), server)
                        self.assertIn(b"200 OK", healthy.output)
                        self.assertIn(b"StudyForge", healthy.output)


if __name__ == "__main__":
    unittest.main()
