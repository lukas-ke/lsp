from lua.tokenize import tokenize, Token, TokenError

TEXT_OK = """local var = 5
function f()
end
"""

TEXT_ERRORS = """var = 42
!!!"""


def _tokenize(text, print_env):
    tokens, errors = tokenize(text)
    if print_env:
        print("Tokens:")
        for t in tokens:
            print(f" {t}")
        print("Errors:")
        for e in errors:
            print(f' TokenError("{e.value}", {e.line}, {e.column})')
    return tokens, errors


def error_eq(e, value, line, column):
    return all((
        e.value == value,
        e.line == line,
        e.column == column))

def test_tokenize_ok(print_env):
    tokens, errors = _tokenize(TEXT_OK, print_env)
    assert len(errors) == 0
    assert tokens[0] == Token("KEYWORD", "local", 0, 0)
    assert tokens[1] == Token("ID", "var", 0, 6)
    assert tokens[2] == Token("ASSIGN", "=", 0, 10)
    assert tokens[3] == Token("INTEGER", "5", 0, 12)
    assert tokens[4] == Token("KEYWORD", "function", 1, 0)
    assert tokens[5] == Token("ID", "f", 1, 9)
    assert tokens[6] == Token("SYMBOL", "(", 1, 10)
    assert tokens[7] == Token("SYMBOL", ")", 1, 11)
    assert tokens[8] == Token("KEYWORD", "end", 2, 0)
    assert len(tokens) == 9
    assert len(errors) == 0

def test_tokenize_errors(print_env):
    tokens, errors = _tokenize(TEXT_ERRORS, print_env)
    assert tokens[0] == Token("ID", "var", 0, 0)
    assert tokens[1] == Token("ASSIGN", "=", 0, 4)
    assert tokens[2] == Token("INTEGER", "42", 0, 6)
    assert len(tokens) == 3

    assert error_eq(errors[0], "!", 1, 6)
    assert len(errors) == 1

def run(print_env):
    test_tokenize_ok(print_env)
    test_tokenize_errors(print_env)

if __name__ == '__main__':
    run(True)
