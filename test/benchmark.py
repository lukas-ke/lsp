from lua.tokenize import tokenize
from time import time
import lua.build_lua_doc as build_lua_doc
import lua.lua_types as lt


def read_file(file_path):
    with open(file_path, "r", encoding="utf-8") as f:
        return f.read()


def bench_tokenize(file_path):
    times = []

    text = read_file(file_path)
    for i in range(3):
        start = time()
        tokens = tokenize(text)  # noqa: F841
        end = time()
        times.append(end - start)

    print(file_path)
    for n, item in enumerate(times):
        print(f"{n}: {item:.3f}s")


def bench_build_lua_doc(file_path):
    g_env = lt.GlobalEnv()
    times = []

    text = read_file(file_path)
    for i in range(3):
        start = time()
        doc = build_lua_doc.read_lua(text, g_env, file_path)  # noqa: F841
        end = time()
        times.append(end - start)

    print(file_path)
    for n, item in enumerate(times):
        print(f"{n}: {item:.3f}s")


if __name__ == '__main__':
    print("Measure time for tokenizing")
    bench_tokenize("test/workspace/main.lua")  # tiny
    bench_tokenize("test/testdata/big_file.lua")  # big

    print("Measure time for finding scopes")
    bench_build_lua_doc("test/workspace/main.lua")  # tiny
    bench_build_lua_doc("test/testdata/big_file.lua")  # big
