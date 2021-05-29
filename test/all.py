from . import test_lua_db
from . import test_lua_re
from . import test_doc
from . import test_fragment
from . import test_sillyparse
from . import test_build_lua_doc
from . import test_annotation
from . import test_invalid

print_env = False

test_lua_db.run(print_env)
test_lua_re.run(print_env)
test_doc.run(print_env)
test_fragment.run(print_env)
test_sillyparse.run(print_env)
test_build_lua_doc.run(print_env)
test_annotation.run(print_env)
test_invalid.run(print_env)
