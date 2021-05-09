import lsp_server.doc as doc
from lsp.lsp_defs import Position

text = """local util = require("util")
local Small = require("small")
local result = util.addNumbers(5, 5)

a_function(x, y)"""


def test_Document(print_env):
    d = doc.Document(uri="", text=text)

    def word_at(ln, ch):
        return d.word_at(Position(ln, ch))

    def line_at(ln, ch):
        return d.line_at(Position(ln, ch))

    assert len(d.lines) == 6  # Note: doc inserts an extra line, (maybe wrong)
    assert line_at(0, 0) == 'local util = require("util")'
    assert line_at(0, 1) == 'local util = require("util")'
    assert line_at(1, 0) == 'local Small = require("small")'

    assert word_at(0, 0) == 'local'
    assert word_at(0, 4) == 'local'
    assert word_at(0, 5) == ''
    assert word_at(0, 6) == 'util'
    assert word_at(4, 10) == ''
    assert word_at(4, 11) == 'x'


def test_doc_simple(print_env):
    assert doc.word_start("abc(123", 2) == 0
    assert doc.word_end("abc(123", 2) == 2
    assert doc.word_at("abc(123", 2) == "abc"


def run(print_env):
    test_doc_simple(print_env)
    test_Document(print_env)


if __name__ == '__main__':
    run(False)
