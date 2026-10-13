### Before you write anything: find the function to compare against

Read the golden patch and the code it changes, and find the function the implementation
corresponds to. Then check two things about it, because a program that imports a name the
fix does not create fails at its first line and establishes nothing:

* the **module** exists in the applied tree at the path you will import from;
* the **name** exists in that module, spelled exactly as you will import it.

$sites

If the behavior is not a function of its own -- if the fix puts it inline inside a larger
method, or behind a guard, or fused into a loop that also writes to disk -- then there is
no free function to import, and inventing a plausible name for one is the single most
common way this program is written wrongly. Reach the behavior the way the repository's
own tests reach it: construct the object, call the real method -- intercepting what it
does to the clock, the filesystem or a subprocess exactly as the repository's own test
suite does -- and report what you actually called.

Then **bridge any type simplifications** the specification made. The type bridge is how
each of the specification's types maps onto the repository's values, and this program
carries it out: map each input of the specified function onto the real function's
arguments and the state it reads, and convert what the copy of the implementation returned,
raised or left changed into the repository's own types -- the container the real function
returns, its element types, an array's dtype, shape and mask, the exception class -- before
comparing the two. Compare everything the specification states exactly: `==` takes `1`,
`1.0` and `True` for one another, and `numpy.array_equal` ignores the dtype. Convert from
the copy's result alone, since a conversion that copies a type, a dtype or a shape off the
repository's result agrees with it by construction. Converting the repository's result
into the specification's types instead drops whatever the specification has no field for,
and a change to only that is one this program never sees. What the specification
deliberately leaves out -- an exception's message, an attribute no test checks -- name with
the type abstractions in the module docstring, and leave it out of the comparison. What you
build has to be the specification's input as the repository reads it: an empty sequence
rendered as an empty string the repository cannot parse is a different input, and a
disagreement on it is a fault of the type bridge, not of the implementation.

Where the specification's input is a projection of a richer repository value (a matrix
seen as its dimensions, an object as a few of its fields), draw the other way round:
build the repository value first, the way the repository's own tests build one, read the
specification's input off it, and compare on that projection when the preconditions admit
it. Draw those values so that their projections reach the awkward inputs as well. A
projection no repository value has is then never drawn. Drawing the specification's input
first and searching for a repository value that reads back as it reports every input the
search misses as `unbuildable`, whether a value exists or not, and the bundle is not
certified while it prints one. A tuple Benchproofer hands this program to recheck is the
specification's input all the same, so keep the way from it to a repository value as
well, and report one that nothing reads back as `unbuildable`.

Write that mapping in the module docstring -- the model-to-repository symbol binding, and
each type abstraction, with the projection where the draw starts from the repository -- so
a reviewer can check the type bridge rather than trust it.

`benchproofer:skipped <the function>: <why>` means nothing in this environment can call
the function -- it needs a service, a device or a platform the task's image does not have
-- and not that the function is awkward to reach. A function the repository's own tests
call is one this program can call: a method through its object, as above, and a function
that takes a callable, or only passes a value through to one, by building it around a stub
of your own in that callable's place and reading what flows through -- what the stub was
called with, and what came back out of what the stub returned. Print `skipped` for a
function nothing here can reach, instead of importing something that does not exist or
comparing something else; never for an import that failed, which is this program's own
error to fix.

### What the implementation assumes

$assumed

### Rules Benchproofer checks

$conformance_rules$recorded

### How to write it

Import the real function out of the repository around you: the working copy is on the
import path, so `from <its dotted module> import <the name>` works. Then draw inputs the
specification's preconditions admit, call the real function and the copy of the
implementation on the corresponding inputs, and compare what each returned, what each
raised, and what each left changed.

The one thing that makes this program worthless is writing the repository's side
yourself. If you read the fixed source, work out what it does, and put that in a
function here, then both sides came from the same reading and they agree whatever the
repository does. Call the repository's own code, and the repository's own helpers
around it -- its parsers, its converters, its `boolean()` -- rather than a copy of
them: a hand-written helper that is laxer or stricter than the real one makes the
comparison agree or disagree for reasons that are not the implementation's. Stub only
what reaches outside the process -- a subprocess, the network, the clock, a file outside
a temporary directory, a global registry the code reads, such as a request context or a
site object a running server sets -- and stub it the way the repository's own tests do. A
callable the function is handed as an argument is an input, not the repository's side, so
that one may be yours. Compare first every input the FAIL_TO_PASS tests and the PASS_TO_PASS
tests the test patch adds or edits hand these functions, as those tests build it; then draw
the rest, the awkward ones among them: empty, boundary, duplicated, malformed, unicode. A
disagreement on any of them is worth more than agreement on a million tidy ones.
