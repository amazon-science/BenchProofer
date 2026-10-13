A program Benchproofer runs for this task runs where the benchmark's tests ran and passed, in
the task's own image, so whatever those tests run can be run there: the repository and what it
installs, and a browser engine, another language's interpreter or a server the tests start. How
the tests call a function is how a program here can call it. A program runs from the
repository's root, which is on the import path, and a directory of tests is not, so a program
that builds an input with a test module or a test app first puts on `sys.path` the directory the
benchmark's own test runner puts there (Django's `tests/`, say). A file the test patch adds or
changes may not be in the tree as the patch leaves it: build what a test of it builds in the
program itself.
