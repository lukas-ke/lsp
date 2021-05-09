# https://www.lua.org/manual/5.1/manual.html

import re


def match_require(prefix):
    return re.search(r'require(\(["|\'])(.*)', prefix)


def in_require(prefix):
    m = match_require(prefix)
    if m:
        return True
    return False


keywords = ["and",
            "break",
            "do",
            "else",
            "elseif",
            "end",
            "false",
            "for",
            "function",
            "if",
            "in",
            "local",
            "nil",
            "not",
            "or",
            "repeat",
            "return",
            "then",
            "true",
            "until",
            "while"]

symbols = [
    r"\+",
    r"-",
    r"\*",
    r"\/",
    r"\%",
    r"\^",
    r"\#",
    r"\=\=",
    r"\~\=",
    r"\<\=",
    r"\>\=",
    r"\<",
    r"\>",
    r"\=",
    r"\(",
    r"\)",
    "{",
    "}",
    r"\[",
    r"\]",
    r"\;",
    r"\:",
    r"\,",
    r"\.",
    r"\.\.",
    r"\.\.\."]

# Names
LUA_ID = r'[a-zA-Z_]\w*'

# Whitespace, but not endline
LUA_SPACE = r'[ \t]+'

token_specification = [
    ('COMMENT', r'--.*?$'),
    ('ID', LUA_ID),
    ('ASSIGN', r'=(?!=)'),
    ('COMPARE', r'=='),
    ('INTEGER', r'[0-9]+'),
    ('SYMBOL', '|'.join(symbols)),
    ('NEWLINE', r'\n'),
    ('SKIP', LUA_SPACE),
    ('STR', r'".*?"'),
    ('MISMATCH', r'.')]

TOKEN = re.compile('|'.join(f'(?P<{p[0]}>{p[1]})' for p in token_specification), flags=re.DOTALL|re.MULTILINE)

COMMENT_PREFIX = re.compile("^(--*)", flags=re.DOTALL|re.MULTILINE)


def print_token(t):
    if t.category in keywords:
        print(f"{t.line}:{t.column} Keyword {t.category}")
    else:
        print(f"{t.line}:{t.column} {t.category}: |{t.value}|")
