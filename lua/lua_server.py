from lsp.log import file_logger
from lsp_server import lsp_io_server
from lua import build_lua_doc
from lua.builtins import add_built_ins
from lua.lua_db import LuaDB
from lua.lua_types import GlobalEnv
from pathlib import Path


def get_top_dir():
    return Path(__file__).parent.parent.absolute()


def get_workspace_dir():
    # Hardcoded path for require etc.
    # TODO: Determine in some other way (e.g. proper workspace
    # support)
    top_dir = get_top_dir()
    workspace_dir = top_dir / "test/workspace"
    assert workspace_dir.exists()
    return workspace_dir.absolute()


def create_db(log):
    g_env = GlobalEnv()
    ws = get_workspace_dir()
    module_path = ws / "some_globals.lua"
    build_lua_doc.read_file(module_path, g_env)
    lua_path = (str(ws) + "/?.lua").replace("\\", "/")
    add_built_ins(g_env)
    db = LuaDB(lua_path, g_env, log)
    return db


def run():
    log_path = get_top_dir() / "server.log"
    with file_logger(log_path, 2) as log:
        db = create_db(log)
        exit_code = lsp_io_server.run(db, log)
        exit(exit_code)
