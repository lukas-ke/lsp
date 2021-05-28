from lsp import lsp_defs
from pathlib import Path


def test_uri_to_path(print_env):
    uri = "file:///c%3A/some_path/some_file.lua"
    assert lsp_defs.uri_to_path(uri) == Path(r"c:\some_path\some_file.lua")


def run(print_env):
    test_uri_to_path(print_env)


if __name__ == '__main__':
    run(print_env=True)
