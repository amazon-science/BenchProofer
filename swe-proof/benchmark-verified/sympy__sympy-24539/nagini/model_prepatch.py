"""Twin-artifact model for sympy__sympy-24539.

Behaviour under specification (stated as desired behaviour, not as an edit):

  A multivariate polynomial can be rendered as an algebraic expression over a
  chosen sequence of generator symbols. The rendering selects, exactly once, the
  sequence of generator symbols it will build the expression over, and that
  sequence is the only input that controls which symbols appear in the result:

    * when the caller supplies NO symbols, the polynomial's own default
      generator symbols are used;
    * when the caller supplies a sequence whose length equals the polynomial's
      number of generators, THAT supplied sequence is the one used — the caller
      gets exactly the symbols they asked for, in order;
    * when the caller supplies a non-empty sequence whose length does NOT match
      the number of generators, the request is rejected with a value error and
      no expression is produced.

  The discriminating case the contract pins: a supplied sequence of the correct
  length must be the sequence the expression is built over (element for element,
  in order) — never silently replaced by the polynomial's default symbols.

Generator-symbol sequences are modelled as `List[int]` of symbol identities
(Nagini bans the rich-object operations); the selected sequence — the sole
quantity the rendering's symbol choice controls — is the modelled result, with
its element-wise relation to the supplied sequence carried by `PSeq[int]`. The
rejection of a mismatched count is a user-defined exception class (a builtin
exception in an `Exsures` crashes the Nagini translator; mapping.md).

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List
from nagini_contracts.contracts import *


class SymbolCountError(Exception):
    """Signals that a non-empty supplied symbol sequence has a length that does
    not match the number of generators. Stands in for the value error the
    desired behaviour raises (a builtin exception in an `Exsures` crashes the
    Nagini translator; mapping.md)."""
    pass


# axioms-start
# (no axiomatized callees: the quantity under specification is which generator-
# symbol sequence is selected to render the expression over. The downstream
# expression builder is a callee that is a deterministic function of
# (term dict, selected symbols); the selected sequence alone controls the
# rendered result, so it is modelled directly and no callee contract is
# consumed. See mapping.md / refinement.md.)
# axioms-end


# pure-start
# (no pure helpers needed: the selection is pinned by direct element-wise
# equality of the modelled result to the relevant input carrier.)
# pure-end


def select_render_symbols(symbols: List[int], default_symbols: List[int],
                          ngens: int) -> List[int]:
    # pre-conditions-start
    # `symbols` is the caller-supplied generator-symbol sequence (read-only),
    # `default_symbols` the polynomial's own generator symbols (read-only).
    # Both are read-only: selection never mutates them (fractional permission).
    Requires(Acc(list_pred(symbols), 1 / 2))
    Requires(Acc(list_pred(default_symbols), 1 / 2))
    # The polynomial's own generator count agrees with its default symbols.
    Requires(ngens == len(default_symbols))
    # pre-conditions-end
    # post-conditions-start
    # Inputs are preserved (read-only).
    Ensures(Acc(list_pred(symbols), 1 / 2))
    Ensures(Acc(list_pred(default_symbols), 1 / 2))
    Ensures(Acc(list_pred(Result())))
    # A value is produced ONLY when EITHER no symbols were supplied OR the
    # supplied count matches the number of generators.
    Ensures(len(symbols) == 0 or len(symbols) == ngens)
    # When the caller supplied a matching, non-empty sequence, the selected
    # sequence is EXACTLY that supplied sequence (element for element, in
    # order) — never the default symbols.
    Ensures(Implies(len(symbols) == ngens and len(symbols) > 0,
                    ToSeq(Result()) == ToSeq(symbols)))
    # When the caller supplied nothing, the selected sequence is the
    # polynomial's own default generator symbols.
    Ensures(Implies(len(symbols) == 0,
                    ToSeq(Result()) == ToSeq(default_symbols)))
    # The value error is raised on EXACTLY the rejected case: a non-empty
    # supplied sequence whose length does not match the number of generators.
    Exsures(SymbolCountError,
            Acc(list_pred(symbols), 1 / 2)
            and Acc(list_pred(default_symbols), 1 / 2)
            and len(symbols) > 0 and len(symbols) != ngens)
    # post-conditions-end
    # impl-start
    if len(symbols) > 0 and len(symbols) != ngens:
        raise SymbolCountError()
    else:
        # Pre-patch defect: the selected sequence is set to the default
        # generator symbols on EVERY non-rejected path, so a correctly-sized
        # supplied sequence is silently discarded.
        src = default_symbols  # type: List[int]
    # Materialise the selected sequence (a fresh carrier element-for-element
    # equal to `src`); the downstream builder reads this sequence.
    result = []  # type: List[int]
    i = 0
    n = len(src)
    while i < n:
        # invariants-start
        Invariant(Acc(list_pred(symbols), 1 / 2))
        Invariant(Acc(list_pred(default_symbols), 1 / 2))
        Invariant(Acc(list_pred(result)))
        Invariant(0 <= i and i <= n)
        Invariant(n == len(src))
        Invariant(len(symbols) == 0 or len(symbols) == ngens)
        Invariant(src is default_symbols)
        Invariant(ToSeq(result) == ToSeq(src).take(i))
        # invariants-end
        c = src[i]
        Assert(ToSeq(src).take(i + 1) == ToSeq(src).take(i) + PSeq(c))
        result = result + [c]
        i = i + 1
    Assert(ToSeq(src).take(n) == ToSeq(src))
    return result
    # impl-end
