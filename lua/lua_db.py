from . import fragment
from lsp import db
from . import lua_types
from lua.sillyparse import find_arglist_start, find_indexing_before, find_indexing_at
from lua.lua_doc import LuaDoc, EMPTY_ENV
from lua.build_lua_doc import read_lua
from lsp.lsp_defs import (
    CompletionItem,
    CompletionItemKind,
    DefinitionParams,
    Hover,
    HoverParams,
    Location,
    ParameterInformation,
    Position,
    Range,
    SignatureHelp,
    SignatureInformation,
    uri_to_path,
)
import lsp.lsp_defs as lsp_defs
from . import lua_re
from pathlib import Path
from typing import Mapping

LUA_TYPE_TO_LSP_KIND = {
    lua_types.Number: CompletionItemKind.Value,
    lua_types.Function: CompletionItemKind.Function,
    lua_types.Table: CompletionItemKind.Struct,  # TODO: Consider..
}


def stupid_resolve_function_behind(log, get_line_f, pos, g_env, l_env):
    al, ac = find_arglist_start(get_line_f, pos.line, pos.character)
    if al is None:
        log.info("Couldn't find arglist start")
        return None
    if ac < 2:
        # TODO: Should find a suitable chunk of code before,
        # can't search from start of line
        log.info("Too close to start for fragment_resolve")
        return None

    name_range = find_indexing_before(get_line_f, al, ac - 2)
    if name_range is None:
        log.info("Could not find_indexing_before")
        return None
    line_num, (start_char, end_char) = name_range

    expr = get_line_f(line_num)[start_char:end_char]
    if expr.count(":") > 1:
        log.info("TODO: Multiple : indexes")
        return None
    expr = expr.replace(":", ".")  # Repair invalid lua a.b:c
    log.info(f"{line_num}, ({start_char}, {end_char}) -> {expr}")

    return fragment.resolve(expr, g_env, l_env)


def stupid_commas_behind(doc, pos):
    commas = 0
    character = pos.character
    ln = doc.lines[pos.line]
    for ch in range(character - 1, -1, -1):
        if ln[ch] == ",":  # TODO: Utterly idiotic
            commas += 1
        elif ln[ch] == "(":
            break

    return commas


def lsp_kind(obj):
    return LUA_TYPE_TO_LSP_KIND.get(type(obj), CompletionItemKind.Text)


def make_file_completion(key):
    return CompletionItem(label=key)


def make_completion(key, obj):
    return CompletionItem(label=key, kind=lsp_kind(obj))


def as_index_list(prefix):
    return prefix.strip().split(".")


def complete_all(g_env):
    return [make_completion(key, g_env[key]) for key in g_env if key != "_G"]


def complete_single(prefix, g_env, l_env) -> [CompletionItem]:
    local_keys = [key for key in l_env.recursive_names() if key.startswith(prefix)]
    local_completions = [make_completion(key, l_env[key]) for key in local_keys]
    global_completions =  [make_completion(key, g_env[key])
                           for key in g_env
                           if key != "_G" and key.startswith(prefix) and key not in local_keys]
    return local_completions + global_completions


def complete_index_list(index_list, g_env, l_env, include_f) -> [CompletionItem]:
    o = l_env.get(index_list[0])
    if o is None:
        o = g_env.get(index_list[0])

    if o is None:
        return []

    for item in index_list[1:-1]:
        # TODO: Maybe should generalize with "indexable"
        if not isinstance(o, lua_types.Table):
            return []

        o = o.get(item)
        if o is None:
            return []

    if isinstance(o, lua_types.Table):
        prefix = index_list[-1]
        return [make_completion(key, o[key])
                for key in o
                if key.startswith(prefix)
                and include_f(o[key])]


def simple_paths_hack(lua_path):
    # Hack for simple require completion for paths like
    #   c:/some_folder/?.lua
    # TODO: I should also allow stuff like
    #   c:/some_folder/?/the_file.lua or
    #   c:/some_folder/?/?.lua
    simple_paths = [p for p in lua_path.split(";") if p.endswith("?.lua")]
    simple_paths = [p[:-5] for p in simple_paths]
    for p in simple_paths:
        assert "?" not in p
    return [Path(p) for p in simple_paths]


def complete_require(uri, prefix_full, lua_path):
    prefix = lua_re.match_require(prefix_full).group(2)
    current_file = uri_to_path(uri)

    def match_prefix(f):
        return f.is_file() and f.name.startswith(prefix)

    candidates = []
    for p in simple_paths_hack(lua_path):
        if p.exists() and p.is_dir():
            for f in p.iterdir():
                if match_prefix(f) and not f.samefile(current_file):
                    candidates.append(f.stem)

    return [make_file_completion(c) for c in candidates]


def stupid_type_definition(doc, position, g_env, l_env, log):
    """Does *stupid* type-definition finding.

    Finds the "word" at the position in doc, and looks in g_env, l_env
    for matching keys.

    If the match is a function, it opens the file the function was
    defined in. If there is line and character info available it will
    jump there.

    TODO: Save the file information for more objects, this could support
    any item associated with a name.

    TODO: Allow indexing e.g. finding the definition for a or b or c
    in "a.b.c"

    """

    w = doc.word_at(position)  # TODO: Simplistic
    log.info(f"typeDefinition for: {w}")

    o = l_env.get(w)
    if o is None:
        o = g_env.get(w)
    if o is None:
        return None

    file_path = o.file_path
    if file_path is None:
        return None
    line_start = o.line_num if o.line_num is not None else 0
    char_start = o.char_num if o.char_num is not None else 0

    return Location(
        uri=lsp_defs.path_to_uri(file_path),
        range=Range(
            start=Position(line=line_start, character=char_start),
            end=Position(line=line_start, character=char_start)))

def method_path_fragment(path):
    if len(path) == 0:
        return False
    last_item = path[-1]
    if len(last_item) == 0:
        return False
    return last_item[-1] == ":"


class LuaDB(db.DB):
    lua_docs: Mapping[str, LuaDoc]

    def __init__(self, lua_path, g_env, log):
        self.lua_path = lua_path
        self.g_env = g_env
        self.log = log.prefixed("[LuaDB] ")

        # URI to LuaDoc
        self.lua_docs = {}

    def set_lua_doc(uri: str, doc: LuaDoc):
        self.lua_docs[uri] = doc

    def get_local_env(self, doc, position):
        ld = self.lua_docs.get(doc.uri)
        if ld is None:
            self.log.info(f"{doc.uri} not in lua_docs")
            return EMPTY_ENV
        l_env = ld.scope_at(position)
        if l_env is EMPTY_ENV:
            self.log.info(f"Got EMPTY_ENV at {position.line}, {position.character}")
        else:
            self.log.info(f"Got {l_env.scopeName} at {position.line}, {position.character}")
        return l_env

    def completions(self, doc, position):
        prefix = doc.lines[position.line][:position.character]

        if lua_re.in_require(prefix):
            self.log.info(f"in require: {prefix}")
            return complete_require(doc.uri, prefix, self.lua_path)
        else:
            self.log.info(f"not in require: {prefix}")
        path = as_index_list(prefix)

        method = method_path_fragment(path)
        if method:
            self.log.info("Method")
            path[-1] = path[-1][:-1]
            path.append("")
        else:
            self.log.info("Not method: " + "|".join(path))

        l_env = self.get_local_env(doc, position)
        if len(path) == 1 and not method:
            return complete_single(path[0], self.g_env, l_env)
        else:
            if method:
                # Only complete to functions
                # TODO: Only complete to methods with matching type (or unspecified) type of
                #       first argument (self)?
                # (at least exclude 0-args? Maybe wrong due to Lua silliness)
                def include_f(o):
                    return isinstance(o, lua_types.Function)
            else:
                # Complete to any object
                def include_f(o):
                    return True
            return complete_index_list(path, self.g_env, l_env, include_f)

    def typeDefinition(self, doc, position):
        l_env = self.get_local_env(doc, position)
        return stupid_type_definition(doc, position, self.g_env, l_env, self.log)

    def definition(self, doc, definitionParams: DefinitionParams) -> Location:
        l_env = self.get_local_env(doc, definitionParams)
        return stupid_type_definition(doc, definitionParams, self.g_env, l_env, self.log)

    def signatureHelp(self, doc, position):
        self.log.info(f"signatureHelp: {doc.line_at(position)}")
        l_env = self.get_local_env(doc, position)

        func = stupid_resolve_function_behind(
            self.log,
            lambda n: doc.lines[n],
            position,
            self.g_env,
            l_env)

        if func is None:
            self.log.info("signatureHelp: Could not find function.")
            return None

        if not isinstance(func, lua_types.Function):
            self.log.info("Resolved item not callable")
            return None

        num_commas = stupid_commas_behind(doc, position)
        activeParameter = min(num_commas, 1)

        parameters = [ParameterInformation(
            label=arg.name,
            documentation=arg.doc) for arg in func.args]

        if func.name is None:
            func_name = "function"
        else:
            func_name = func.name

        signature = SignatureInformation(
            label=func.signature_str(),
            documentation=func.get_doc(),  # TODO
            parameters=parameters,
            activeParameter=activeParameter)

        self.log.info("returning SignatureHelp")
        signatureHelp = SignatureHelp(
            activeSignature=0,
            activeParameter=activeParameter,
            signatures=[signature])

        self.log.info(str(signatureHelp.toDict()))

        return signatureHelp


    def hover(self, doc, hoverParams):
        try:
            index_info = find_indexing_at(
                self.log,
                doc.line_n,
                hoverParams.position.line,
                hoverParams.position.character)
        except IndexError:  # TODO: Fix find_indexing_at instead
            index_info = None

        if index_info is None:
            return Hover("")

        contents, (start_line, start_char), (end_line, end_char) = index_info
        parts = contents.split(".")  # TODO: Handle final :

        def label_only():
            return Hover(contents, Range(
                Position(line=start_line, character=start_char),
                Position(line=end_line, character=end_char)))

        if len(parts) == 0:
            return label_only()
        l_env = self.get_local_env(doc, hoverParams.position)
        first = l_env.get(parts[0])
        if first is None:
            first = self.g_env.get(parts[0])
        if first is None:
            return label_only()

        obj = first
        for part in parts[1:]:
            obj = obj.get(part)
            if obj is None:
                return label_only

        return Hover(obj.pretty_str(indent=0), Range(
            Position(line=start_line, character=start_char),
            Position(line=end_line, character=end_char)))

    def didOpen(self, doc):
        text = "\n".join(doc.lines) # TODO: I just had it as text
        lua_doc = read_lua(text, self.g_env, doc.uri)
        self.log.info(f"read LuaDoc with {len(lua_doc.scopes)} scopes")
        self.log.info(lua_doc.pretty_str())
        self.lua_docs[doc.uri] = lua_doc

    def didChange(self, doc):
        text = "\n".join(doc.lines)
        lua_doc = read_lua(text, self.g_env, doc.uri)
        self.log.info(f"re-read LuaDoc with {len(lua_doc.scopes)} scopes")
        self.lua_docs[doc.uri] = lua_doc
