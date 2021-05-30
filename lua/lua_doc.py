from lua.lua_types import EmptyEnv

EMPTY_ENV = EmptyEnv()


class LuaDoc:
    """A parsed representation of a Lua file.

    Represented as overlapping line ranges with local scopes:

        scopes= [
          (range(0,12): LocalEnv(...)),
          (range(0,3): LocalEnv(..)),
          ...
        }
    """

    def __init__(self, scopes):
        assert isinstance(scopes, list)
        self.scopes = scopes

    def scope_at(self, pos):
        narrowest_matching = None

        def shorter_range(lhs):
            if narrowest_matching is None:
                return True
            rhs = narrowest_matching[0]
            return (lhs.stop - lhs.start) < (rhs.stop - rhs.start)

        for r, scope in self.scopes:
            if pos.line in r:
                if shorter_range(r):
                    narrowest_matching = (r, scope)

        if narrowest_matching is None:
            return EMPTY_ENV
        return narrowest_matching[1]

    def pretty_str(self):
        lines = []
        for r, scope in self.scopes:
            lines.append(f"Scope: {scope.scopeName} ({r.start}->{r.stop}) {{")
            lines.append(scope.pretty_str(indent=0, heading=False))
            lines.append("{")
            lines.append("")
        return "\n".join(lines)
