`conformance.py` is a program, not a test suite. It runs with no arguments where the
benchmark's tests run, against the task's tree with the golden patch already applied, prints
the lines below, and exits. It imports the standard library and the repository -- nothing
else. The task's environment is the repository's own, with only what the repository installs:
not `hypothesis` or any other fuzzer, so draw inputs with `random.Random(<the seed>)`, and not
the checker's own library, which the copy of the implementation runs without. Do not apply any
patch yourself, and do not write the copy of the implementation into the tree: that would
overwrite the function it is compared against.

$copy

Each function the program reports is named by the dotted path it is reached at --
`package.module.function`, or `package.module.Class.method` for a method, not a bare name --
and that module appears in the program, because Benchproofer checks that what it compared
against is something it imported.

Print one line for each function you compared:

    benchproofer:compared <function> <how many inputs> <how they were drawn>

and one line for each disagreement you found:

    benchproofer:disagrees <function> <the input, what the repository did, what the implementation did>

and after each disagreement, the arguments the implementation was called with, so the
input can be put to this comparison again after this file is rewritten:

    benchproofer:witness <function> <the arguments, as a Python tuple literal>

The tuple is `repr` of the arguments, and it has to read back with `ast.literal_eval`:
numbers, strings, bytes, booleans, None, and tuples, lists, dicts and sets of them. Print
no `witness` line for an input whose arguments are not such values.

Before drawing anything, compare the inputs Benchproofer hands this file. Benchproofer
defines a module-level dict `BENCHPROOFER_REPLAY` before this file's own code runs, mapping a
function's dotted name to a list of argument tuples; read it with
`globals().get("BENCHPROOFER_REPLAY", {})`, since a run with nothing to compare again does
not define it. Put each tuple through the same mapping onto the repository's values and the
same comparison as a drawn input, printing the same lines, then print for each function it
names

    benchproofer:rechecked <function> <how many of the tuples handed to this file were compared>

A tuple the specification's preconditions do not admit is not compared. Print

    benchproofer:inadmissible <function> <its position in the list, from 0>: <why>

instead, and count it out of `rechecked`. Every tuple is either compared or declared
inadmissible; the bundle is not certified while one is neither.

Seed the draw from a literal written in this file, never from the clock, and print the
seed once:

    benchproofer:seed <the seed>

A disagreement nobody can reproduce is not evidence. This file is run more than once --
by the gate now, and again by a reader who wants to see the input for themselves -- and a
program that reseeds from the clock reports a failing input the next run never draws.

Build the repository's side of each input in a step of its own, before the call: the
object the function belongs to, the argument in the repository's own types, the state it
reads. A raise inside the call itself is the function's own behaviour, and is compared
like a return. An input the specification admits that this program could not compare is
not a disagreement. Print one of these lines for it, by the reason, with the error, and go
on drawing:

    benchproofer:unbuildable <function> <the input>: <the error>

when this program could not build the value: the encoding has no image for it, or it built
the value some way the repository does not. Build each admitted value the way the
repository's own callers or tests build it, rather than skipping the ones that fail to
build.

    benchproofer:refused <function> <the input>: <the error>

when the repository refuses the value: built the way its own callers or tests build it, its
constructor or validator raises, because the repository has no such value. That is a
finding about the specification's domain, which admits a value the repository cannot
have. An `Outside the bridge` entry naming such values as ones the repository never has
resolves it, with this program building each input from a repository value so that it draws
none of them, and so does, in a first draft, a model whose types have no such value. Print
the line for every such value drawn.

    benchproofer:copy-raised <function> <the input>: <the error>

when this file's copy of the implementation raised. The implementation this file contains
is the verified one, and it raises nothing its specification does not declare, so when its
copy raises anything else -- a Python class you wrote to replace one of the verifier's types
lacks an operation, say -- the copy is wrong, not the implementation.

The bundle is not certified while this program prints one of these three lines.

A value the preconditions exclude is not compared either. Print

    benchproofer:excluded <the input>: <the line of the specification stating the precondition>

for one you drew and set aside, the line copied as the specification writes it; one that
quotes no line of the specification, and names no entry as below, is counted as not
compared.

`conformance.py` does not compare on the inputs an `Outside the bridge` entry of the third kind
names, on which the fixed function runs only what the golden patch leaves as it was, and
skipping exactly those inputs is not a narrowing of what the specification admits. For each
such input it draws or is handed, it prints its `excluded` or `inadmissible` line with
`Outside the bridge:` and that entry for the reason. Benchproofer looks for the words after
`Outside the bridge:` in the section's own text, so quote at least five words of the entry
exactly as `correspondence.md` writes them, backticks, dashes and punctuation included; a
paraphrase names no entry.

If part of the implementation cannot be compared at all -- it uses a construct you
cannot execute here, or reaches something this environment does not have -- say so
instead of quietly comparing the rest:

    benchproofer:skipped <the function>: <why>

The function is named as the specification does, in a line written out in the program, and
its body need not be copied into the program, since it is not compared. Comparing only the
part that was easy, and exiting zero, reads as agreement about the whole implementation. A part declared `skipped` is recorded as not compared and the
bundle is not certified on it, which is the honest outcome; a part left out without a
`skipped` line is a bundle that passed on nothing.

Aim for $inputs inputs in total. Do not write that number into a loop bound: draw inputs
until you have compared that many or until $seconds seconds have elapsed, whichever comes
first, and report the number you reached. Reaching fewer is recorded, not penalized, so
report what happened rather than the number that was asked for. A function with fewer
inputs than that -- one that takes no argument has exactly one -- is compared on every one
of them, and that leaves nothing uncompared: print no `skipped` line for it.

Exit zero when every comparison agreed, and non-zero when any did not. Print nothing else
on a line that starts with `benchproofer:`: a line Benchproofer cannot read leaves the run
undecided.
