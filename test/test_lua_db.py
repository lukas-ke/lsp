import lua.lua_db as lua_db
from lua.lua_db import LuaDB
from lua.lua_types import GlobalEnv
from lsp.lsp_defs import CompletionItemKind, Position
import io
from pathlib import Path
from lua import lua_types
from lsp.lsp_defs import Position
from lsp_server.doc import Document
from lsp.log import stdout_logger
from lua import build_lua_doc

def get_workspace_dir():
    return Path(".").absolute()


def init_g_env():
    g_env = GlobalEnv()
    build_lua_doc.read_file("test/testdata/test_lua_db.lua", g_env)
    print(g_env.pretty_str(indent=0))
    return g_env


def create_db(log):
    lua_path = "test/testdata/lua_db_require/?.lua"
    return LuaDB(lua_path, init_g_env(), log)


def find_item(completions, label):
    for c in completions:
        if c.label == label:
            return c
    return None


def print_completions(print_env, label, entries):
    if not print_env:
        return
    if len(entries) != 0:
        print(f"{label}:")
        for item in entries:
            print(f"  {item}")
    else:
        print(f"{label}: <no completions>")


def has_item(items, name, expected_kind):
    item = find_item(items, name)
    if item is None:
        print(f"{name} missing")
        return False

    kind = item.kind
    if kind != expected_kind:
        print(f"{name} kind: {kind} != {expected_kind}")
        return False
    return True


def has_f(items):
    def f(name, expected_kind):
        return has_item(items, name, expected_kind)
    return f


def describe_prefix(doc, position):
    prefix = doc.lines[position.line][:position.character]
    return f"{prefix}|"


def check_completions(db, doc, pos, check_f, print_env):
    textDocument = None
    items = db.completions(doc, pos)
    print_completions(print_env, describe_prefix(doc, pos), items)
    check_f(items)


class Separator:
    def __init__(self, print_env):
        self.first = True
        self.print_env = print_env

    def __call__(self):
        if not self.print_env:
            return

        if self.first:
            self.first = False
        else:
            print()


def test_db_completions(print_env, log):
    db = create_db(log)

    assert db.g_env.has("my_table")
    assert db.g_env.has("a_function")
    print_blank_line = Separator(print_env)

    def check(prefix, check_f):
        print_blank_line()
        doc = Document("", prefix)
        pos = Position(line=0, character=len(prefix))
        check_completions(db, doc, pos, check_f, print_env)

    def checks_all(items):
        has = has_f(items)
        assert has("my_table", CompletionItemKind.Struct)
        assert has("my_value", CompletionItemKind.Value)
        assert has("global_value", CompletionItemKind.Value)
        assert has("a_function", CompletionItemKind.Function)
        #assert len(items) == 4
    check("", checks_all)

    def checks_my(items):
        assert len(items) == 2
        has = has_f(items)
        assert has("my_table", CompletionItemKind.Struct)
        assert has("my_value", CompletionItemKind.Value)
    check("my", checks_my)

    def checks_my_table_all(items):
        assert len(items) == 3
    check("my_table.", checks_my_table_all)

    def checks_my_table_x(items):
        assert len(items) == 2
        has = has_f(items)
        assert has("x", CompletionItemKind.Value)
        assert has("xavier", CompletionItemKind.Text)  # TODO: Should be value?
    check("my_table.x", checks_my_table_x)

    def checks_require(items):
        labels = [item.label for item in items]
        assert "first_file" in labels
        assert "second_file" in labels
    check('require("', checks_require)

    def checks_bad_completion(items):
        assert(len(items) == 0)
    check('a_function.something.', checks_bad_completion)


def test_db_misc(print_env, log):
    TEXT = """
t1={
    t2={
       f=function(x,y) end
    }
}"""

    g_env = lua_types.GlobalEnv()
    build_lua_doc.read_lua(TEXT, g_env, "<test_db_misc>")

    l_env = lua_types.LocalEnv(None, "imaginary")

    def echo_line_f(s):
        def get_line(n):
            assert(n == 0)
            return s
        return get_line

    f = lua_db.stupid_resolve_function_behind(
        log,
        echo_line_f("t1.t2.f("),
        Position(0, 8),
        g_env,
        l_env)
    assert isinstance(f, lua_types.Function)
    assert len(f.args) == 2


def run(print_env):
    with stdout_logger(log_level=2) as log:
        test_db_completions(print_env, log)
        test_db_misc(print_env, log)


if __name__ == '__main__':
    run(print_env=True)
