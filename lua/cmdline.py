import argparse


def get_lua_server_options():
    parser = argparse.ArgumentParser(
        description="Lua language server")

    disable_opts = [
        ("log", "Disable writing to server log file")]

    group = parser.add_argument_group("Disable commands")
    for name, description in disable_opts:
        group.add_argument(
            f"--disable-{name}",
            action='store_false',
            dest=f"enable_{name}",
            help=description)

    return parser.parse_args()
