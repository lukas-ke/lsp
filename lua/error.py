"""Type definitions for errors that can be detected during
Lua-parsing

"""
from lsp.lsp_defs import (
    Diagnostic,
    Position,
    Range,
)


class LuaBaseError(Exception):
    """Base for errors and warnings detected when parsing Lua code.

    Subclasses are:

    - Raised as an exception for "unrecoverable" errors, which ends the
      parsing at that point.

    - Added to a list for errors that don't have to end the parsing.

    """
    # TODO: Allow a range, not just a position
    def __init__(self, message, line_num, char_num):
        super().__init__(message)
        self.line_num = line_num
        self.char_num = char_num

    def get_message(self):
        return f"{self.get_prefix()} {self.args[0]}"

    def get_prefix(self):
        return ""


class LuaError(LuaBaseError):
    """Raised for Lua syntax errors"""
    pass


class TODOError(LuaBaseError):
    """Raised for incomplete features in the parser"""

    def get_prefix(self):
        return "TODO:"


def to_diagnostic(e: LuaBaseError):
    pos = Position(line=e.line_num, character=e.char_num)
    return Diagnostic(
        range=Range(start=pos, end=pos),
        message=e.get_message())
