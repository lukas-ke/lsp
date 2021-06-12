import argparse
from pathlib import Path


def _get_parser():
    parser = argparse.ArgumentParser(
        description="Start a Lua language server.")

    disable_opts = [
        ("log", "Disable writing to server log file"),
        ("hover", "Disable hover information"),
        ("local-env", "Disable local environments, only do completion on names in globals parsed as a library on start-up with --load-module"),
        ("built-ins", "Disable hard-coded definitions for built-in Lua functions"),
    ]

    group = parser.add_argument_group(
        "Disable commands",
        description="Options that disable server features (in some cases LSP capabilities)")
    for arg_name, description in disable_opts:
        py_name = arg_name.replace("-", "_")
        group.add_argument(
            f"--disable-{arg_name}",
            action='store_false',
            dest=f"enable_{py_name}",
            help=description)

    parser.add_argument(f"--load-module",
                        action="append",
                        dest="load_modules",
                        metavar="<path>",
                        default=[],
                        help="Specify a module to load on start-up for initializing globals. Can be repeated.")
    return parser


def get_lua_server_options():
    options = _get_parser().parse_args()
    options.load_modules = [Path(m).resolve() for m in options.load_modules]
    return options


def get_default_lua_server_options():
    return _get_parser().parse_args(args=[])
