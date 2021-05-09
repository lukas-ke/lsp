from . lua_types import (
    Arg,
    Comment,
    Function,
)

def add_built_ins(d):
    d["print"] = Function(
        name="print",
        args=[Arg(name="...")],
        doc=Comment(
            "Receives any number of arguments and prints their values to stdout, using the tostring function to convert each argument to a string.\n\n" +
            "print is not intended for formatted output, but only as a quick way to show a value, for instance for debugging. For complete control over the\n" +
            "output, use string.format and io.write."))
