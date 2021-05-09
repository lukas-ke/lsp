import json
from . lsp_defs import ResponseError


class Header:
    ContentLength = None
    ContentType = None


header_end = [b"\r", b"\n", b"\r", b"\n"]


def parse_header(b, log):
    fields = b.split(b"\r\n")
    header = {}
    for num, f in enumerate(fields):
        if len(f) == 0:
            assert num == len(fields) - 1
        else:
            key, value = f.split(b": ")
            header[key] = value
    return header


def make_header(message):
    items = [
        f"Content-Length: {len(message)}".encode("ascii"),
        b"Content-Type: application/vscode-jsonrpc; charset=utf-8",
        b"\r\n"]

    return b"\r\n".join(items)


def make_message():
    return {"json_rpc": "2.0"}


def make_request(msg_id, method, params):
    # TODO: In Python 3.9, use x | y merge syntax
    data = {"id": msg_id,
            "method": method}
    if params is not None:
        data["params"] = params

    msg = {**make_message(), **data}
    return json.dumps(msg)


def make_notification(method, params):
    data = {"method": method}
    if params is not None:
        data["params"] = params

    msg = {**make_message(), **data}
    return json.dumps(msg)


def make_response(request_id, result_or_error):
    data = {}
    data["id"] = request_id

    if result_or_error is None:
        data["result"] = None
    elif isinstance(result_or_error, ResponseError):
        data["error"] = result_or_error.toDict()
    elif isinstance(result_or_error, list):
        data["result"] = [item.toDict() for item in result_or_error]
    else:
        data["result"] = result_or_error.toDict()

    msg = {**make_message(), **data}
    return msg


def fake_client_capabilities():
    # TODO: Extend me
    return {}


def send_message(write, message):
    header = make_header(message)
    write(header + message.encode("utf-8"))


def make_initialize_request(msg_id, client_name, client_version, processId):
    assert type(processId) == int
    return make_request(
        msg_id,
        method="initialize",
        params={
            "processId": processId,

            "clientInfo": {
                "name": client_name,
                "version": client_version
            },
            "capabilities": fake_client_capabilities(),  # TODO
        })


def make_shutdown_request(msg_id):
    return make_request(msg_id, method="shutdown", params=None)


def make_exit_notification():
    return make_notification(method="exit", params=None)


def make_initialized_notification():
    return make_notification(method="initialized", params={})
