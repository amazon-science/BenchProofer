A definition under a `benchproofer:models <callee>` line of the `axioms` region represents its
callee as an assumption does, and everything here holds of it as of one. What it states is
all it computes: an input a call site can pass on which it and the real callee return, raise
or modify different things refutes it, and the `refuted` line quotes the line of the
definition that computes the value they differ on.

The proof relies on an assumption where the specification's functions call the callee, so what
it needs is that the assumption holds of the arguments those calls can pass. Draw the inputs
of those functions from what their preconditions admit, derive the callee's arguments from
them the way each call site derives them, and aim there, where `axioms.py`, written by whoever
wrote the assumption, would not look: empty and boundary values, malformed input, values that
round or overflow, unicode and encodings in the input, aliasing, an argument the callee itself
mutates, an error the callee raises where the assumption says it returns. An argument no call
site can pass -- a name the implementation never looks up, a value those functions never
build -- is outside what the proof relies on, and a disagreement there is not one.

Each input is of the type the call site declares: its annotation, its docstring, or the
interface the statement gives. Use another type only where a call site in the repository, or
a FAIL_TO_PASS test or a PASS_TO_PASS test the test patch adds or edits, passes one, and for
this `bool` is not `int` and `float` is not `int`. Within that type, use values of any size,
shape or boundary short of the interpreter's own limits, and none that breaks a language
contract, which the system prompt says is no evidence either way. The interpreter's own limits
are not inputs: the limit on the digits of an int converted to a str, the recursion depth,
memory running out, an int too large for a float. On an input of the declared type the
preconditions admit, a raise of the real callee where the assumption says it returns refutes
the assumption: real callees raise, and an assumption that a callee always returns normally
holds only if it never raises on any input its preconditions admit. An input on which the real
callee does not return at all -- it runs without end, or for longer than any of the
benchmark's tests waits -- refutes nothing where, as a result, the function the fix changes
does not return either: the model's domain admits only inputs on which that function returns
normally, so the input is outside it.

Call the callee the way the task's code calls it, and hold fixed everything that call site
fixes. The assumption is made of that call: a keyword argument, a flag or a configured
object the call passes is passed exactly as the call passes it, and only what reaches the
callee as the task's input is varied. A call with other arguments tests a program the task
never runs.

$environment_rules An assumption is made of the process it holds in, the one the program
starts in: which thread or process runs a call, and how much stack is left when it is made,
are not arguments either, so start no thread, no second process and no subprocess, and leave
the recursion limit as it is. Any of these tests a program the task never runs.

Stub only what reaches outside the process -- a subprocess, the network, the clock, a file
outside a temporary directory, a global registry the code reads, such as a request context or a
site object a running server sets -- and stub it the way the repository's own tests do. A
callee run against such a stub, in your program or in `axioms.py`, runs as the benchmark's
tests run it, so the stub changes nothing the call reads. State the benchmark's tests set
between calls is an input of the call, as above, and not a stub: set it between your calls the
way the tests do.

Refute what the assumption states, not how the model represents it. The specification
states the callee's behaviour at an abstraction of its own -- strings as code-point lists,
opaque handles, int-scaled values -- and the bundle's `correspondence.md` says how that
maps onto the real values. A real result that is not literally of the modeled type is that
mapping, not a disagreement: what disagrees is a real result that breaks a property the
assumption states. An assumption stating its callee as a function of its arguments states
that two calls on the same arguments return the same value. It is refuted by two such calls
that disagree, not by a side effect nothing in the specification reads, such as a cache or
`sys.modules` growing, or output printed. Two calls whose arguments an `Outside the bridge`
entry reads alike are one call to the model, and their disagreement refutes nothing.

What an assumption states is its code: its clauses, and the declaration they belong to,
which says what the callee takes and returns and whether it is a function of its arguments.
A docstring or a comment beside it is prose the checker never reads. So each `refuted` line
quotes, as written, the line of the `axioms` region it breaks.

A program runs with no arguments, prints its protocol lines, and exits. Report a
disagreement only when your program observed it: Benchproofer re-runs the file and reads
what it printed, so a claim the run does not support is worth nothing, and a program that
crashes on its own bug is set aside rather than counted toward the gate's result.
