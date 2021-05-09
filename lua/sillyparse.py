DEBUG = False

def dbg(msg):
    if DEBUG:
        print(msg)


class State:
    def __init__(self, line, character):
        self.line = line
        self.ch = character
        self.scopeStack = []
        self.candidate = None
        self.candidate_line = None

    def push(self, sym):
        self.scopeStack.append(sym)

    def pop(self):
        self.scopeStack.pop()

    def top(self):
        if len(self.scopeStack) == 0:
            return None
        else:
            return self.scopeStack[-1]


CLOSERS = ")]}"
OPENERS = "([{"

WHITESPACE = " \t\n"
STRING_DELIMITERS = "\"'"
# TODO: Must have a non-digit first in the name
NAME_SYMBOLS = "123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz_"
INITIAL_NAME_SYMBOL = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz_"
INDEXING_SYMBOLS = ".:"

def opener_for(ch):
    if ch == ")":
        return "("
    elif ch == "]":
        return "["
    elif ch == "}":
        return "{"

def closer_for(ch):
    if ch == "(":
        return ")"
    elif ch == "[":
        return "]"
    elif ch == "{":
        return "}"

def find_string_intervals(line):
    intervals = []
    open_char = None
    open_index = None
    escaped = False

    for num in range(len(line)):
        ch = line[num]
        if ch == '\\':
            escaped = not escaped
            continue

        if escaped:
            escaped = False
            continue

        if open_char is None and ch in STRING_DELIMITERS:
            open_char = ch
            open_index = num

        elif ch == open_char:
            open_char = None
            intervals.append(range(open_index, num))
    if open_char is not None:
        intervals.append(range(open_index, num))

    return intervals


def within(ch, intervals):
    for r in intervals:
        if ch in r:
            return True
    return False


def find_indexing_at(log, get_line_f, line_num, char_num):
    """Return indexing, (start_line, start_char), (end_line, end_char)
    for the indexing expression surrounding (line_num, char_num),
    e.g.
    > "some.lua.qualified.name", (3, 7), (3, 23)
    or None if not at indexing tokens.

    - TODO: What should I call that? Qualified name? Indexing? Discern
    eh["abc"] vs eh.abc, or just consider that syntactic sugar? One
    can be resolved by expressions and might get a bit complicated.

    """
    line = get_line_f(line_num)
    log.info(f"Hover for {line}")
    start = None
    for i in range(char_num, -1, -1):
        if line[i] in NAME_SYMBOLS or line[i] in INDEXING_SYMBOLS:
            start = i
        else:
            break

    if start is None:
        return None

    end = len(line)
    for i in range(char_num, len(line)):
        if line[i] not in NAME_SYMBOLS and line[i] not in INDEXING_SYMBOLS:
            end = i
            break

    candidate = line[start:end]
    if candidate[0] not in INITIAL_NAME_SYMBOL:
        return None
    return candidate, (line_num, start), (line_num, end)


def find_indexing_before(get_line_f, line_num, char_num):
    first_line = True
    in_word = False
    word_end = None

    for ln in range(line_num, -1, -1):
        line = get_line_f(ln)
        if first_line:
            start_char = char_num
        else:
            start_char = len(line)
        first_line = False

        for n in range(start_char, -1, -1):
            dbg(f"Line: {ln}, Char: {n}:")
            if n >= len(line):
                continue
            ch = line[n]
            if ch in WHITESPACE:
                if in_word:
                    dbg(f"in word at {n}, returning {n + 1}, {word_end}")
                    return ln, (n + 1, word_end)
                else:
                    continue
            elif ch in NAME_SYMBOLS or ch in INDEXING_SYMBOLS:
                if not in_word:
                    dbg(f"enter word on {ch} at {n}")
                    word_end = n + 1
                    in_word = True
                    continue
            else:
                if not in_word:
                    return None
                else:
                    return ln, (n + 1, word_end)
        if in_word:
            return ln, (0, word_end)
    else:
        return None


def find_arglist_start(get_line_f, line_num, char_num):
    """Find the start of the innermost Lua argument list that contains
    line_num, char_num.

    Does not include the parenthesis, since those are optional in some cases in Lua, e.g. for
    func "1" or
    func [2] or
    func {}

    e.g. for > "func(x,|y), finds the x-index

    And for f1(1, f2(bah|)) find the index of the b in bah

    Considers only the opening-end of the argument list, i.e. it can be
    incomplete and unclosed.

    TODO: Decide corner cases like
    --B--       --A--
    ....., func(
               ^- Should that position count for A or B list?
    """
    dbg("--find_arglist_start--")

    st = State(line_num, char_num)

    first_line = True
    for ln in range(line_num, -1, -1):

        line = get_line_f(ln)
        string_intervals = find_string_intervals(line)

        dbg(f"Get line: {ln}: {line}")
        if line is None:
            return None, None
        if first_line:
            if char_num > len(line):
                return None, None

        if not first_line:
            char_num = len(line)
        first_line = False

        for n in range(char_num - 1, -1, -1):
            ch = line[n]

            if within(n, string_intervals):
                dbg(f"Ignoring {ch} at {n}")
                continue


            if ch in CLOSERS:
                if ch == ")" and st.candidate is not None:
                    dbg(f"Stacked parenthesis )[snip]( at {n}, use candidate {st.candidate}")
                    return st.candidate_line, st.candidate,

                dbg(f"push: {ch} at {n}")
                st.push(ch)
            elif ch in OPENERS:
                dbg(f"match: {ch} to {st.top()} at {n}")
                top = st.top()
                if top is None:
                    if ch == "(":
                        dbg(f"Open ( at {n} -> candidate at {n + 1}")
                        assert st.candidate is None
                        st.candidate = n + 1
                        st.candidate_line = ln
                    else:
                        # Else what: Mismatched braces or we're in a string?
                        return None, None  # TODO
                else:
                    dbg("top not None at {n}")
                    if top == closer_for(ch):
                        dbg(f"Popped {top} at {n}")
                        st.pop()
            else:
                if ch in WHITESPACE or st.candidate is None:
                    continue
                elif st.candidate is not None:
                    if ch in NAME_SYMBOLS:
                        dbg(f"Name at {n}, return previous candidate at {st.candidate}")
                        return st.candidate_line, st.candidate

                    if ch == ",":
                        dbg(f"Candidate at {st.candidate} reset by {ch}")
                        st.candidate = None
                        st.candidate_line = None
                        continue
                dbg(f"inconsequential [{ch}] at {n}")

    return st.candidate_line, st.candidate
