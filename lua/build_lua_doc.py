"""Build a lua_doc.LuaDoc by parsing Lua source code.

The goal is for this to allow "partial success", i.e. the code doesn't
have to be well formed, so that completion can be provided at least up
to a certain point.

"""

from . tokenize import tokenize
from . scope import find_scopes_plus_errors
from . lua_doc import LuaDoc


def read_lua(text, g_env, file_path=None) -> LuaDoc:
    tokens = tokenize(text)
    scopes, errors = find_scopes_plus_errors(tokens, g_env, file_path)
    return LuaDoc(scopes=scopes, errors=errors)


def read_file(file_path, g_env) -> LuaDoc:
    with open(file_path, "r") as f:
        text = f.read()
        return read_lua(text, g_env, file_path)
