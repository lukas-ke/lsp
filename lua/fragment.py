"""Code for retrieving info about Lua fragments"""

from luaparser import ast
from luaparser import astnodes
import luaparser

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


def resolve_index_to_path(node):
    if not isinstance(node.idx, astnodes.Name):
        # rhs must be name (TODO: at least for now)
        return None

    name_rhs = node.idx.id

    if isinstance(node.value, astnodes.Index):
        path = resolve_index_to_path(node.value)
        path.append(name_rhs)
        return path

    elif isinstance(node.value, astnodes.Name):
        name_lhs = node.value.id
        return [name_lhs, name_rhs]
    else:
        assert False


def resolve_index(node, g_env, l_env):
    path = resolve_index_to_path(node)
    try:
        return get_by_path(path, g_env, l_env)
    except AttributeError:
        return None


def resolve_name(node, g_env, l_env):
    name = node.id
    o = l_env.get(name)
    if o is not None:
        return o
    return g_env.get(name)


RESOLVERS = {
    astnodes.Index: resolve_index,
    astnodes.Name: resolve_name,
}


def resolve_node(node, g_env, l_env):
    resolver = RESOLVERS.get(node.__class__)
    if resolver is None:
        return None
    return resolver(node, g_env, l_env)


def resolve(code, g_env, l_env):
    try:
        tree = ast.parse(code)
    except luaparser.builder.SyntaxException as e:
        return None

    if not isinstance(tree, astnodes.Chunk):
        return
    if not isinstance(tree.body, astnodes.Block):
        return

    entries = tree.body.body
    if len(entries) != 1:
        return None

    return resolve_node(entries[0], g_env, l_env)
