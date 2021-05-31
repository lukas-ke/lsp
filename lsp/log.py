import contextlib


def info_message(prefix, msg):
    return f"{prefix}Info: {msg}\n"


def error_message(prefix, msg):
    return f"{prefix}Error: {msg}\n"


class Log:
    """Simplistic file logger"""
    def __init__(self, log_file, log_level, prefix=""):
        assert log_file is not None or log_level == 0
        self.log_file = log_file
        self.log_level = log_level
        self.prefix = prefix

    def prefixed(self, prefix):
        """Create a copy of this logger that writes to the same file, but with
        a prefix.

        """
        return Log(self.log_file, self.log_level, prefix=prefix)

    def info(self, msg):
        if self.log_level > 1:
            self.log_file.write(info_message(self.prefix, msg))
            self.log_file.flush()

    def error(self, msg):
        if self.log_level > 0:
            self.log_file.write(error_message(self.prefix, msg))
            self.log_file.flush()


@contextlib.contextmanager
def file_logger(log_file_path, log_level, prefix=""):
    if log_level > 0:
        log_file = open(log_file_path, 'w', encoding="utf-8")
    else:
        log_file = None

    log = Log(log_file, log_level, prefix)
    yield log
    if log_level > 0:
        log_file.close()


class StdoutLog:
    def __init__(self, log_level, prefix=""):
        self.prefix = prefix
        self.log_level = log_level
        self.prefix = prefix

    def prefixed(self, prefix):
        return StdoutLog(log_level=self.log_level, prefix=prefix)

    def info(self, msg):
        if self.log_level > 1:
            print(info_message(self.prefix, msg))

    def error(self, msg):
        if self.log_level > 0:
            print(error_message(self.prefix, msg))


# Just for symmetry with file_logger
@contextlib.contextmanager
def stdout_logger(log_level, prefix=""):
    yield StdoutLog(log_level, prefix)


class NullLog:
    def prefixed(self, *args):
        return NullLog()

    def info(self, *args):
        pass

    def error(self, *args):
        pass

# Just for symmetry with file_logger
@contextlib.contextmanager
def null_logger():
    yield NullLog()
