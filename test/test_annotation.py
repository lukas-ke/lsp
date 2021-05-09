from lua.annotations import parse_comment, strip_prefix, strip_annotations


COMMENT_1 = """-- Hello
--@param Arg1 FirstType The description goes here
--and can continue here
--@param Arg2 SecondType
--@param Arg3 ThirdType Docs for third type
--@return integer
--@return Some.Other.Type
"""

COMMENT_1_STRIPPED_PREFIX = """Hello
@param Arg1 FirstType The description goes here
and can continue here
@param Arg2 SecondType
@param Arg3 ThirdType Docs for third type
@return integer
@return Some.Other.Type"""

COMMENT_1_STRIPPED_ANNOTATIONS = """ Hello
"""


FIRST = True
PREV_TITLE = ""
NUM = 0


def _title(print_env, title):
    global FIRST
    global PREV_TITLE
    global NUM
    PREV_TITLE = title
    NUM = NUM + 1
    if print_env:
        if not FIRST:
            print()
        print(f"{NUM}. {title}:")
        FIRST = False


def _end(print_env):
    if print_env:
        print(f"<end of {PREV_TITLE}>")


def test_strip_prefix(print_env):
    _title(print_env, "test_strip_prefix")
    c = strip_prefix(COMMENT_1)
    if print_env:
        print("Input:")
        print(COMMENT_1)
        print("Output:")
        print(c)
    assert c == COMMENT_1_STRIPPED_PREFIX
    _end(print_env)


def test_parse_comment(print_env):
    _title(print_env, "test_parse_comment")
    annotations = parse_comment(COMMENT_1)

    if print_env:
        print("Input:")
        print(COMMENT_1)
        print("Annotations:")
        for num, a in enumerate(annotations):
            print(f"{num}: {a}")

    assert len(annotations) == 5

    assert annotations[0] == (
        'param',
        'Arg1',
        'FirstType',
        'The description goes here\nand can continue here\n')

    assert annotations[1] == ('param', 'Arg2', 'SecondType', None)

    assert annotations[2] == (
        'param',
        'Arg3',
        'ThirdType',
        'Docs for third type\n')

    assert annotations[3] == ('return', 'integer')
    assert annotations[4] == ('return', 'Some.Other.Type')


def test_strip_annotations(print_env):
    _title(print_env, "test_strip_annotations")
    c = strip_annotations(COMMENT_1)
    if print_env:
        print(c)
    assert c == "Hello"


def run(print_env):
    test_strip_prefix(print_env)
    test_parse_comment(print_env)
    test_strip_annotations(print_env)


if __name__ == '__main__':
    print_env = True
    run(print_env)
