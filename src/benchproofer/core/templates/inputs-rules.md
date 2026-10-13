## Callees whose definition or axiom failed in two rounds

Each callee below was first stated by a definition under its `benchproofer:models` line or by
an axiom over the call's arguments, as the rule for callees the fix does not change requires.
That definition or axiom then failed in two rounds of this run (a round is one pass of the gates
and the review over the bundle), with a repair between them: in each round, the axiom-soundness gate refuted it, or the checker reported an error on a line of
its declaration. Benchproofer found this in the records of those rounds:

$callees

For these callees alone there is a third way: the result of a call of one of them may be an
input of the model, a parameter the implementation reads where the changed code makes the
call, for one of two reasons:

* (a) its result can differ between two calls with the same arguments, because it depends on
  something outside the process -- a server or device it talks to, a subprocess it runs, the
  clock, randomness;
* (b) the checker cannot state it, as a definition or as an axiom over its arguments, within
  the checker's limits: give the limit, for example a recursive type, which Nagini cannot
  express.

Every other callee is stated as the rule for callees says, and its result is never a
parameter; for a callee listed above, this section takes the place of that rule's "its result
is never a parameter". Where the model takes the result of a callee listed above as an input, these four
conditions hold:

1. **The call is an unchanged callee's, with arguments the fix leaves as they were.**
   What a function the golden patch adds, a callee whose behavior it changes, or code inside a
   changed function (a branch or guard of it included) computes is never an input: that is the
   operation the task is about. Nor is the result of a call whose arguments the golden patch
   adds, changes or computes, even for a callee listed above: the input would then hold what
   the fix computes, and the model would assume the very thing the fix decides.
2. **The reason holds.** It is (a) or (b), as it applies to that call; a callee that could
   be modeled or stated as an axiom is not taken as an input.
3. **The input holds what the real callee returns.** The model's domain admits every value the
   real callee returns on the inputs the benchmark's tests and the statement hand the changed
   code, as it admits every such input of the changed function's own. `conformance.py` hands
   the implementation the real callee's result: its repository side makes the call as the
   changed code does, to the callee itself or to the stub the repository's own tests put in its
   place, and the implementation is given what that call returned. Where the changed code calls
   the callee more than once, each call's result is an input, in the order the calls are made;
   where the number of calls depends on the input, the results are a sequence the
   implementation consumes in order.
4. **The call is stated as an output.** Taking the result as an input leaves the call itself
   unstated -- which callee is called, with which arguments, how many times -- so an
   implementation that made the call with other arguments would read the same input and meet
   every obligation. The model states each such call as an output: the arguments of each call,
   in the order the calls are made, or, where the changed code makes the call for some of the
   elements it goes through and not others, for each element whether it made the call and with
   which arguments. An obligation states what they are, and `conformance.py` compares them
   with the arguments the repository side's call was made with.

Each callee whose result the model takes as an input is listed in `correspondence.md`, in a
section of its own after `Outside the bridge`, `## Callee results taken as inputs`: one bullet
per callee, with the callee as a dotted path, its call site as `file:line` at the base commit,
and its reason, (a) or (b). The section is the one line `Nothing.` when the model takes none,
and anything else under its heading is read as an entry. In `Operations` such a call is a
`refinement`: say which parameter holds the result of which call, and which output states
its arguments. The run report lists each entry under the same heading.

The equivalence auditor checks each callee `correspondence.md` lists under `Callee results
taken as inputs`, and any other parameter that holds a callee's result, against the list and
the four conditions. An input holding the result of a callee the list does not name is a
finding, with the verdict `unsound`, and so is an input that breaks a condition, conditions 1
and 4 above all.
An input that meets every condition is a `refinement` row.
