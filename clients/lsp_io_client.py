import subprocess
import os

from lsp.util import (send_message,
                      make_initialize_request,
                      make_shutdown_request,
                      make_exit_notification,
                      make_initialized_notification)
from lsp.parser import Parser
from lsp_server.lsp_io_server import get_top_dir
from lsp.log import file_logger


def get_client_log_path():
    return get_top_dir() / "client.log"


def launch_server():
    return subprocess.Popen(
        # Note: Requires Python on path
        args="python -m lua.lua_server",
        stdout=subprocess.PIPE,
        stdin=subprocess.PIPE)


def test_lsp_server(log):

    with launch_server() as lsp_server:
        def write(msg):
            lsp_server.stdin.write(msg)
            lsp_server.stdin.flush()

        def read():
            lsp_server.stdout.read()

        response_parser = Parser(log)

        log.info("Make initialize request..")
        send_message(write, make_initialize_request(
            msg_id=1,
            client_name="lsp_io_client",
            client_version="1.0",
            processId=os.getpid()))
        log.info("Read initialize response..")
        reply = response_parser.read_response(lsp_server.stdout)
        log.info(str(reply))

        send_message(write, make_initialized_notification())

        log.info("Make shutdown request..")
        send_message(write, make_shutdown_request(msg_id=2))
        log.info("Read shutdown response..")
        reply = response_parser.read_response(lsp_server.stdout)
        log.info(str(reply))

        log.info("Make exit request..")
        send_message(write, make_exit_notification())

        log.info("Waiting for server to exit..")
        try:
            exit_code = lsp_server.wait(timeout=1.0)
        except subprocess.TimeoutExpired:
            log.info("Server didn't shut down in time. Shutting down client.")
        else:
            log.info(f"lsp-server shut down with exit code {exit_code}")


def run():
    log_path = get_client_log_path()
    with file_logger(log_path, 2) as log:
        log.info("--------------------")
        test_lsp_server(log)


if __name__ == '__main__':
    run()
