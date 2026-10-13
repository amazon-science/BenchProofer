"""Twin-artifact model for django__django-12262.

Behaviour under specification (stated as desired behaviour, not as an edit):

  A custom-tag argument binder consumes an ordered run of supplied keyword
  arguments, each identified by the name of the parameter it targets, and
  decides the outcome of the binding. The binder knows two static facts about
  the callable being bound:

    * the names of its positional parameters, and
    * the names of its keyword-only parameters

  and whether the callable also accepts arbitrary extra keyword arguments
  (a "catch-all" keyword parameter). A supplied keyword name is ACCEPTABLE iff
  it names one of the declared parameters -- positional OR keyword-only --
  REGARDLESS of whether that keyword-only parameter happens to carry a default
  value. (Whether a keyword-only parameter has a default governs only whether it
  is still *required*; it never makes an explicitly-supplied value for that
  parameter unacceptable.)

  Walking the supplied keywords front to back, the FIRST one that is problematic
  determines the outcome:

    * outcome UNEXPECTED -- the keyword names no declared parameter and the
      callable has no catch-all keyword parameter;
    * outcome DUPLICATE -- the keyword names a parameter for which a value has
      already been supplied earlier in the run (it is supplied a second time);
    * otherwise outcome OK -- every supplied keyword was acceptable and supplied
      at most once.

  The two problematic outcomes are distinct and must not be confused: supplying
  an acceptable keyword twice is a DUPLICATE, never an UNEXPECTED keyword.

  Binding is a bounded front-to-back scan of the supplied run: the binder MUST
  actually ANSWER with an outcome (a total-correctness obligation, carried as
  MustTerminate in the precondition). Nagini is a partial-correctness verifier
  by default, so without this obligation a diverging implementation (e.g.
  `while True: pass` inserted before the scan) would satisfy the value
  postcondition vacuously; the real binder always delivers its decision.

Parameter names are modelled as integer codes; the supplied-keyword run is a
`List[int]` of those codes. The declared positional and keyword-only parameter
name sets are `PSeq[int]`; the subset of keyword-only names that carry a default
value is also given (`keyword_only_with_default`, a sub-collection of the
keyword-only names); the catch-all flag is a bool. The outcome is the integer
code 0 (OK), 1 (UNEXPECTED), or 2 (DUPLICATE). The decision is pure membership/
duplication logic over the inputs, modelled deeply as a front-recursive fold;
no callee is axiomatized.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List
from nagini_contracts.contracts import *
from nagini_contracts.obligations import MustTerminate


# axioms-start
# (no axiomatized callees: the binding decision is membership/duplication logic
# over the supplied-keyword run and the declared parameter-name sets, all
# modelled deeply below. The extraction of an individual keyword from a token
# and the compilation of its value are unchanged, independent of this decision,
# and unobserved by the behaviour pinned here.)
# axioms-end


# pure-start
@Pure
def contains(s: PSeq[int], x: int) -> bool:
    """True iff name code `x` occurs in sequence `s`. Front-recursive so a
    single unfold is available per fold/loop step."""
    if len(s) == 0:
        return False
    return s[0] == x or contains(s.drop(1), x)


@Pure
def acceptable(positional: PSeq[int], keyword_only: PSeq[int],
               catch_all: bool, name: int) -> bool:
    """A supplied keyword `name` is acceptable iff it names a declared
    parameter -- positional OR keyword-only -- or the callable has a catch-all
    keyword parameter. Membership in `keyword_only` is the full set of
    keyword-only names, independent of which of them carry defaults."""
    return catch_all or contains(positional, name) or contains(keyword_only, name)


@Pure
def outcome(supplied: PSeq[int], seen: PSeq[int],
            positional: PSeq[int], keyword_only: PSeq[int],
            catch_all: bool) -> int:
    """Outcome of binding the supplied-keyword run `supplied`, given the names
    `seen` already bound earlier in the run. Front-recursive (one unfold per
    supplied keyword) so a forward impl loop can discharge it. Returns 0 (OK),
    1 (UNEXPECTED), or 2 (DUPLICATE) -- the FIRST problematic keyword wins."""
    if len(supplied) == 0:
        return 0
    name = supplied[0]
    if not acceptable(positional, keyword_only, catch_all, name):
        return 1
    if contains(seen, name):
        return 2
    return outcome(supplied.drop(1), seen + PSeq(name),
                   positional, keyword_only, catch_all)
# pure-end


def bind_keywords(supplied: List[int], positional: PSeq[int],
                  keyword_only: PSeq[int], keyword_only_with_default: PSeq[int],
                  catch_all: bool) -> int:
    # pre-conditions-start
    # The supplied-keyword run is read-only (the binder inspects it, it does not
    # mutate it): required AND ensured at fractional permission (directive 5).
    # `positional` / `keyword_only` / `keyword_only_with_default` are pure
    # sequence values (the declared parameter-name sets); `catch_all` is a plain
    # bool. Well-formedness: every keyword-only name that carries a default is
    # itself a keyword-only name (defaults are a sub-collection of the keyword-
    # only parameters), which holds for every real callable.
    Requires(Acc(list_pred(supplied), 1 / 2))
    Requires(Forall(int, lambda k: (Implies(
        0 <= k and k < len(keyword_only_with_default),
        contains(keyword_only, keyword_only_with_default[k])))))
    # TERMINATION: the binder must actually ANSWER — deciding the outcome of a
    # finite supplied-keyword run is a bounded computation (one step per
    # keyword). Nagini is a partial-correctness verifier by default, so without
    # this obligation a non-terminating implementation (e.g. an endless loop
    # before returning) satisfies the value postcondition vacuously; the real
    # binder always returns or raises its decision.
    Requires(MustTerminate(2))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(supplied), 1 / 2))
    # The returned outcome is exactly the front-to-back binding decision: 0 OK,
    # 1 UNEXPECTED (an unacceptable keyword), 2 DUPLICATE (an acceptable keyword
    # supplied twice); the first problematic keyword determines it. Starting
    # from no keyword bound (empty `seen`). This pins the discriminating
    # behaviour: an acceptable keyword carrying a default is NOT unexpected, and
    # a repeated acceptable keyword is a DUPLICATE rather than UNEXPECTED.
    Ensures(Result() == outcome(ToSeq(supplied), PSeq(0).take(0),
                                positional, keyword_only, catch_all))
    # post-conditions-end
    # impl-start
    seen = PSeq(0).take(0)  # type: PSeq[int]
    i = 0
    while i < len(supplied):
        # invariants-start
        Invariant(Acc(list_pred(supplied), 1 / 2))
        Invariant(0 <= i and i <= len(supplied))
        Invariant(seen == ToSeq(supplied).take(i))
        # The remaining computation from index `i` with the keywords bound so
        # far equals the total outcome (no problematic keyword has been seen yet
        # in indices < i, else the loop would have returned).
        Invariant(outcome(ToSeq(supplied), PSeq(0).take(0),
                          positional, keyword_only, catch_all) ==
                  outcome(ToSeq(supplied).drop(i), seen,
                          positional, keyword_only, catch_all))
        # the scan consumes the caller's termination obligation with a
        # strictly decreasing, bounded-below measure (len(supplied) - i),
        # discharging MustTerminate(2) from the precondition.
        Invariant(MustTerminate(len(supplied) - i + 1))
        # invariants-end
        name = supplied[i]
        Assert(ToSeq(supplied).drop(i)[0] == name)
        Assert(ToSeq(supplied).drop(i).drop(1) == ToSeq(supplied).drop(i + 1))
        Assert(ToSeq(supplied).take(i + 1) == seen + PSeq(name))
        if not acceptable(positional, keyword_only, catch_all, name):
            return 1
        if contains(seen, name):
            return 2
        seen = seen + PSeq(name)
        i = i + 1
    return 0
    # impl-end
