"""Twin-artifact model for astropy__astropy-13977.

Behaviour under specification (stated as desired behaviour, not as an edit):

  A numeric operation dispatcher protects the work of evaluating an operation
  on a collection of operands. When that protected evaluation completes
  successfully the dispatcher yields its ordinary computed result.

  When the protected evaluation instead fails with a recoverable error (the
  operands could not be combined), the dispatcher must NOT unconditionally
  surface that error. It first inspects the operands: if AT LEAST ONE operand
  is of a kind that supplies its own operation handler (an object that opted
  into custom dispatch, rather than one of the recognised built-in kinds), the
  dispatcher must abstain — yielding the "not handled here" sentinel — so that
  the other operand's handler is given the chance to complete the operation.
  Only when EVERY operand is one of the recognised
  built-in kinds (none supplies its own handler) is the recoverable error
  surfaced to the caller.

  Equivalently: a recoverable failure is propagated iff every operand is a
  recognised built-in kind; otherwise the dispatcher abstains. A successful
  evaluation is always returned as-is.

The operand collection is modelled as `List[int]` of per-operand kind flags
(0 = a recognised built-in kind that supplies no custom handler; 1 = an operand
supplying its own custom handler). The recoverable-failure condition is a
boolean. The three observable outcomes are encoded as result codes
(0 = ordinary computed result; 1 = the "not handled here" sentinel; 2 = the
recoverable error is surfaced). The classification predicate is modelled deeply
and validated against the real per-operand test by axiom_check.py (G-AX).

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List
from nagini_contracts.contracts import *
from nagini_contracts.obligations import MustTerminate


# axioms-start
# (No consumed @ContractOnly axiom: the protected body's unchanged callees are
# summarised by `recoverable_failure`, and the one genuinely-new operation —
# the operand classification and the abstain-vs-surface dispatch — is modelled
# deeply below and validated against the real predicate by axiom_check.py.)
# axioms-end


# pure-start
@Pure
def all_recognised(flags: PSeq[int]) -> bool:
    """True iff every operand kind flag is 0 (a recognised built-in kind that
    supplies no custom handler). Front-recursive so a single unfold is
    available per loop step."""
    if len(flags) == 0:
        return True
    return flags[0] == 0 and all_recognised(flags.drop(1))


@Pure
def has_custom_handler(flags: PSeq[int]) -> bool:
    """True iff at least one operand supplies its own custom handler."""
    return not all_recognised(flags)
# pure-end


def dispatch_ufunc(io_kinds: List[int], recoverable_failure: bool) -> int:
    # pre-conditions-start
    Requires(Acc(list_pred(io_kinds), 1 / 2))
    # Each operand flag is well-formed: 0 = recognised built-in kind (no custom
    # handler), 1 = operand supplies its own custom handler.
    Requires(Forall(int, lambda k:
        (Implies(0 <= k and k < len(io_kinds),
                 io_kinds[k] == 0 or io_kinds[k] == 1),
         [[io_kinds[k]]])))
    Requires(MustTerminate(2))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(io_kinds), 1 / 2))
    # Outcome is exactly one of the three observable codes.
    Ensures(Result() == 0 or Result() == 1 or Result() == 2)
    # A successful protected evaluation is returned as-is.
    Ensures(Implies(not recoverable_failure, Result() == 0))
    # A recoverable failure is surfaced (code 2) iff every operand is a
    # recognised built-in kind; otherwise the dispatcher abstains (code 1).
    Ensures(Implies(recoverable_failure and all_recognised(ToSeq(io_kinds)),
                    Result() == 2))
    Ensures(Implies(recoverable_failure and has_custom_handler(ToSeq(io_kinds)),
                    Result() == 1))
    # post-conditions-end
    # impl-start
    if not recoverable_failure:
        # The protected evaluation completed; yield the ordinary result.
        return 0
    # invariants-start
    # invariants-end
    # PRE-PATCH (buggy) skeleton: the protected evaluation is NOT guarded, so a
    # recoverable failure is surfaced unconditionally — the operands are never
    # inspected for a custom handler, and the dispatcher never abstains.
    return 2
    # impl-end
