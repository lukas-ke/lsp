from lua import fragment
from lua.lua_types import (GlobalEnv, LocalEnv)
import lua.lua_types as lua_types
from lua.build_lua_doc import read_lua
from lsp.lsp_defs import Position

MODULE_TEXT = """a = {
  b = {
    c = {
      d = {
        e = 23,
        func = function(x, y) end,
      }
    }
  }
}

function globalFunction(a,b,c) end
"""


def table_keys(v, keys):
    if not isinstance(v, lua_types.Table):
        return False
    return sorted(keys) == sorted(k for k in v.fields.keys())


def run(print_env):
    g_env = GlobalEnv()
    file_path = "(str)"
    lua_doc = read_lua(MODULE_TEXT, g_env, file_path)
    l_env = lua_doc.scope_at(Position(line=0, character=0))

    def check_resolve_None(code):
        return fragment.resolve(code, g_env, l_env) is None

    def check_resolve_table(code, keys):
        """True if code resolves to a table with the given keys"""
        return table_keys(fragment.resolve(code, g_env, l_env), keys)

    def check_resolve_Number(code, value):
        number = fragment.resolve(code, g_env, l_env)
        if not isinstance(number, lua_types.Number):
            return False
        return number.value == value

    def check_resolve_Function(code):
        f = fragment.resolve(code, g_env, l_env)
        return isinstance(f, lua_types.Function)

    assert check_resolve_table("a", ["b"])
    assert check_resolve_None("b")
    assert check_resolve_table("a.b", ["c"])
    assert check_resolve_table("a.b.c", ["d"])
    assert check_resolve_table("a.b.c.d", ["e", "func"])
    assert check_resolve_Function("a.b.c.d.func")
    assert check_resolve_Function("globalFunction")
    # TODO: Allow resolving calls to types etc.


if __name__ == '__main__':
    print_env = True
    run(print_env)
