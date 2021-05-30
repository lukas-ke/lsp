# -*- coding: utf-8 -*-
from . import annotations


def _space_sep_non_empty(*args):
    filtered = [a for a in args if a is not None and len(a) > 0]
    return " ".join(filtered)


def _no_sep_non_empty(*args):
    filtered = [a for a in args if a is not None and len(a) > 0]
    return "".join(filtered)


class LuaItem:
    def __init__(self, file_path, line_num=None, char_num=None):
        self.file_path = file_path
        self.line_num = line_num
        self.char_num = char_num

    def pretty_str(self, indent):
        assert False, "Base LuaItem pretty_str"

    def pretty_print(self, indent=0):
        print(self.pretty_str(indent))


class Comment:
    def __init__(self, raw_comment):
        self.comment_text = annotations.strip_annotations(raw_comment)
        self.annotations = annotations.parse_comment(raw_comment)

    def get_annotations(self):
        return self.annotations

    def get_doc(self):
        return self.comment_text

    def get_arg_docs(self):
        arg_docs = []

        for a in self.annotations:
            if a.label == "param":
                if a.doc is not None:
                    arg_docs.append((a.name, a.doc))

        if len(arg_docs) == 0:
            return ""

        parameter_notes = "\n".join([f"  {name}: {docs}"
                                     for name, docs in arg_docs])
        return f"\n\n**Parameter notes**:\n{parameter_notes}"


class Uninitialized(LuaItem):
    def __init__(self, name, file_path):
        LuaItem.__init__(self, file_path)
        self.name = name

    def pretty_str(self, indent):
        return "<uninitialized>"


class Arg:
    """Function argument"""
    def __init__(self, name, lua_type=None, doc=None, line_num=None, char_num=None):  # noqa: E501
        self.name = name
        self.lua_type = lua_type
        self.doc = doc
        self.line_num = line_num
        self.char_num = char_num

    def signature_str(self):
        """What this argument should look like in a help parameter list"""
        if self.lua_type is None:
            return self.name
        else:
            return f"{self.name}: {self.lua_type}"


def _lua_str_to_python_bool(lua_str):
    if lua_str == "true":
        return True
    elif lua_str == "false":
        return False
    else:
        assert False, "FILE_NOT_FOUND"


def _python_bool_to_lua_str(python_bool):
    if python_bool:
        return "true"
    else:
        return "false"


class Boolean(LuaItem):
    def __init__(self, value, doc, line_num, char_num):
        if not isinstance(value, bool):
            self.value = _lua_str_to_python_bool(value)
        else:
            self.value = value
        self.doc = doc
        self.line_num = line_num
        self.char_num = char_num

    def pretty_str(self, indent):
        s = _python_bool_to_lua_str(self.value)
        return f"{s}: boolean"


def _assign_types_to_args(args, comment: Comment):
    assert comment is not None
    assert isinstance(comment, Comment)

    def find_arg(name):
        for arg in args:
            if arg.name == name:
                return arg
        return None

    for a in comment.get_annotations():
        if a[0] == "param":
            name = a[1]
            lua_type = a[2]
            arg = find_arg(name)
            if arg is not None:
                arg.lua_type = lua_type


def _returns_from_annotations(comment: Comment):
    assert comment is not None
    assert isinstance(comment, Comment)
    returns = []
    for a in comment.get_annotations():
        if a.label == "return":
            returns.append(a.type)
    return returns


class Function(LuaItem):
    def __init__(self, name=None, names=None, args=None, doc=None, file_path=None, line_num=None, char_num=None):  # noqa: E501
        LuaItem.__init__(self, file_path)
        self.name = name
        self.args = args
        self.doc = doc
        assert self.doc is None or isinstance(self.doc, Comment)
        self.line_num = line_num
        self.char_num = char_num

        # TODO: Hack, use some index/name type that forces figuring out which
        self.names = names

        if self.doc is not None:
            _assign_types_to_args(self.args, self.doc)

        if self.doc is not None:
            self.returns = _returns_from_annotations(self.doc)
        else:
            self.returns = []

    def pretty_str(self, indent):
        if self.name is not None:
            return f"<function {self.name}>"  # TODO
        else:
            return "<anonymous function>"

    def signature_str(self):
        return _no_sep_non_empty(
            self.name,
            _space_sep_non_empty(
                self.arg_list_str(),
                self.return_str()))

    def arg_list_str(self):
        """Returns the argument list within parenthesis and with types e.g.
        "(someArg: integer, otherArg: string)

        """
        args_str = ", ".join([arg.signature_str() for arg in self.args])
        return f"({args_str})"

    def arg_signature_str(self, arg_num):
        return self.args[arg_num].signature_str()

    def return_str(self):
        if len(self.returns) == 0:
            return ""
        else:
            # TODO: Use more explicit call than str,
            # require these to be LuaType:s
            return "→ " + ", ".join([str(r) for r in self.returns])
        return str(self.returns)  # TODO

    def add_returns(self, returns):
        if len(self.returns) != 0:
            # The function has been annotated, prefer those returns
            # TODO: Do something smarter, e.g. separate namespaces for
            #       annotations and deductions
            return
        else:
            self.returns.extend(returns)

    def get_doc(self):
        if self.doc is not None:
            return self.doc.get_doc() + self.doc.get_arg_docs()
        else:
            return ""


class Any(LuaItem):
    def __init__(self, name=None, file_path=None):
        LuaItem.__init__(self, file_path)
        self.name = name

    def pretty_str(self, indent):
        if self.name is not None:
            return f"any<{self.name}>"
        else:
            return "any"


class Unknown(LuaItem):
    """For names that can't be resolved in LocalEnv or GlobalEnv

    TODO: Not sure what to do with these. Maybe they could be
    "late-resolved", if the name has shown up in globals later... e.g.
    to deal with different files introducing globals and "arbitrary
    order of parsing"

    """

    def __init__(self, name, file_path):
        LuaItem.__init__(self, file_path)
        self.name = name

    def pretty_str(self, indent):
        return f"<{self.name}>: Unknown"

    def __str__(self):
        return f"Unknown<{self.name}>"


class Unimplemented(LuaItem):
    """For avoiding None in output for unimplemented cases
    """

    def __init__(self, what, file_path):
        LuaItem.__init__(self, file_path)
        self.what = what

    def pretty_str(self, indent):
        return f"[unimplemented {self.what}]"

    def __str__(self):
        return f"[unimplemented {self.what}]"


class Number(LuaItem):
    def __init__(self, value, file_path, line_num=None, char_num=None):
        LuaItem.__init__(self, file_path)
        assert not isinstance(value, str)
        self.value = value
        self.line_num = line_num
        self.char_num = char_num

    def __str__(self):
        return self.pretty_str(0)

    def pretty_str(self, indent):
        if self.value is None:
            return "number"
        else:
            return f"{self.value}: number"


class String(LuaItem):
    def __init__(self, value, file_path):
        LuaItem.__init__(self, file_path)
        self.value = value

    def pretty_str(self, indent):
        return f'"{self.value}":string'


class Table(LuaItem):
    def __init__(self, file_path):
        LuaItem.__init__(self, file_path)
        self.fields = {}

    def __setitem__(self, key, value):
        self.fields[key] = value

    def __getitem__(self, key):
        return self.fields[key]

    def __len__(self):
        return len(self.fields)

    def get(self, key):
        return self.fields.get(key)

    def pretty_str(self, indent):
        ind = " " * indent
        ind2 = " " * (indent + 1)
        return ("{"
                + "".join(
                    [f"\n{ind2}{key}={self.fields[key].pretty_str(indent + 1)}"
                     for key in self.fields])
                + f"\n{ind}}}")

    def pretty_print(self, indent=0):
        print(self.pretty_str(indent))

    def has(self, key):
        return key in self.fields

    def __str__(self):
        return "A Table"

    def __iter__(self):
        return self.fields.__iter__()


class GlobalEnv:
    def __init__(self):
        self.names = {}
        self.names["_G"] = self

    def __len__(self):
        return len(self.names)

    def __getitem__(self, key):
        return self.names[key]

    def __setitem__(self, key, value):
        assert issubclass(value.__class__, LuaItem) or value is None
        self.names[key] = value

    def __iter__(self):
        return self.names.__iter__()

    def get(self, key):
        return self.names.get(key)

    def has(self, key):
        return key in self.names.keys()

    def print_env(self):
        names = "\n".join([f" {n}" for n in self.names])
        print(f"Env for global scope:\n{names}")

    def pretty_str(self, indent, heading=True):
        ind = " " * indent
        ind2 = " " * (indent + 1)
        if heading:
            title = f'{ind}Global env {{'
        else:
            title = ""
        return (
            title
            + "".join([
                f"\n{ind2}{key}={self.names[key].pretty_str(indent + 1)}"
                for key in self.names if key != "_G"])
            + f"\n{ind}}}")

    def pretty_print(self, indent=0, heading=True):
        print(self.pretty_str(indent, heading))


def _pretty_str(v, indent):
    if v is None:
        return "<None>"
    else:
        return v.pretty_str(indent)


class RecursiveEnvIterator:
    """Iterator over the names in env and all its parent scopes."""
    def __init__(self, env):
        self.env = env
        self.it = iter(self.env.names)

    def __iter__(self):
        return self

    def __next__(self):
        while True:
            try:
                return next(self.it)
            except StopIteration:
                next_env = self.env.parent
                if next_env is None:
                    raise
                else:
                    self.it = iter(next_env.names)
                    self.env = next_env
        return StopIteration()


class LocalEnv:
    def __init__(self, parent, scopeName=None, depth=0):
        assert parent is None or depth > 0
        self.names = {}
        self.parent = parent
        self.depth = depth
        assert self.parent is None or isinstance(self.parent, LocalEnv)
        self.scopeName = scopeName

    def push_new(self, scopeName=None):
        if scopeName is None:
            scopeName = self.scopeName
        return LocalEnv(parent=self, scopeName=scopeName, depth=self.depth + 1)

    def __len__(self):
        return len(self.names)

    def __getitem__(self, key):
        # Search for key in wider scopes
        if key in self.names:
            return self.names[key]
        elif self.parent is not None:
            return self.parent[key]
        return None  # TODO: Throw? Implement get()

    def __iter__(self):
        return self.names.__iter__()

    def recursive_names(self):
        return RecursiveEnvIterator(self)

    def get(self, key):
        if key in self.names:
            return self.names[key]
        elif self.parent is not None:
            return self.parent.get(key)
        return None

    def local_assign(self, key, value):
        self.names[key] = value

    def find_scope_with(self, key):
        if key in self.names:
            return self
        elif self.parent is not None:
            return self.parent.find_scope_with(key)
        return None

    def print_env(self, heading=True):
        names = "\n".join([" " + n for n in self.names])
        if heading:
            print(f'Env for scope "{self.scopeName}":\n{names}')
        else:
            print(names)

    def pretty_str(self, indent, heading=True):
        ind = " " * indent
        ind2 = " " * (indent + 1)

        if heading:
            title = f'{ind}locals in "{self.scopeName}:{self.depth}" {{'
        else:
            title = ""

        def maybe_parent():
            if self.parent is not None:
                return f'\n{ind2}(+ scope "{self.parent.scopeName}")'
            return ""

        return (
            title
            + "".join(
                [f"\n{ind2}{key}={_pretty_str(self.names[key], indent + 1)}"
                 for key in self.names])
            + f"{maybe_parent()}"
            + f"\n{ind}}}")

    def pretty_print(self, indent=0, heading=True):
        print(self.pretty_str(indent, heading))

    def has(self, key, recursive):
        if key in self.names:
            return True
        elif recursive and self.parent is not None:
            return self.parent.has(self, key, True)
        return False


class nop_iter:
    def __next__(self):
        raise StopIteration

    def __iter__(self):
        return self


class EmptyEnv:
    def __len__(self):
        return 0

    def __getitem__(self, key):
        return None  # TODO: Throw?

    def __iter__(self):
        return nop_iter()

    def recursive_names(self):
        return nop_iter()

    def get(self, key):
        return None

    def find_scope_with(self, key):
        return None

    def print_env(self):
        print('EmptyEnv')

    def pretty_str(self, indent):
        return "EmptyEnv"

    def pretty_print(self, indent=0):
        print(self.pretty_str(0))

    def has(self, key, recursive):
        return False
