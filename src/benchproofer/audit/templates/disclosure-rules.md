The question is what a solver can get out of the specification, and a reader who has just
seen the golden patch cannot judge it: once you know the intended algorithm, every
specification looks like a restatement of it, and the ones that would really hand it over
stop standing out. So the implementation is withheld, the golden patch is withheld, and
what you have is the spec view: what a solver is shown, the specification with the
implementation and proof removed.

What a recoverable implementation looks like, each under the name a finding gives it:

* `loop` -- the specification spells out a sequence of steps, so satisfying it is a matter
  of copying those steps into code: a loop or a fold, or a helper that simulates one by
  passing its partial results and flags from step to step as arguments. A specification
  that says "returns what this loop returns" is a copy of some implementation with a
  `forall` in front of it.
* `intermediate` -- it names intermediate results or helper structures that only one
  particular algorithm would have, so it describes a way of solving the task rather than
  what solving it means.
* `table` -- it contains the expected outputs as a table, listed for particular inputs
  rather than said of all of them.
* `literal` -- it contains the expected value as a constant.
* `oracle` -- it pins the result to a term the spec view itself provides instead of
  grounding it in the inputs, that is, deriving it from them. A postcondition has to be
  dischargeable only by the real computation, and one that equates the result to a helper,
  to a lookup, or to a constant that an assumption (an `axiom`, an `opaque` declaration or a
  `@ContractOnly` function) pins exactly is discharged by returning that term --
  `return expected(x)`, or a bare `return 2` against `Result() == 2` -- with the work never
  done. What grounds a result instead is a structural predicate over the input the task
  already has: a length, a membership, an order, an element-wise or arithmetic relation.
  Then the result is something the modeled computation has to produce, rather than
  something equal to a term already written down. This one is a finding even where the
  term is something the code before the fix already had: what is handed over is not the
  term but that the result *is* it.

What it does *not* look like: a specification that fully pins down the required result in
the task's own terms. That is what a good specification does. "The result is the fewest
coins adding to the amount" says exactly what is required and leaves the solver to work out
how; that is not disclosure, even though it determines the result. The question is whether
the *method* has been handed over, not whether the *result* has been described.

Judge what the specification reveals *beyond* the task statement and the code as it stood
before the fix, both of which a solver has in front of it. A name, a helper, a case split, a
constant or a sequence of steps that the code before the fix already has discloses nothing:
the specification is naming what the solver is looking at. What can be handed over is what
the fix adds -- the behavior the solver is asked to produce.

So that a specification can be copied into code is not a finding on its own, nor that its
proof closes by `rfl` or `decide`, nor that taking `result =` off it leaves a body that
computes the result. A specification that states its result as a function of the input -- a
case split naming the result in each case -- can be copied into code by construction, and
that is the specification describing the result; the cases there are what the specification
says, and no one term gives the result. That holds whether a case names a constant or a
term built from the inputs, and whether its condition is stated over the inputs or over an
assumption's value, such as `Implies(eq_class(i, j) == EQ_TRUE, Result() == ONE)`; nor is
such a split a `table`, since each case says the result of every input that meets it. The
same split written once as a helper and equated to the result -- `out = entryFor i j eq kd`,
where `entryFor` is that case split naming the result in each case -- is the specification
describing the result too, as if the cases were written inline. A helper that computes its
value -- a loop, a fold, a sum over the input -- is not such a split: equating the result to
it is `oracle`, unless it defines a notion the task itself uses (below). A postcondition
naming one constant for every input the precondition admits is `literal`. What hands the
method over is one of the five constructs above, in a line you can quote.

A verifier's language often has only one way to define a result: a pure function, usually
recursive, over the input. "The runs of equal adjacent elements of a list" is written as a
function that takes the list apart one element at a time, because that is how the language
defines a thing, and so it can be run. A helper like that is the specification, not a second
implementation, when what it defines is a notion the task itself uses -- a run, where one
ends, what is dropped, what is kept. A helper that exists for the proof -- a lemma, or a
function that says how partial results fit together -- tells the solver how to prove, not
what to compute, and is not disclosure either. Judge what each definition says rather than
what the comments around it call it: a comment calling a helper declarative does not make it
so, and one calling it an implementation does not make it one.

A verdict of `unsound` rests on findings, each naming one of the five constructs and quoting
the line of the specification it rests on, copied character for character: a reader can
check a quoted line against the specification and cannot check an impression.
