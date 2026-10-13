Correct means what the task means by correct: on every input the specification admits, the
implementation returns what the task considers right. A control is not put to the
benchmark's tests. Benchproofer runs it through the bundle's `conformance.py` in place of the
reference implementation, which compares it with the fixed code, and one that disagrees
there is wrong. One that `conformance.py` cannot run as written -- in a language the
repository cannot run, or over values only the checker has -- or cannot decide rests on the
checker's acceptance alone, and one the checker then refuses is undecided, for the attack
validation auditor to rule on with your claim. So correctness is yours to make sure of,
and it comes first: an implementation that is not correct is not evidence about this
specification, however elegant it is, so aim for one you are sure of on every input,
including the edges the task mentions.

This is the opposite check from an attack, and attacks cannot make it. A specification that
refuses everything survives every attack ever written and is still useless: it demands
something the task never asked for, so the only implementation that satisfies it is the one
its author had in mind, and every other correct implementation is marked wrong. A different
correct implementation the checker accepts shows that this one does not, so a structurally
different but correct control must verify: prove it unambiguously, `verify` exiting 0,
before you file it. Where the checker proves, a refusal is either the specification ruling
the control out or a proof the control lacks -- an invariant a loop does not state, a lemma
nobody called, an assertion the solver needs to take a step -- and the checker does not say
which, so write that proof in the control's own regions. If the checker still refuses one
you are sure is correct, submit it all the same as unproved, and say in its claim what you
tried. A falsifier's refutation names an input, and on an input the task allows it is a
finding about the specification. A prover's refusal of a control you could not prove decides
nothing by itself: the attack validation auditor is shown it with your claim, and rules whether
it is correct and whether the specification or a proof it lacks refuses it.

Write it a genuinely different way, and the more different the better: another algorithm,
another order of the same steps, another intermediate representation, a recursion where the
solution file iterates. The reference implementation written again under new names decides
nothing. Benchproofer drops a file as a repeat only when its code matches the reference
implementation's, or that of one already on record, once comments, indentation and blank
lines are left out, so it does not drop a renamed copy.
