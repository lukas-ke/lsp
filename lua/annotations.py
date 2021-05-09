from . import lua_re
from typing import NamedTuple, Optional
import re

__all__ = [
    'parse_comment',
    'strip_annotations',
    'strip_prefix'  # Maybe
    'Param',
    'Return',
]


class Param(NamedTuple):
    label: str
    name: str
    type: str
    doc: Optional[str]


class Return(NamedTuple):
    label: str
    type: str


def parse_comment(comment):
    annotations = []
    stripped_comment = strip_prefix(comment)
    for m in ANNOTATION.finditer(stripped_comment):
        kind = m.lastgroup
        if kind == "PARAM":
            annotations.append(Param("param", m.group(3), m.group(4), m.group(5)))
        elif kind == "RETURN":
            annotations.append(Return("return", m.group(8)))
    return annotations


def strip_annotations(comment):
    stripped_prefix = strip_prefix(comment)
    stripped_annotations = ANNOTATION.sub("", stripped_prefix)
    return strip_trailing_space(stripped_annotations)


def strip_prefix(comment):
    stripped_prefix = lua_re.COMMENT_PREFIX.sub("", comment)

    stripped_lines = [ln.strip() for ln in stripped_prefix.split("\n")]
    return "\n".join([ln for ln in stripped_lines if len(ln) != 0])


def strip_trailing_space(comment):
    stripped_lines = [ln.strip() for ln in comment.split("\n")]
    return "\n".join([ln for ln in stripped_lines if len(ln) != 0])


class an:
    """Components for annotation regexps"""

    # Separator between annotation parts
    sep = lua_re.LUA_SPACE

    # The name the annotation introduces
    name = lua_re.LUA_ID

    # An actual dot symbol (i.e. not "any symbol")
    dot = r"\."

    # A qualified lua name, like a.b.c
    qual_name = f"{name}(?:{dot}{name})*"

    # The Lua type an annotation specifies
    lua_type = qual_name

    # The end of an annotation (non-capturing).
    #
    # Annotations end at the end of the string or at the start of the
    # next annotation
    end = r"(?:\Z|(?=[@]))"

    # Annotation docs match everything non-greedily (so it must be
    # halted with end), preferably use an.opt_doc
    doc = r".*?"

    # Optional document string. The annotation will match even if this
    # entry, which should be at the end, does not exist.
    #
    # Note: Includes the preceding separator, since it is only
    # required if there are docs, so this section should be appended
    # snugly to the previous component of the regexp, not preceded by
    # {sep}.
    opt_doc = f"(?:{sep}({doc}){end})?"


def param_re():
    return f"@(param){an.sep}({an.name}){an.sep}({an.lua_type}){an.opt_doc}"


def return_re():
    return f"@(return){an.sep}({an.lua_type})"

annotations = [
    ("PARAM", param_re()),
    ("RETURN", return_re())]


ANNOTATION = re.compile('|'.join(f'(?P<{p[0]}>{p[1]})' for p in annotations), flags=re.DOTALL|re.MULTILINE)
