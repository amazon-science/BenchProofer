## The code this is about

The golden patch defines or edits these functions, methods, classes and names, by the file
each is in, a method under its class:

$listed
$others
**Model the fix, not a re-imagining of it.** Read the changed functions AND their callees
first. What you formalize is the code listed above. You may NOT model a different function
that happens to satisfy a weaker specification: one that exists only in your file leaves
nothing in the repository to compare your implementation with, and the bundle is rejected
for it.

**Multiple changed functions → multiple contracted functions.** Model each changed function
whose behavior the task asks for as its own function with its own contract and body, in the
numbered regions the system prompt describes (`spec.2`, `impl.2`, and so on). Prefer that
over collapsing several functions the golden patch changes into one function of your own --
the latter yields fewer comparisons against the repository and a less faithful model -- and
over modelling one of them only, which leaves the rest of the fix unspecified.

$task_rules

**Model the function the FAIL_TO_PASS tests call**, or the function the golden patch changes on
the path from it, under type abstraction and nothing else. The input cases the golden patch
distinguishes are the input cases the model distinguishes, and each input case's modeled result
corresponds to what the golden patch computes. The model's **domain** is the one the system
prompt describes.

$outside_rules

The modeled function's **parameters** are what it reads at entry: its arguments and the
object state it reads. A callee it calls is stated as the system prompt's `Callees the fix
does not change` says, and its result is never a parameter. The modeled function's **result**
is what the FAIL_TO_PASS tests and the PASS_TO_PASS tests the test patch adds or edits check:
what the function returns, what it raises, and what it leaves changed. Every step of the
implementation is then the same concrete operation, the same operation over a refined type that
represents the value, or a call to an unchanged callee; a changed operation this checker cannot
express is not allowed to become a parameter, it is modeled deeply instead: computed inside the
model.

Two parameters are forbidden, and they are the common way a model stops being about the
task:

* **A value the fix itself computes is never a parameter** -- a guard's condition, a
  filtered or sorted list, a flag saying which branch applies, a new constant. Take what it
  is computed *from* and compute it inside the model. A model handed `planEmpty : Bool` or
  an already-filtered list assumes the very thing the fix decides, so no implementation of
  it can be wrong the way the task is about.
* **A value the repository fixes at that point is a constant of the model, not a
  parameter.** A module-level roster the function reads is a constant: as a parameter its
  domain is every value of its type, and the specification then has to hold of values the
  repository never has.

Pin the behavior the statement and the tests above demand, strongly enough that no
wrong implementation of the modeled behavior satisfies it. Ask of your specification: could
an implementation satisfy it and still fail one of the tests above? If it could, the
specification is the defect.

Under type abstraction: a `str` may become a sequence of code points; a rich object -- a
matrix, a query set, a syntax tree, a data frame -- becomes a structure with only the fields
the fix touches; a raise becomes a declared exception the contract names, or a result that
contains the error. The comparison maps each such simplification back onto the real
function and runs it, so a behavior buried inside a larger method is still modeled as that
method, under a type abstraction.

**No leakage.** The specification is shown to whoever solves the formalized task. It must
not name the patched file or function (in identifiers OR docstrings/comments), or use an
identifier copied from a patched repository symbol, unless the task's statement names it.
The same holds of the tests: reproducing a line the test patch adds leaks the golden patch
as surely as quoting the fix does, so read them for the behavior they check and state that
behavior in the task's own terms. Text the statement itself quotes is already public.
