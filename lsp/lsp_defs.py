"""Python-implementations of some of the LSP protocol interfaces and
such as defined in:
https://microsoft.github.io/language-server-protocol/specifications/specification-current/

Used for parsing JSON-rpc requests and responding to them.

"""
from urllib.parse import urlparse, unquote
from urllib.request import url2pathname
from pathlib import Path
import os

def assert_type_or_None(v, t):
    assert v is None or isinstance(v, t)
    return v


def make_dict(**kwargs):
    d = {}
    for k in kwargs:
        v = kwargs[k]
        if v is not None:
            d[k] = v
    return d


def make_dicts(items):
    if items is None:
        return None
    return [item.toDict() for item in items]


class CompletionItemKind:
    Text = 1
    Method = 2
    Function = 3
    Constructor = 4
    Field = 5
    Variable = 6
    Class = 7
    Interface = 8
    Module = 9
    Property = 10
    Unit = 11
    Value = 12
    Enum = 13
    Keyword = 14
    Snippet = 15
    Color = 16
    File = 17
    Reference = 18
    Folder = 19
    EnumMember = 20
    Constant = 21
    Struct = 22
    Event = 23
    Operator = 24
    TypeParameter = 25


def path_to_uri(path):
    if isinstance(path, str):
        if path.startswith("file:///"):
            return path
        else:
            path = Path(path)

    s = str(path.absolute())
    s.replace(":", "%3A")  # TODO hack alert
    s.replace("\\", "/")
    return "file:///" + s


def uri_to_path(uri):
    parsed = urlparse(uri)
    host = "{0}{0}{mnt}{0}".format(os.path.sep, mnt=parsed.netloc)
    return Path(os.path.normpath(
        os.path.join(host, url2pathname(parsed.path))))


class Location:
    """"Represents a location inside a resource, such as a line inside a
    text file.

    """
    def __init__(self, uri, range):
        self.uri = uri
        self.range = range

    def toDict(self):
        return {
            "uri": self.uri,
            "range": self.range.toDict()}


# Defines how the host (editor) should sync document changes to the language
# server.
class TextDocumentSyncKind:

    # Documents should not be synced at all.
    None_ = 0

    # Documents are synced by always sending the full content
    # of the document.
    Full = 1

    # Documents are synced by sending the full content on open.
    # After that only incremental updates to the document are
    # send[sic].
    Incremental = 2


class Position:
    def __init__(self, line, character):
        self.line = line
        self.character = character

    @staticmethod
    def fromDict(d):
        line = d["line"]
        character = d["character"]
        return Position(line, character)

    def toDict(self):
        return {"line": self.line, "character": self.character}


class Range:
    def __init__(self, start, end):
        self.start = start
        self.end = end

    @staticmethod
    def fromDict(d):
        start = Position.fromDict(d["start"])
        end = Position.fromDict(d["end"])
        return Range(start, end)

    def toDict(self):
        return {
            "start": self.start.toDict(),
            "end": self.end.toDict()}

    def num_lines(self):
        return self.end.line - self.start.line + 1


class TextDocumentContentChangeEvent:
    def __init__(self, range, text):
        self.range = range
        self.text = text

    @staticmethod
    def fromDict(d):
        text = d["text"]
        range_dict = d.get("range")
        if range_dict is None:
            return TextDocumentContentChangeEvent(range=None, text=text)
        else:
            range = Range.fromDict(range_dict)
            return TextDocumentContentChangeEvent(range, text)


class TextDocumentIdentifier:
    def __init__(self, uri):
        self.uri = uri

    @staticmethod
    def fromDict(d):
        uri = d["uri"]
        return TextDocumentIdentifier(uri)


class DocumentLinkParams:
    def __init__(self, textDocument: TextDocumentIdentifier):
        self.textDocument = textDocument


class DocumentLink:
    def __init__(self, range: Range, target: str):
        self.range = range
        self.target = target

    def toDict(self):
        return {
            "range": self.range.toDict(),
            "target": self.target}


class TextDocumentPositionParams:
    def __init__(self, textDocument, position):
        self.textDocument = textDocument
        self.position = position

    @staticmethod
    def fromDict(d):
        textDocument = TextDocumentIdentifier.fromDict(d["textDocument"])
        position = Position.fromDict(d["position"])
        return TextDocumentPositionParams(textDocument, position)


# TODO: also WorkDoneProgressParams and PartialResultParams
DefinitionParams = TextDocumentPositionParams

# TODO: Also WorkDoneProgressParams
HoverParams = TextDocumentPositionParams


class CompletionParams:
    def __init__(self, textDocument, position):
        self.textDocument = textDocument
        self.position = position

    @staticmethod
    def fromDict(d):
        textDocument = TextDocumentIdentifier.fromDict(d["textDocument"])
        position = Position.fromDict(d["position"])
        return CompletionParams(textDocument, position)


class DidCloseTextDocumentParams:
    def __init__(self, textDocument):
        self.textDocument = textDocument

    def fromDict(d):
        textDocument = TextDocumentIdentifier.fromDict(d["textDocument"])
        return DidCloseTextDocumentParams(textDocument)


class InitializeResult:
    def __init__(self, capabilities, serverInfo):
        assert isinstance(capabilities, dict)  # TODO: Hack for now
        assert isinstance(serverInfo, dict)  # TODO: Hack for now
        self.capabilities = capabilities
        self.serverInfo = serverInfo

    def toDict(self):
        return {
            "capabilities": self.capabilities,
            "serverInfo": self.serverInfo
        }


class SignatureHelpParams:
    def __init__(self, textDocument, position):
        self.textDocument = textDocument
        self.position = position

    def fromDict(d):
        textDocument = TextDocumentIdentifier.fromDict(d["textDocument"])
        position = Position.fromDict(d["position"])
        return SignatureHelpParams(textDocument, position)


class ParameterInformation:
    def __init__(self, label, documentation):
        self.label = assert_type_or_None(label, str)
        self.documentation = assert_type_or_None(documentation, str)  # TODO

    def toDict(self):
        return make_dict(
            label=self.label,
            documentation=self.documentation)


class SignatureInformation:
    """One signature for something callable."""

    def __init__(self, label, documentation, parameters, activeParameter):
        self.label = assert_type_or_None(label, str)

        # TODO: documentation can be some markup-interface
        self.documentation = assert_type_or_None(documentation, str)

        # List of ParameterInformation
        self.parameters = assert_type_or_None(parameters, list)
        self.activeParameter = assert_type_or_None(activeParameter, int)

    def toDict(self):
        # TODO: Maybe just store it like this immediately?
        return make_dict(
            label=self.label,
            documentation=self.documentation,
            parameters=make_dicts(self.parameters),
            activeParameter=self.activeParameter)


class SignatureHelp:
    """Signatures for something callable.

    This is the type for a response to a textDocument/signatureHelp
    request.

    Per the spec:
    There can be multiple signatures, but only one signature and
    parameter can be active.

    Presumably the currently matching signature and the parameter that
    should be entered at the current position for that signature.

    So for these signatures:

        someFunction(x: int, y: string, z: boolean)
        someFunction(x: string, y: string)

    This input:
    > someFunction(2, "he|"

    would be activeSignature: 0, activeParameter: 1

    while:
    > someFunction("he)
    would be activeSignature: 1, activeParameter: 0

    """

    def __init__(self, activeSignature, activeParameter, signatures):
        self.activeSignature = assert_type_or_None(activeSignature, int)
        self.activeParameter = assert_type_or_None(activeParameter, int)
        self.signatures = assert_type_or_None(signatures, list)

    def toDict(self):
        return make_dict(
            activeSignature=self.activeSignature,
            activeParameter=self.activeParameter,
            signatures=make_dicts(self.signatures))


class Hover:
    def __init__(self, contents, range=None):
        self.contents = contents
        self.range = range

    def toDict(self):
        d = {"contents": self.contents}
        if self.range is not None:
            d["range"] = self.range.toDict()
        return d


class ResponseError:
    def __init__(self, code, message):
        self.code = code
        self.message = message

    def toDict(self):
        return make_dict(code=self.code, message=self.message)


class CompletionItem:
    def __init__(self, label: str, kind: CompletionItemKind=None):
        self.label = label
        self.kind = kind

    def toDict(self):
        return make_dict(label=self.label, kind=self.kind)
