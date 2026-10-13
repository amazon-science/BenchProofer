"""Twin-artifact model for sphinx-doc__sphinx-8721.

Behaviour under specification (stated as desired behaviour, not as an edit):

  When the documentation-source collector assembles the set of highlighted
  module-source pages for an output target, it must respect the kind of output
  target being produced, identified by the target's name (a sequence of Unicode
  code points), together with a boolean preference that decides whether module
  pages are wanted for electronic-book output:

    (1) For an ELECTRONIC-BOOK target (any name beginning with the code-point
        sequence `epub`) the per-module source pages are produced ONLY when the
        electronic-book preference is enabled; with the preference disabled
        (its default) no module pages are produced.

    (2) For every other target the per-module source pages are produced as
        before: one page for each module that has a recorded source entry, in
        the order the modules are presented.

  The decisive content: with the electronic-book preference disabled, an
  electronic-book target yields NO module pages (the collector returns an empty
  set of pages) — module pages are not emitted into electronic-book output by
  default.

Target names are modelled as `List[int]` of Unicode code points (Nagini bans
`str` indexing); the specification is carried over `PSeq[int]`. The begins-with
decision is modelled DEEPLY (a spelled-out fold), validated == the real
`str.startswith` out-of-band by axiom_check.py (G-AX), never consumed as an
axiom. The collection of recorded module entries enters as an ordinary list
value.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List
from nagini_contracts.contracts import *
from nagini_contracts.obligations import MustTerminate


# axioms-start
# (No consumed axioms. The electronic-book name decision — the `epub`-prefix
#  test — is modelled DEEPLY below (`prefix_eq`) and validated == the real
#  `str.startswith` by axiom_check.py / G-AX, never consumed. The
#  electronic-book preference and the recorded module entries are plain input
#  values, not axioms.)
# axioms-end


# pure-start
@Pure
def prefix_eq(s: PSeq[int], lit: PSeq[int]) -> bool:
    """The first `len(lit)` code points of `s` equal `lit` code point for code
    point — a LITERAL prefix match (begins-with). Total: if `s` is shorter than
    `lit` no such match exists, so the result is False. Front-recursive (over
    both sequences) so a single unfold is available per loop step."""
    if len(lit) == 0:
        return True
    if len(s) == 0:
        return False
    return s[0] == lit[0] and prefix_eq(s.drop(1), lit.drop(1))


@Pure
def lemma_prefix_too_long(s: PSeq[int], lit: PSeq[int]) -> bool:
    """If `lit` is strictly longer than `s`, no literal prefix match exists.
    Proven by front-recursion on `s`."""
    Requires(len(lit) > len(s))
    Ensures(Result())
    Ensures(not prefix_eq(s, lit))
    if len(s) == 0:
        return True
    return lemma_prefix_too_long(s.drop(1), lit.drop(1))


@Pure
def lit_epub() -> PSeq[int]:
    # 'epub'
    return PSeq(101, 112, 117, 98)


@Pure
def suppressed(name: PSeq[int], enable_epub: bool) -> bool:
    """The collector produces NO module pages for the target named `name` under
    electronic-book preference `enable_epub` iff `name` begins with `epub` and
    the electronic-book preference is off. Every other target is unsuppressed
    (module pages produced as before)."""
    return prefix_eq(name, lit_epub()) and not enable_epub
# pure-end


def begins_with(name: List[int], lit: List[int]) -> bool:
    # pre-conditions-start
    Requires(Acc(list_pred(name), 1 / 4))
    Requires(Acc(list_pred(lit), 1 / 4))
    Requires(MustTerminate(2))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(name), 1 / 4))
    Ensures(Acc(list_pred(lit), 1 / 4))
    # Result is the LITERAL prefix (begins-with) match of `lit` against `name`.
    Ensures(Result() == prefix_eq(ToSeq(name), ToSeq(lit)))
    # post-conditions-end
    # impl-start
    n = len(lit)
    if n > len(name):
        Assert(lemma_prefix_too_long(ToSeq(name), ToSeq(lit)))
        return False
    ok = True
    i = n
    while i > 0:
        # invariants-start
        Invariant(Acc(list_pred(name), 1 / 4))
        Invariant(Acc(list_pred(lit), 1 / 4))
        Invariant(0 <= i and i <= n and n == len(lit))
        Invariant(n <= len(name))
        Invariant(len(ToSeq(lit).drop(i)) <= len(ToSeq(name).drop(i)))
        Invariant(ok == prefix_eq(ToSeq(name).drop(i), ToSeq(lit).drop(i)))
        Invariant(MustTerminate(i + 1))
        # invariants-end
        Assert(ToSeq(name).drop(i - 1)[0] == ToSeq(name)[i - 1])
        Assert(ToSeq(lit).drop(i - 1)[0] == ToSeq(lit)[i - 1])
        Assert(ToSeq(name).drop(i - 1).drop(1) == ToSeq(name).drop(i))
        Assert(ToSeq(lit).drop(i - 1).drop(1) == ToSeq(lit).drop(i))
        if name[i - 1] != lit[i - 1]:
            ok = False
        i = i - 1
    Assert(ToSeq(name).drop(0) == ToSeq(name))
    Assert(ToSeq(lit).drop(0) == ToSeq(lit))
    return ok
    # impl-end


def module_source_pages(name: List[int], enable_epub: bool,
                        modules: List[int]) -> List[int]:
    # pre-conditions-start
    # `name` (the output-target name) and `modules` (the recorded per-module
    # source entries, one element per module that has a page) are read-only.
    Requires(Acc(list_pred(name), 1 / 2))
    Requires(Acc(list_pred(modules), 1 / 2))
    Requires(MustTerminate(3))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(name), 1 / 2))
    Ensures(Acc(list_pred(modules), 1 / 2))
    Ensures(Acc(list_pred(Result())))
    # A suppressed target (an electronic-book target with the preference off)
    # yields NO module pages — the produced page set is empty.
    Ensures(Implies(suppressed(ToSeq(name), enable_epub), len(Result()) == 0))
    # Every other target produces exactly one page per recorded module entry,
    # in the order the modules are presented.
    Ensures(Implies(not suppressed(ToSeq(name), enable_epub),
                    ToSeq(Result()) == ToSeq(modules)))
    # post-conditions-end
    # impl-start
    empty = []  # type: List[int]
    ep = [101, 112, 117, 98]  # type: List[int]
    Assert(ToSeq(ep) == lit_epub())
    if begins_with(name, ep) and not enable_epub:
        Assert(prefix_eq(ToSeq(name), lit_epub()) and not enable_epub)
        Assert(suppressed(ToSeq(name), enable_epub))
        return empty
    # The guard did not fire: the target is not suppressed.
    Assert(not (prefix_eq(ToSeq(name), lit_epub()) and not enable_epub))
    Assert(not suppressed(ToSeq(name), enable_epub))
    result = []  # type: List[int]
    i = 0
    n = len(modules)
    while i < n:
        # invariants-start
        Invariant(Acc(list_pred(modules), 1 / 2))
        Invariant(Acc(list_pred(result)))
        Invariant(0 <= i and i <= n and n == len(modules))
        Invariant(ToSeq(result) == ToSeq(modules).take(i))
        Invariant(MustTerminate(n - i + 1))
        # invariants-end
        Assert(ToSeq(modules).take(i + 1).drop(i)[0] == ToSeq(modules)[i])
        Assert(ToSeq(modules).take(i) + PSeq(ToSeq(modules)[i])
               == ToSeq(modules).take(i + 1))
        result = result + [modules[i]]
        i = i + 1
    Assert(ToSeq(modules).take(n) == ToSeq(modules))
    return result
    # impl-end
