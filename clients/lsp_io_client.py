import subprocess
import os

from lsp.util import (send_message,
                      make_initialize_request,
                      make_shutdown_request,
                      make_exit_notification,
                      make_initialized_notification)
from lsp.parser import Parser


def launch_server():
    return subprocess.Popen(
        # Note: Requires Python on path
        args="python -m lua.lua_server",
        stdout=subprocess.PIPE,
        stdin=subprocess.PIPE)


def test_lsp_server(log_f):

    with launch_server() as lsp_server:
        def write(msg):
            lsp_server.stdin.write(msg)
            lsp_server.stdin.flush()

        def read():
            lsp_server.stdout.read()

        response_parser = Parser(log_f)

        log_f("Make initialize request..")
        send_message(write, make_initialize_request(
            msg_id=1,
            client_name="lsp_io_client",
            client_version="1.0",
            processId=os.getpid()))
        log_f("Read initialize response..")
        reply = response_parser.read_response(lsp_server.stdout)
        log_f(str(reply))

        send_message(write, make_initialized_notification())

        log_f("Make shutdown request..")
        send_message(write, make_shutdown_request(msg_id=2))
        log_f("Read shutdown response..")
        reply = response_parser.read_response(lsp_server.stdout)
        log_f(str(reply))

        log_f("Make exit request..")
        send_message(write, make_exit_notification())

        log_f("Waiting for server to exit..")
        try:
            exit_code = lsp_server.wait(timeout=1.0)
        except subprocess.TimeoutExpired:
            log_f("Server didn't shut down in time. Shutting down client.")
        else:
            log_f(f"lsp-server shut down with exit code {exit_code}")


def run():
    with open("client.log", "w") as client_log:
        def log_f(msg):
            client_log.write(f"{msg}\n")
            client_log.flush()

        log_f("--------------------")
        test_lsp_server(log_f)


if __name__ == '__main__':
    run()
