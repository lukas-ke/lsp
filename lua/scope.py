from . tokenize import token_str
from . lua_types import (
    Uninitialized,
    Number,
    Comment,
    LuaItem,
    Function,
    String,
    Any,
    Table,
    Unknown,
    Arg,
    GlobalEnv,
    Boolean
)
from . import lua_types as lt
from . error import (
    LuaError,
    TODOError
)


class Name(LuaItem):  # TODO: Needed?
    def __init__(self, t):
        self.t = t

    def __str__(self):
        return self.t.value


class State:
    def __init__(self, tokens, g_env, file_path):
        self.scopeStack = []
        self.scopeStack.append((0, lt.LocalEnv(None, scopeName="outer")))
        self.g_env = g_env
        self.file_path = file_path
        self.scopes = []  # (range, scope)
        self.n = 0  # Token num
        self.tokens = tokens
        self.file_returns = []

    def done(self):
        return self.n == len(self.tokens)

    def peek(self, category, value):
        t = self.tokens[self.n]
        return t.category == category and t.value == value

    def at(self):
        if self.n < len(self.tokens):
            t = self.tokens[self.n]
            return (t.line, t.column)
        elif len(self.tokens) == 0:
            return (0, 0)
        else:
            t = self.tokens[-1]
            return (t.line, t.column)

    def peek_category(self, category):
        t = self.tokens[self.n]
        return t.category == category

    def take(self):
        t = self.tokens[self.n]
        self.n += 1
        return t

    def prev(self):
        if self.n > 0:
            return self.tokens[self.n - 1]
        return None

    def get(self):
        return self.tokens[self.n]

    def inner_scope(self):
        assert len(self.scopeStack) != 0
        return self.scopeStack[-1]

    def push_scope(self, start, name):
        _, top = self.inner_scope()
        new = top.push_new(scopeName=name)
        self.scopeStack.append((start, new))

    def global_assign(self, name, value):
        self.g_env[name] = value

    def local_assign(self, name, value):
        _, l_env = self.inner_scope()
        l_env.local_assign(name, value)

    def pop_scope(self, end):
        assert len(self.scopeStack) != 0
        start, top = self.scopeStack.pop()
        # Include terminating line
        range_end = end + 1
        self.scopes.append((range(start, range_end), top))

    def get_object(self, name):
        _, l_env = self.inner_scope()
        o = l_env.get(name)
        if o is None:
            o = self.g_env.get(name)
        return o

    def add_file_returns(self, returns):
        """Add file-scope returns (i.e. returns available when loading the
        file with "require"

        """
        self.file_returns.append(returns)


def resolve_field(st, comment=None):
    if not peek_assign(st):
        raise LuaError("Invalid field?", *st.at())
    st.take()
    return resolve_rhs(st, comment)


def resolve_table(st):
    opening_brace = st.take()
    assert opening_brace.value == "{", (
        "Resolve table called without opening brace")

    # TODO: Handle list tables too

    table = Table(st.file_path)

    comment = None
    if peek_comment(st):
        comment = resolve_comment(st)

    if st.done():
        raise LuaError(
            f"EOF in table starting at {opening_brace.line}", *st.at())

    if peek_name(st):
        name_token = st.take()
        first = resolve_field(st, comment)
        table[name_token.value] = first
    else:
        # Empty table
        if eat_rbrace(st):
            return table
        else:
            # TODO: Unexpected entry in table.
            # could be e.g. a number for lists
            raise TODOError("Table issue", *st.at())

    comment = None

    def resolve_next():
        if eat_comment(st):
            # Discard comment after field (before comma or end)
            return True

        if eat_rbrace(st):
            # End of table
            return False

        if eat_comma(st):
            comment = None
            if peek_comment(st):
                comment = resolve_comment(st)
            if eat_rbrace(st):
                # End of table, trailing comma (which is OK)
                return False

            if peek_name(st):
                name_token = st.take()
                value = resolve_field(st, comment)
                # TODO: Comment for lhs or for rhs?
                table[name_token.value] = value
                return True
            else:
                if st.done():
                    raise LuaError("Unexpected EOF", *st.at())
                else:
                    raise LuaError(
                        f"Unexpected {token_str(st.get())}", *st.at())

        elif eat_rbrace(st):
            return False
        else:
            if st.done():
                raise LuaError("End of file in table", *st.at())
            else:
                raise LuaError(f"Unexpected {token_str(st.get())}", *st.at())

    while resolve_next():
        pass
    return table


def resolve_rhs(st, comment=None):
    """Resolve one item on the rhs side"""
    if st.done():
        return None
    elif peek_lbrace(st):
        return resolve_table(st)
    elif st.peek_category("INTEGER"):
        t = st.take()
        return Number(
            value=int(t.value),
            file_path=st.file_path,
            line_num=t.line,
            char_num=t.column)
    elif peek_name(st):
        name = st.take()
        if peek_lparen(st):
            return resolve_call(st, Name(name))
        elif eat_dot(st):
            index_list = resolve_index(st, Name(name))
            if peek_lparen(st):
                return resolve_call(st, index_list)
            return index_list
        else:
            return name
    elif peek_str(st):
        t = st.take()
        return String(value=t.value[1:-1], file_path=st.file_path)
    elif peek_bool(st):
        t = st.take()
        return Boolean(
            value=t.value,
            doc=None,
            line_num=t.line,
            char_num=t.column)
    elif peek_function(st):
        return resolve_anonymous_function(st, comment)
    else:
        raise LuaError(f"Unexpected {token_str(st.get())} {st.at()}", *st.at())


def resolve_rhs_list(st):
    if st.done():
        return

    items = []
    first = resolve_rhs(st)
    if first is None:
        raise LuaError(
            f"None resolved on rhs around {token_str(st.prev())}", *st.at())

    items.append(first)

    def resolve_next():
        if not eat_comma(st):
            return False
        item = resolve_rhs(st)
        if item is None:
            raise LuaError("Error: Trailing comma?", *st.at())
        else:
            items.append(item)
            return True

    while resolve_next():
        pass
    return items


def resolve_name(st):
    if st.done():
        return None

    if st.peek_category("ID"):
        return Name(st.take())
    else:
        raise LuaError(f"Expected name, got: {token_str(st.get())}", *st.at())


def resolve_index(st, lhs):
    assert isinstance(lhs, Name)
    if st.done():
        return []

    path = []
    path.append(lhs.t.value)

    if peek_name(st):
        rhs = st.take()
        if eat_dot(st):
            rest = resolve_index(st, Name(rhs))
            path.extend(rest)
        else:
            path.append(rhs.value)
    return path


def _eat(st, category, value=None):
    if st.done():
        return False
    if _peek(st, category, value):
        st.take()
        return True
    return False


def _peek(st, category, value=None):
    if st.done():
        return False
    if value is None:
        return st.peek_category(category)
    return st.peek(category, value)


def peek_assign(st):
    return _peek(st, category="ASSIGN")


def peek_bool(st):
    if st.done():
        return False
    t = st.get()
    if t.category == "KEYWORD" and t.value in ["true", "false"]:
        return True
    return False


def peek_comment(st):
    return _peek(st, category="COMMENT")


def peek_keyword(st, keyword):
    return _peek(st, category="KEYWORD", value=keyword)


def peek_function(st):
    return peek_keyword(st, "function")


def peek_end(st):
    result = peek_keyword(st, "end")
    return result


def peek_name(st):
    return _peek(st, category="ID")


def peek_comma(st):
    return _peek(st, category="SYMBOL", value=",")


def peek_str(st):
    return _peek(st, category="STR")


def peek_lbrace(st):
    return _peek(st, category="SYMBOL", value="{")


def peek_rbrace(st):
    return _peek(st, category="SYMBOL", value="}")


def peek_lparen(st):
    return _peek(st, category="SYMBOL", value="(")


def peek_rparen(st):
    return _peek(st, category="SYMBOL", value=")")


def eat_comment(st):
    ate = _eat(st, category="COMMENT")
    while _eat(st, category="COMMENT"):
        pass
    return ate


def eat_end(st):
    return _eat(st, "KEYWORD", "end")


def eat_comma(st):
    return _eat(st, "SYMBOL", ",")


def eat_lparen(st):
    return _eat(st, "SYMBOL", "(")


def eat_lbrace(st):
    return _eat(st, "SYMBOL", "{")


def eat_rbrace(st):
    return _eat(st, "SYMBOL", "}")


def eat_rparen(st):
    return _eat(st, "SYMBOL", ")")


def eat_dot(st):
    return _eat(st, "SYMBOL", ".")


def eat_local(st):
    return _eat(st, "KEYWORD", "local")


def eat_function(st):
    return _eat(st, "KEYWORD", "function")


def eat_return(st):
    return _eat(st, "KEYWORD", "return")


def eat_assign(st):
    return _eat(st, "ASSIGN", "=")


def resolve_name_list(st):
    names = []

    if st.done():
        # TODO: Is this an error?
        return names

    # TODO: Names can be followed by operators.

    first = resolve_name(st)
    if first is None:
        raise LuaError("No name in list", *st.at())
        return names
    else:
        names.append(first)

    def resolve_next():
        if not eat_comma(st):
            return False
        name = resolve_name(st)
        if name is None:
            # .. presumably not valid here
            # (e.g. unlike in tables)
            raise LuaError("Trailing comma", *st.at())
        names.append(name)
        return True

    # Append the rest
    while resolve_next():
        pass

    return names


def get_object(st, obj):
    # TODO: Also indexes
    if isinstance(obj, Name):
        return st.get_object(obj.t.value)
    elif issubclass(obj.__class__, LuaItem):
        # Literal
        return obj
    elif isinstance(obj, list):
        # Assume index list
        if len(obj) == 0:
            return None  # TODO: Happens e.g. for "trailing-period-assign.lua"
        t = st.get_object(obj[0])
        if t is None:
            raise LuaError(f"Unknown name: {obj[0]}", *st.at())  # TODO: Don't terminate on this  # noqa: E501
        for num, key in enumerate(obj[1:]):
            try:
                t = t.get(key)
            except AttributeError:
                # Non-table lookup
                # TODO: Don't raise (=fail) on this, just resolve to
                # e.g. Uninitialized/Unknown, and add the error to the
                # list in st
                index_str = ".".join(obj[0:num + 1])
                # TODO Include object type at {index_str} (e.g.
                # function or whatever)
                raise LuaError(f"{index_str} not indexable", *st.at())
            if t is None:
                index_str = ".".join(obj[0:num + 1])
                raise LuaError(
                    f"{index_str} has no item with key {key}", *st.at())
            if t is None:
                return Unknown(name=".".join(obj), file_path=st.file_path)
        return t
    else:
        return None  # TODO: What should be done here?


def describe_name_or_index(name_or_index):
    assert name_or_index is not None
    if isinstance(name_or_index, Name):
        name = name_or_index
        return name.t.value
    elif isinstance(name_or_index, list):
        index = name_or_index
        return ".".join(index)
    else:
        assert False, f"Wrong type {name_or_index.__class__} passed to name_or_index"  # noqa: E501


def resolve_arg_list(st):
    if not eat_lparen(st):
        raise LuaError("Missing argument list", *st.at())

    args = []

    def add_arg(name):
        args.append(Arg(
            name=name.value,
            lua_type=None,
            doc=None,
            line_num=name.line,
            char_num=name.column))

    if peek_name(st):
        add_arg(st.take())

    while not st.done() and not peek_rparen(st):
        if peek_comma(st):
            comma = st.take()
            if not peek_name(st):
                # Real lua fails on this when the function is _called_
                raise LuaError(f"Trailing comma in arg-list at {comma.line}:{comma.column}", *st.at())  # noqa: E501
            add_arg(st.take())
        else:
            # TODO Check what else can go here
            raise LuaError(f"Expected ), found {st.get()}", *st.at())

    return args


def resolve_body(st, func):
    while not st.done() and not peek_end(st):
        resolve_token(st, outer_scope=False, func=func)


def resolve_function(st, comment=None):
    if not peek_name(st):
        return None

    name_token = st.take()

    names = None
    if eat_dot(st):
        names = resolve_index(st, Name(name_token))
        name = names[-1]
    else:
        name = name_token.value

    args = resolve_arg_list(st)
    if st.done():
        raise LuaError("Unexpected EOF", *st.at())
    rp = st.take()
    st.push_scope(rp.line, name)  # TODO: Include column + add args to scope

    func = Function(
        name=name,
        args=args,
        doc=comment,
        file_path=st.file_path,
        line_num=name_token.line,
        char_num=name_token.column,
        names=names)
    resolve_body(st, func)

    if not peek_end(st):
        raise LuaError("Missing end", *st.at())
    kw_end = st.take()
    st.pop_scope(kw_end.line)
    return func


def resolve_anonymous_function(st, comment):
    assert peek_function(st), "resolve_anonymous_function called without function-token"  # noqa: E501
    fn = st.take()
    args = resolve_arg_list(st)
    rp = st.take()
    st.push_scope(rp.line, f"anonymous at {fn.line}:{fn.column}")  # TODO: Include args, column # noqa: E501
    func = Function(
        name=None,
        args=args,
        doc=comment,
        file_path=st.file_path,
        line_num=fn.line,
        char_num=fn.column)
    resolve_body(st, func)
    assert peek_end(st)
    kw_end = st.take()
    st.pop_scope(kw_end.line)
    return func


def resolve_local(st, comment=None):
    if st.done():
        raise LuaError("Trailing local", *st.at())  # TODO Figure out proper error  # noqa: E501

    if peek_function(st):
        st.take()
        func = resolve_function(st, comment)
        if func is None:
            raise LuaError("Function resolved to None?", *st.at())  # TODO: Figure out what to do here # noqa: E501
        st.local_assign(func.name, func)
        return

    lhs_list = resolve_name_list(st)

    if st.done():
        # Presumably the above were declarations
        # TODO or maybe we have stacked names which would be an error
        return

    if not eat_assign(st):
        if len(lhs_list) == 0:
            prev = st.prev()
            raise LuaError(
                f"<name> expected near {prev.line, prev.column}", *st.at())
        else:
            for item in lhs_list:
                assert isinstance(item, Name)  # TODO: Use lua_types.Name
                name = item.t.value
                st.local_assign(
                    item.t.value,
                    Uninitialized(name, st.file_path))
    else:
        # Assignment
        rhs_list = resolve_rhs_list(st)
        if rhs_list is None:
            raise LuaError("Missing rhs for assignment", *st.at())

        for num, lhs in enumerate(lhs_list):
            if num < len(rhs_list):
                rhs = rhs_list[num]
                # TODO If it isn't a call, then I should resolve the
                # return value
                obj = get_object(st, rhs)
                st.local_assign(lhs.t.value, obj)


def resolve_global_assign(st, lhs_list):
    if st.done():
        raise LuaError("Trailing =", *st.at())

    rhs_list = resolve_rhs_list(st)
    for num, lhs in enumerate(lhs_list):
        if num < len(rhs_list):
            rhs = rhs_list[num]
            obj = get_object(st, rhs)
            st.global_assign(lhs.t.value, obj)


def resolve_call_parameters(st):
    while not st.done() and not peek_rparen(st):
        st.take()  # TODO: tossing parameters

    if st.done():
        raise LuaError("<eof> in arglist", *st.at())


def resolve_call(st, func_name_or_index):
    opening_paren = st.take()

    # TODO: Lua allows calls on a single table or string
    assert opening_paren.value == "(", "resolve_call called without opening paren"  # noqa: E501

    resolve_call_parameters(st)
    assert eat_rparen(st)  # TODO: LuaError

    func = get_object(st, func_name_or_index)
    if not isinstance(func, Function):
        where = describe_name_or_index(func_name_or_index)
        return Any(f"Call result for non-function {where}")

    if len(func.returns) > 0:
        if func.returns[0] in ["integer", "float", "number"]:
            # TODO: Convert already at comment parsing?
            return Number(
                value=None,
                file_path=st.file_path,
                line_num=opening_paren.line)

        elif isinstance(func.returns[0], LuaItem):
            return func.returns[0]
    # TODO: Add suport for multiple results
    return Any(f"Call result for {func.signature_str()}")  # TODO


def resolve_comment(st):
    lines = []

    def add(token):
        lines.append(token.value)

    while peek_comment(st):
        token = st.take()
        lines.append(token.value)
        # TODO: How separate commnent groups (broken by blank space)
        # and recognize after-line-comments?
    raw_comment = "\n".join(lines)
    return Comment(raw_comment)


def indexed_assign(st, index_list, value):
    assert issubclass(value.__class__, LuaItem)
    but_last = index_list[:-1]
    target = get_object(st, but_last)
    name = index_list[-1]
    target[name] = value


def resolve_indexed_assign(st, index):
    # TODO: Fuse with global_assign, pass an lhs that can contain
    # indexes Differentiate between Name and Index. Maybe call it a
    # reference or path or smth unless there's some obvious downside
    # and I should do a recursive index structure.

    rhs_list = resolve_rhs_list(st)

    if rhs_list is None or len(rhs_list) == 0:
        raise LuaError(
            f"Missing rhs for assignment around {st.prev()}", *st.at())

    if len(rhs_list) != 1:
        raise TODOError(
            f"Multi-value indexed assignment around {st.prev()}", *st.at)

    rhs = rhs_list[0]
    target = get_object(st, index[:-1])

    if not isinstance(target, Table):
        # Only tables supports assignment
        return

    name = index[-1]
    value = get_object(st, rhs)
    target[name] = value


def resolve_token(st, outer_scope=True, func=None):
    """Handle tokens in a "body".

    Consumes one or more tokens from st and updates its
    environments/scopes.

    """
    comment = None
    if peek_comment(st):
        comment = resolve_comment(st)

    if st.done():
        # TODO: Maybe process the final comment (if any), in case it has
        # annotations
        return

    if eat_local(st):
        resolve_local(st, comment)
    elif st.peek_category("ID"):
        names = resolve_name_list(st)
        assert len(names) != 0
        if len(names) > 1:
            # TODO: Could be indexes in a name list too :(
            assert eat_assign(st)
            resolve_global_assign(st, names)
        else:
            if peek_assign(st):
                st.take()
                resolve_global_assign(st, names)
                return
            elif peek_lparen(st) or peek_lbrace(st) or peek_str(st):
                resolve_call(st, names[0])
                return
            elif eat_dot(st):
                index_list = resolve_index(st, names[0])
                if peek_assign(st):
                    st.take()
                    resolve_indexed_assign(st, index_list)
                    return
                elif peek_lparen(st):
                    resolve_call(st, index_list)
                    return
                else:
                    pass  # TODO

            if st.done():
                raise LuaError("Unexpected EOF", *st.at())
            else:
                raise TODOError(f"Unexpected token {st.get()}", *st.at())

        # TODO: Maybe could be global assign, what do I know?
        raise LuaError(
            f"Unexpected non-local name {token_str(st.get())}", *st.at())

    elif eat_function(st):
        f = resolve_function(st, comment)
        if f is None:
            raise LuaError("Could not resolve function", *st.at())  # TODO
        if f.names is not None:
            indexed_assign(st, f.names, f)
        else:
            st.global_assign(f.name, f)
        return None
    elif eat_return(st):
        if peek_end(st):
            return None
        else:
            returns = resolve_rhs_list(st)
            if func is not None:
                func.add_returns(returns)
            elif outer_scope:
                st.add_file_returns(returns)
            else:
                # Returns while not in function, LuaError or scope.py-error?
                assert False, f"return outside function at {st.at()}"

    elif peek_end(st):
        if outer_scope:
            raise LuaError(f"Unmatched end {token_str(st.get())}", *st.at())  # TODO Proper error # noqa: E501
        return
    else:
        t2 = st.take()
        assert t2 is not None  # Can probably not happen
        line_num, char_num = st.at()
        raise(LuaError(f"Unhandled token: {token_str(t2)}", *st.at()))


def find_scopes_plus_errors(tokens, g_env, file_path):
    assert isinstance(g_env, GlobalEnv)
    st = State(tokens, g_env, file_path)

    errors = []
    try:
        while st.n < len(tokens):
            resolve_token(st)
    except LuaError as e:
        errors.append(e)
    except TODOError as e:
        errors.append(e)

    # Pop file scope
    prev = st.prev()
    last_token_line = 0 if prev is None else prev.line
    epicycle = 1
    st.pop_scope(last_token_line + epicycle)

    return st.scopes, errors


def find_scopes(*args):
    scopes, errors = find_scopes_plus_errors(*args)
    return scopes
