import sys

from pathlib import Path
from lua.lua_types import GlobalEnv
from lua.scope import find_scopes
from lua.tokenize import tokenize

if __name__ == '__main__':
    if len(sys.argv) != 2:
        sys.exit("Error: No file name given")

    lua_file_path = Path(sys.argv[1])
    with open(lua_file_path, 'r') as f:
        text = f.read()
        tokens = tokenize(text)
        g_env = GlobalEnv()
        scopes = find_scopes(tokens, g_env, lua_file_path)

        for r, sc in scopes:
            sc.pretty_print()

        g_env.pretty_print()
