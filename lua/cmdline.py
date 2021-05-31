import argparse


def _get_parser():
    parser = argparse.ArgumentParser(
        description="Lua language server")

    disable_opts = [
        ("log", "Disable writing to server log file"),
        ("hover", "Disable hover information")]

    group = parser.add_argument_group("Disable commands")
    for name, description in disable_opts:
        group.add_argument(
            f"--disable-{name}",
            action='store_false',
            dest=f"enable_{name}",
            help=description)

    return parser


def get_lua_server_options():
    return _get_parser().parse_args()


def get_default_lua_server_options():
    return _get_parser().parse_args(args=[])
