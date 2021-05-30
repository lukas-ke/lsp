from lsp.log import NullLog

# TODO: HORRID
WORD_CHARS = "abcdefghijklmnopqrstuvxyzABCDEFGHIJKLMNOPQRSTUVXYZ0123456789_"


def word_start(s, at):
    for n in range(at, -1, -1):
        if s[n] not in WORD_CHARS:
            return n + 1
    return 0


def word_end(s, at):
    for n in range(at, len(s)):
        if s[n] not in WORD_CHARS:
            return n - 1
    return len(s) - 1


def word_at(s, at):
    start = word_start(s, at)
    end = word_end(s, at)
    return s[start:end + 1]


def lines_from_text(text):
    return text.split("\n") + [""]


def partial_update(lines, rng, text):
    if rng.start.line == len(lines):
        lines.append("")  # TODO: Hack

    new_content = text.split("\n")

    l0 = lines[rng.start.line]
    l1 = lines[rng.end.line]

    pre = l0[:rng.start.character]
    post = l1[rng.end.character:]

    if len(new_content) == 0:
        new_content.append([pre + post])
    else:
        new_content[0] = pre + new_content[0]
        new_content[-1] = new_content[-1] + post

    del lines[rng.start.line:rng.end.line + 1]
    for i in range(len(new_content)):
        lines.insert(rng.start.line + i, new_content[i])


class Document:
    def __init__(self, uri, text, log=None):
        self.uri = uri
        self.lines = lines_from_text(text)
        self.version = 0

        if log is None:
            log = NullLog()
        self.log = log.prefixed("Doc")

    def contentChanges(self, changes, version):
        # TODO: If no range given, maybe this is OK and document can
        # be initialized?
        # .. no,  lsp-mode is still unsynchronized.
        assert version == self.version + 1, (
            f"Unsynchronized, {version} vs {self.version}")
        self.version = version  # TODO: Change first
        for ch in changes:
            rng = ch.range
            if rng is None:
                # Full document change
                self.log.info("Full document change")
                self.lines = lines_from_text(ch.text)
                continue
            else:
                partial_update(self.lines, rng, ch.text)

    def getText(self):
        return "\n".join(self.lines)

    def line_n(self, n):
        return self.lines[n]

    def line_at(self, position):
        return self.lines[position.line]

    def word_at(self, position):
        # TODO: Probably Lua-specific
        ln = self.lines[position.line]
        return word_at(ln, position.character)
