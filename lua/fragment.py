"""Code for retrieving info about Lua fragments"""

from lua.lua_re import LUA_ID
import re


def get_by_name(name, g_env, l_env):
    o = l_env.get(name)
    if o is None:
        return g_env.get(name)


def get_by_path(path, g_env, l_env):
    first = get_by_name(path[0], g_env, l_env)
    if first is None:
        return None

    item = first
    for name in path[1:]:
        item = item.get(name)

    return item


def resolve_index(path, g_env, l_env):
    try:
        return get_by_path(path, g_env, l_env)
    except AttributeError:
        return None


def resolve_name(name, g_env, l_env):
    o = l_env.get(name)
    if o is not None:
        return o
    return g_env.get(name)


def resolve_node(path, g_env, l_env):
    if len(path) == 1:
        return resolve_name(path[0], g_env, l_env)
    else:
        return resolve_index(path, g_env, l_env)


def resolve(code, g_env, l_env):
    path = code.split(".")
    for item in path:
        if not re.match(LUA_ID, item):
            return None

    return resolve_node(path, g_env, l_env)
