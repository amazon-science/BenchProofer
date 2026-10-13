Run every call you compare in one environment, the one the benchmark's tests run the fixed code
in: one thread of one process, on the platform those tests run on, under one working directory,
time zone, locale, set of environment variables and file system. Between two calls you compare,
change none of these and nothing else the calls read: not a file or a link on disk, and not the
state of an object you pass to both. State the benchmark's tests set between calls -- an option
such as one set through a `set_options` context manager, or a setting a test overrides -- is an
input of the call: the model takes it as a parameter, and a program may set it between calls the
way the tests do. A difference that shows only when one of these changes
between two calls, or only on another platform than the one the benchmark's tests run on, is a
program the task never runs, and not a finding. So is one that shows only in a state of the
environment the benchmark's tests never build, which is not an input: a special file such as a
FIFO or a device where the code reads a file, an executable that never exits, a configuration
the tests always set left missing or unset, a full disk, a permission the tests never take
away. So is a difference that shows only through what earlier calls in the same process left
behind -- a cache an earlier call filled, an exception a library raises only the first time it
is asked about a value -- unless a FAIL_TO_PASS test or a PASS_TO_PASS test the test patch adds
or edits reaches it: there the code's result depends on its history rather than its arguments,
so compare with the result it gives every time after the first.
