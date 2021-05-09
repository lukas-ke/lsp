import lua.lua_re as lr


def run(print_env):
    assert lr.in_require('local util = require("Ut')
    assert not lr.in_require('util = flurm("Ut')

    m = lr.match_require('util = require("Ut')
    assert m.group(2) == "Ut"

    if print_env:
        print(m.group(2))


if __name__ == '__main__':
    run(True)
