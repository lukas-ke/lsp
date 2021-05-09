import lua.build_lua_doc as build_lua_doc
import lua.lua_types as lt


def check_for_file(print_env, file_path, check):
    g_env = lt.GlobalEnv()
    print()
    print(file_path)
    print("-" * len(file_path))
    with open(file_path, "r") as f:
        text = f.read()
        doc = build_lua_doc.read_lua(text, g_env, file_path)
        check(doc.scopes, g_env)
        print_scopes(print_env, doc.scopes, g_env)


def get_if_Class(env, name, cls):
    o = env.get(name)
    if o is None:
        return None
    if not isinstance(o, cls):
        return None
    return o


def get_if_Table(env, name):
    return get_if_Class(env, name, lt.Table)


def is_GlobalEnv(env, name):
    o = get_if_Class(env, name, lt.GlobalEnv)
    return o is not None


def is_Boolean(env, name, value):
    o = get_if_Class(env, name, lt.Boolean)
    if o is None:
        return False
    return o.value == value


def is_Number(env, name, value):
    o = get_if_Class(env, name, lt.Number)
    if o is None:
        return
    return o.value == value


def is_String(env, name, value):
    o = get_if_Class(env, name, lt.String)
    if o is None:
        return
    return o.value == value


def is_Function(env, name):
    o = get_if_Class(env, name, lt.Function)
    return o is not None


def is_Any(env, name):
    o = get_if_Class(env, name, lt.Any)
    return o is not None


def is_Uninitialized(env, name):
    o = get_if_Class(env, name, lt.Uninitialized)
    return o is not None


def print_scopes(print_env, scopes, g_env):
    print()
    for r, scope in scopes:
        title = f'Scope "{scope.scopeName}" (span {r.start} -> {r.stop}) {{'
        print(title, end="")
        print(scope.pretty_str(indent=0, heading=False))

    print("Globals {", end="")
    print(g_env.pretty_str(0, heading=False))


def get_scope(name, scopes):
    for r, scope in scopes:
        if scope.scopeName == name:
            return r, scope
    return None


def test_empty(print_env):

    def check(scopes, g_env):
        assert len(scopes) == 1
        r, outer = get_scope("outer", scopes)
        assert len(outer) == 0

        assert len(g_env) == 1
        assert is_GlobalEnv(g_env, "_G")

    check_for_file(print_env, "test/testdata/empty.lua", check)


def test_simple(print_env):

    def check(scopes, g_env):
        assert len(scopes) == 1, "Expected only a local scope"

        r, l_env = scopes[0]
        assert(r.start == 0)
        # TODO: Detecting last line, e.g. whitespace and such
        # (We want completion on the last line too, file scope
        # should include all lines)
        assert(r.stop == 8)
        assert is_Number(l_env, "a", 120)
        assert is_Number(l_env, "b", 10)
        assert is_Number(l_env, "c", 20)
        assert is_Number(l_env, "d", 30)
        assert is_Uninitialized(l_env, "e")
        assert is_Uninitialized(l_env, "f")
        assert is_Number(l_env, "y", 3)
    check_for_file(print_env, "test/testdata/simple.lua", check)


def test_local_assign(print_env):

    def check(scopes, g_env):
        assert len(scopes) == 1, "Expected only a local scope"
        #  assert "xylophone" not in g_env.names # TODO Fails

    check_for_file(print_env, "test/testdata/local-assign.lua", check)


def test_scope(print_env):

    def check_outer(r, scope):
        assert(len(scope) == 1)
        assert is_Function(scope, "my_func")

    def check_my_func(r, scope):
        assert(len(scope) == 2)
        assert is_Number(scope, "x", 5)
        assert is_Function(scope, "f2")

    def check_f2(r, scope):
        assert(len(scope) == 1)
        assert is_Number(scope, "y", 2)

    def check_global(scope):
        assert(len(scope) == 4)
        assert is_Number(scope, "some_global", 100)
        assert is_Number(scope, "other_global", 5)
        assert is_String(scope, "global_string", "here's a string")
        assert is_GlobalEnv(scope, "_G")

    def check(scopes, g_env):
        check_outer(*get_scope("outer", scopes))
        check_my_func(*get_scope("my_func", scopes))
        check_global(g_env)

    check_for_file(print_env, "test/testdata/scope.lua", check)


def test_call(print_env):
    def check_f1_scope(ranged_scope):
        r, scope = ranged_scope
        assert(r.start == 0)
        assert(r.stop == 3)
        assert(len(scope) == 0)
        assert scope.parent.scopeName == "outer"

    def check_outer(ranged_scope):
        r, scope = ranged_scope
        assert(r.start == 0)
        assert(r.stop == 9)

        # TODO: Not sure if number value should be resolved
        assert is_Number(scope, "x", 5)

        assert is_Function(scope, "f1")

    def check(scopes, g_env):
        assert len(scopes) == 2
        check_f1_scope(get_scope("f1", scopes))
        check_outer(get_scope("outer", scopes))

    check_for_file(print_env, "test/testdata/call.lua", check)


def test_table(print_env):

    def check_global(g_env):
        assert len(g_env) == 2
        assert is_Number(g_env, "glorb", 1)
        assert is_GlobalEnv(g_env, "_G")

    def check_outer(r, scope):
        assert r.start == 0
        assert r.stop == 13
        a = get_if_Table(scope, "a")
        assert a is not None
        b = get_if_Table(a, "b")
        assert b is not None
        c = get_if_Table(b, "c")
        assert len(c) == 3
        assert is_Number(c, "x", 1)
        assert is_Number(c, "y", 2)
        assert is_String(c, "late_addition", "hello")

    def check(scopes, g_env):
        # TODO: Do tables introduce scopes? Probably not.
        # Can I reach an outer table in an inner table?
        assert len(scopes) == 1
        check_outer(*get_scope("outer", scopes))
        check_global(g_env)

    check_for_file(print_env, "test/testdata/table.lua", check)


def test_some_globals(print_env):

    def check(scopes, g_env):
        pass  # TODO

    check_for_file(print_env, "test/workspace/some_globals.lua", check)


def test_comment(print_env):

    def check(scopes, g_env):
        r, scope = get_scope("outer", scopes)
        f = scope["my_local_function"]
        assert f.doc.get_doc() == "This function is\nrather documented."

    check_for_file(print_env, "test/testdata/comments.lua", check)


def test_boolean(print_env):

    def check(scopes, g_env):
        r, outer = get_scope("outer", scopes)
        assert is_Boolean(g_env, "my_true_global_bool", True)
        assert is_Boolean(outer, "my_true_local_bool", True)
        assert is_Boolean(g_env, "my_false_global_bool", False)
        assert is_Boolean(outer, "my_false_local_bool", False)

    check_for_file(print_env, "test/testdata/boolean.lua", check)


def test_mega(print_env):

    def check(scopes, g_env):
        pass  # TODO

    check_for_file(print_env, "test/testdata/mega.lua", check)


def test_build_lua_doc(print_env):
    test_empty(print_env)
    test_simple(print_env)
    test_local_assign(print_env)
    test_scope(print_env)
    test_call(print_env)
    test_table(print_env)
    test_some_globals(print_env)
    test_comment(print_env)
    test_boolean(print_env)
    test_mega(print_env)


def run(print_env):
    test_build_lua_doc(print_env)
    test_scope(print_env)


if __name__ == '__main__':
    print_env = True
    run(print_env)
