import lua.sillyparse as sp


def single_line_f(text, lineNum):
    def get_this_line(n):
        assert lineNum == n
        return text
    return get_this_line


def multi_line_f(lines):
    def get_this_line(n):
        return lines[n]
    return get_this_line


def test_find_string_intervals(print_env):
    def intervals(s_raw, replace=None):
        s = s_raw
        if replace is not None:
            for k in replace.keys():
                s = s.replace(k, replace[k])

        res = sp.find_string_intervals(s)
        if print_env:
            print(f"{s} -> {res}")
        return [(r.start, r.stop) for r in res]

    hd = {"#": '"'}
    hs = {"#": "'"}
    assert intervals('"abc", "123"') == [(0, 4), (7, 11)]
    assert intervals('"abc", "123') == [(0, 4), (7, 10)]
    assert intervals('"#abc#", "#123#"', hs) == [(0, 6), (9, 15)]
    assert intervals("'#abc#', '#123#'", hd) == [(0, 6), (9, 15)]
    assert intervals(r'"\"abc", "#123#"') == [(0, 6), (9, 15)]
    assert intervals(r'"\"abc", "#123#"') == [(0, 6), (9, 15)]
    assert intervals(r'""""') == [(0, 1), (2, 3)]
    assert intervals(r'"\"abc') == [(0, 5)]


def _find_caret_pos(lines):
    line_num = None
    char_num = None
    for n, line in enumerate(lines):
        caret_pos = line.find("|")
        if caret_pos != -1:
            assert line_num is None
            lines[n] = lines[n].replace("|", "")
            line_num = n
            char_num = caret_pos
    assert line_num is not None, "No caret pos?"

    return line_num, char_num


def test_find_arglist_start_multi_line(print_env):
    def find_start(lines):
        line_num, char_num = _find_caret_pos(lines)
        found = sp.find_arglist_start(multi_line_f(lines), line_num, char_num)
        if print_env:
            s = "\n".join(lines)
            print(f'"{s}" -> {found}')
        return found

    assert find_start(
        ["call_function(",
         "1, 2,"
         "3|"]) == (0, 14)

    assert find_start(
        ["call_function((1+2)"
         "'1, 2',"
         "3|"]) == (0, 14)


def test_find_arglist_start_single_line(print_env):
    def find_start(s):
        caret_pos = s.find("|")  # Caret
        s2 = s.replace("|", "")
        found = sp.find_arglist_start(single_line_f(s2, 0), 0, caret_pos)
        if print_env:
            print(f'"{s}" -> {found}')
        assert found[0] == 0
        return found[1]

    assert find_start("abc(1, 2|, 3)") == 4
    assert find_start("abc(1, (2+3)|, 3)") == 4
    assert find_start("abc(1, (2+3|), 3)") == 4
    assert find_start('abc(1, 2,"|') == 4
    assert find_start('abc(1, 2,"asdf(|') == 4
    assert find_start('abc(1, 2, 1 + asdf(1 + 2|)') == 19
    assert find_start('abc(1, 2,"asdf(|') == 4
    assert find_start('abc(1, 2, f(5)(a|') == 15
    # TODO: Strip comments
    # assert find_start('abc(1, 2, 3, 4, -- test(crap|') == 4


def test_find_indexing_before(print_env):
    def f(lines):
        line_num, char_num = _find_caret_pos(lines)

        def get_line(n):
            return lines[n]

        return sp.find_indexing_before(get_line, line_num, char_num)

    assert f(["abc|"]) == (0, (0, 3))
    assert f(["a.b.c.f|"]) == (0, (0, 7))
    assert f(["abc", "cde|"]) == (1, (0, 3))
    assert f(["abc", ",d|"]) == (1, (1, 2))
    assert f(["abc", ",,|"]) is None
    assert f(["  abcde  ", "  |"]) == (0, (2, 7))
    assert f(["abc", " abc", "|"]) == (1, (1, 4))
    assert f(["abc", " a.bc", "|"]) == (1, (1, 5))


def run(print_env):
    test_find_string_intervals(print_env)
    test_find_arglist_start_single_line(print_env)
    test_find_arglist_start_multi_line(print_env)
    test_find_indexing_before(print_env)


if __name__ == '__main__':
    print_env = True
    run(print_env)
