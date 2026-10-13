* the bug the task reports: the behaviour before the fix, written again under this
  specification;
* a partial-domain one: right on some inputs the precondition admits, wrong on others;
* a boundary one: wrong only at an edge -- empty, one element, the largest value, a tie;
* a control-flow one: a branch taken the wrong way, a step skipped or done out of order;
* an ungrounded one: it meets the postcondition by returning what the axiom of an unchanged
  callee, or a helper function, says, without doing the work the task asks for.

Wrong means what the task means by wrong: on at least one input the specification admits,
the implementation returns something the task considers incorrect. The benchmark's own
tests are what decide that, and they are run on what you submit, so aim at behaviour they
can see, and at a mistake a competent programmer could make: a specification that admits
only absurd implementations is stronger than one that admits plausible ones. Accepted means
the checker cannot refute it under this specification, unchanged.

Submit every wrong implementation you write, whether or not you expect the checker to
accept it. One the checker refutes is evidence that the specification holds there, and
counts as that toward the gate's result. An implementation you believe is correct is not
an attack, and decides nothing.
