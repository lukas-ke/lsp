from lua.cmdline import get_lua_server_options
from lsp_server import lsp_io_server
import lsp.log
from lua import build_lua_doc
from lua.builtins import add_built_ins
from lua.lua_db import LuaDB
from lua.lua_types import GlobalEnv


def get_workspace_dir():
    # Hardcoded path for require etc.
    # TODO: Determine in some other way (e.g. proper workspace
    # support)
    top_dir = lsp_io_server.get_top_dir()
    workspace_dir = top_dir / "test/workspace"
    assert workspace_dir.exists()
    return workspace_dir.absolute()


def get_lua_path():
    ws = get_workspace_dir()
    lua_path = (str(ws) + "/?.lua").replace("\\", "/")
    return lua_path


def create_db(log, options):
    g_env = GlobalEnv()
    for module_path in options.load_modules:
        build_lua_doc.read_file(module_path, g_env)

    if options.enable_built_ins:
        add_built_ins(g_env)

    db = LuaDB(get_lua_path(), g_env, log, options)
    return db


def get_logger(options):
    if options.enable_log:
        log_path = lsp_io_server.get_server_log_path()
        return lsp.log.file_logger(log_path, 2)
    else:
        return lsp.log.null_logger()


def run():
    options = get_lua_server_options()
    with get_logger(options) as log:
        db = create_db(log, options)
        exit_code = lsp_io_server.run(db, log)
        exit(exit_code)
