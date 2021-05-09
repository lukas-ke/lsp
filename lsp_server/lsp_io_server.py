import sys
import json
from lsp.parser import Parser
from lsp_server.lsp_state import LSP_state
from lsp.util import send_message
from lsp.db import DB


def run(db, log):

    def write(message):
        sys.stdout.buffer.write(message)  # TODO: Why did I encode it? :)
        sys.stdout.flush()

    def log_f(msg):
        log.info(msg)

    log_f("--------------------")
    lsp_state = LSP_state(db, log)
    p = Parser(log_f)

    while True:
        log_f("Read message..")
        content = p.read()
        response = lsp_state.method(content)
        if response is not None:
            send_message(write, json.dumps(response))
        if lsp_state.exit:
            log_f("State has received exit notification. Exiting.")
            break

    if lsp_state.shutdown and lsp_state.exit:
        return 0
    else:
        return 1


if __name__ == '__main__':
    with open("server.log", 'w') as log_file:
        exit_code = run(DB())
        exit(exit_code)
