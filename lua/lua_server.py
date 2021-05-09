from lsp.log import file_logger
from lua import build_lua_doc
from lua.builtins import add_built_ins
from lua.lua_db import LuaDB
from lua.lua_types import GlobalEnv
from pathlib import Path
from lsp_server import lsp_io_server


def get_workspace_dir():
    # Hack: Allow starting with workspace/ as cwd or the root dir lsp/
    # to let lsp_io_client and luk-lsp in emacs both work (for now)
    workspace_dir = Path("test/workspace")
    if workspace_dir.exists():
        return workspace_dir.absolute()
    else:
        assert Path("../workspace").exists()
        return Path(".").absolute()


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
    with file_logger("server.log", 2) as log:
        db = create_db(log)
        exit_code = lsp_io_server.run(db, log)
        exit(exit_code)
