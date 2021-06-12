from lua.tokenize import tokenize, Token

TEXT = """local var = 5
function f()
end
"""


def test_tokenize(print_env):
    tokens = tokenize(TEXT)
    if print_env:
        for t in tokens:
            print(t)

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


def run(print_env):
    test_tokenize(print_env)


if __name__ == '__main__':
    run(True)
