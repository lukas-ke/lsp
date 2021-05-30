from lua.build_lua_doc import read_file
from lua.lua_types import GlobalEnv


def test_missing_table_assign(print_env):
    g_env = GlobalEnv()
    read_file("test/testdata/invalid/missing_table_assign.lua", g_env)


def test_function_assign(print_env):
    g_env = GlobalEnv()
    read_file("test/testdata/invalid/function_assign.lua", g_env)


def run(print_env):
    test_missing_table_assign(print_env)
    test_function_assign(print_env)


if __name__ == '__main__':
    run(print_env=True)
