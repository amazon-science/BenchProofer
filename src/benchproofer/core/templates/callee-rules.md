A callee the changed code calls is unchanged when the fix does not change its behavior, whether
the code before the fix made the call or the golden patch adds it. An edit that leaves the
callee's behavior as it was -- type annotations, a renamed attribute or variable, a helper
inlined into it, the same function bound under a new module or name, layout, comments and
docstrings -- does not change it. An unchanged callee is modeled -- a definition in the model
computing what it computes -- when the checker can state exactly what it computes on the inputs
the changed code gives it, with a short definition: string operations, lookups, arithmetic over
the values the model already has. Otherwise it is an axiom the model calls with the call's
arguments, with the weakest contract under which the golden patch's own calls to it verify.
Large library dispatch, I/O, hashing, serialization, a callee whose result depends on
something outside the process, and any callee the model could only approximate stay axioms. A
modeled callee's definition goes in the `axioms` region under the line `benchproofer:models
<callee>`, and is checked against the real callee as an axiom is.

Either way its result is never a parameter. A parameter that holds what an unchanged callee
computes from the function's inputs -- a parsed number, a rounded or quantized value, a
normalized string -- is the callee's result handed to the model: take the input it is computed
from, and model the callee exactly or call it as an axiom with the call's arguments. A rounding
or parsing callee the checker cannot state exactly, such as decimal rounding with a mode
argument, stays an axiom, and the mode is one of its arguments, so the obligation pins it. A
function the golden patch adds, or a callee whose behavior it changes, is neither modeled under
a `benchproofer:models` line nor an axiom: that is the operation the task is about, so assuming
it away leaves nothing for the specification to be strong about. It is modeled in the
implementation, never as a parameter. Code inside a changed function is not a callee either, a
branch the golden patch leaves as it was included: no axiom represents it; it is modeled in the
implementation, or left out by an `Outside the bridge` entry of the third kind.
