import sys
import json
from pathlib import Path

from lsp.db import DB
from lsp.log import file_logger
from lsp.parser import Parser
from lsp.util import send_message
from lsp_server.lsp_state import LSP_state

def get_top_dir():
    return Path(__file__).parent.parent.absolute()


def get_server_log_path():
    return get_top_dir() / "server.log"


def run(db, log):

    def write(message):
        sys.stdout.buffer.write(message)  # TODO: Why did I encode it? :)
        sys.stdout.flush()

    log.info("--------------------")
    lsp_state = LSP_state(db, log)
    p = Parser(log)

    while True:
        log.info("Read message..")
        content = p.read()
        response = lsp_state.method(content)
        if response is not None:
            send_message(write, json.dumps(response))
        if lsp_state.exit:
            log.info("State has received exit notification. Exiting.")
            break

    if lsp_state.shutdown and lsp_state.exit:
        return 0
    else:
        return 1


if __name__ == '__main__':
    log_path = get_server_log_path()
    with file_logger(log_path, 2) as log:
        exit_code = run(DB())
        exit(exit_code)
