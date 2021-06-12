import collections
import lua.lua_re as lua_re

# Based on the pretty neat example at
# https://docs.python.org/3/library/re.html#writing-a-tokenizer

Token = collections.namedtuple(
    'Token', [
        'category',
        'value',
        'line',
        'column'])


class TokenError(Exception):
    def __init__(self, value, line, column):
        super().__init__(self, f'Unexpected "{value}" at {line}:{column}')
        self.value = value
        self.line = line
        self.column = column


def read_next(text):
    line_num = 0
    line_start = 0
    for mo in lua_re.TOKEN.finditer(text):
        kind = mo.lastgroup
        value = mo.group(kind)
        if kind == 'NEWLINE':
            line_start = mo.end()
            line_num += 1
        elif kind == 'SKIP':
            pass
        elif kind == 'MISMATCH':
            # TODO: Store current state
            raise TokenError(value, line_num, column)
        else:
            if kind == 'ID' and value in lua_re.keywords:
                kind = "KEYWORD"
            column = mo.start() - line_start
            yield Token(kind, value, line_num, column)


def tokenize(text):
    tokens = []
    errors = []
    try:
        for t in read_next(text):
            tokens.append(t)
    except TokenError as e:
        # Note: List will have zero or one error, since the iteration
        # stops, which is probably for the best (the mismatch could be
        # passed on to allow for more context, but that would make the
        # later stages more complicated).
        errors.append(e)

    return tokens, errors


def token_str(t):
    if t.category in lua_re.keywords:
        return f"{t.line}:{t.column} Keyword {t.category}"
    else:
        return f"{t.line}:{t.column} {t.category}: |{t.value}|"


def print_token(t):
    print(token_str(t))
