"""Twin-artifact model for sympy__sympy-23534.

Behaviour under specification (stated as desired behaviour, not as an edit):

  The factory that turns names into symbol-like objects accepts a requested
  output class. When it is given a *container* of entries (rather than a single
  delimited name string), it processes each entry of the container in turn and
  returns the results *grouped per entry*, in the same order: the k-th group of
  the output is the expansion of the k-th input entry, and the number of groups
  equals the number of entries. The requested output class must be honoured for
  *every* produced object: the class chosen by the caller propagates unchanged
  into the processing of each contained entry. No produced object may silently
  fall back to the factory's default class.

Each entry of the container expands to zero or more objects (an entry may
expand to several objects, e.g. a range entry; an empty range to none). The
per-entry multiplicity is a property of the entry and is preserved in its
group. The observable property tested here is the CLASS of each produced object
together with the grouped shape; the textual content of a name is irrelevant to
it, so a name is abstracted to an opaque token carrying only its expansion
multiplicity, and the touched field of a produced object is modelled as an
integer *class tag*. The default class is the tag DEFAULT_CLS; a caller may
request any other tag.

`expand_entry` carries the per-entry processing (which is not what differs
here); `symbols_on_sequence` is the container-handling that must forward the
requested class into every entry and keep one group per entry.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List
from nagini_contracts.contracts import *


# axioms-start
# (no consumed axioms: the per-entry expansion is modelled deeply below)
# axioms-end


# pure-start
@Pure
def DEFAULT_CLS() -> int:
    """The factory's default output-class tag (used when no class is
    requested)."""
    return 0


@Pure
def all_tag(xs: PSeq[int], t: int) -> bool:
    """True iff every element of xs equals the class tag t. Front-recursive so
    a single unfold is available per concatenation step."""
    if len(xs) == 0:
        return True
    return xs[0] == t and all_tag(xs.drop(1), t)


@Pure
def all_nonneg(xs: PSeq[int]) -> bool:
    """True iff every element of xs is non-negative. Each entry token carries
    its expansion multiplicity (number of objects it produces), which is
    non-negative. Front-recursive."""
    if len(xs) == 0:
        return True
    return xs[0] >= 0 and all_nonneg(xs.drop(1))
# pure-end


def all_tag_concat(a: PSeq[int], b: PSeq[int], t: int) -> None:
    """Proof helper: all_tag distributes over concatenation (front fold)."""
    Requires(all_tag(a, t) and all_tag(b, t))
    Ensures(all_tag(a + b, t))
    if len(a) == 0:
        Assert(a + b == b)
    else:
        Assert((a + b).drop(1) == a.drop(1) + b)
        all_tag_concat(a.drop(1), b, t)


def nonneg_at(xs: PSeq[int], i: int) -> None:
    """Proof helper: extract the i-th element's non-negativity from all_nonneg
    (front fold)."""
    Requires(all_nonneg(xs))
    Requires(0 <= i and i < len(xs))
    Ensures(xs[i] >= 0)
    if i == 0:
        pass
    else:
        Assert(xs.drop(1)[i - 1] == xs[i])
        nonneg_at(xs.drop(1), i - 1)


def expand_entry(cls: int, n: int) -> List[int]:
    """Process a single container entry under the requested class `cls`,
    producing the `n` objects for that entry (its multiplicity). Every produced
    object carries class tag `cls` (the class the caller requested flows into
    the per-entry processing). Models the single-name branch of the factory,
    whose class handling the container path must preserve."""
    # pre-conditions-start
    Requires(n >= 0)
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(Result())))
    # The entry expands to exactly its multiplicity many objects (zero or more) ...
    Ensures(len(Result()) == n)
    # ... and every produced object carries exactly the requested class tag.
    Ensures(all_tag(ToSeq(Result()), cls))
    # post-conditions-end
    # impl-start
    out = []  # type: List[int]
    i = 0
    while i < n:
        # invariants-start
        Invariant(Acc(list_pred(out)))
        Invariant(0 <= i and i <= n)
        Invariant(len(out) == i)
        Invariant(all_tag(ToSeq(out), cls))
        # invariants-end
        old = ToSeq(out)
        out.append(cls)
        Assert(ToSeq(out) == old + PSeq(cls))
        all_tag_concat(old, PSeq(cls), cls)
        i = i + 1
    return out
    # impl-end


def symbols_on_sequence(names: List[int], cls: int) -> PSeq[PSeq[int]]:
    # pre-conditions-start
    # `names` is the read-only container of entries; the factory does not
    # mutate it. Each entry token carries its expansion multiplicity (>= 0).
    Requires(Acc(list_pred(names), 1 / 2))
    Requires(all_nonneg(ToSeq(names)))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(names), 1 / 2))
    # Exactly one group per container entry, in order (the grouped shape the
    # caller deconstructs by indexing into the per-entry groups).
    Ensures(len(Result()) == len(names))
    # For every entry: its group has exactly the entry's multiplicity of
    # objects, AND every object in that group carries the requested class tag
    # `cls` -- never the factory default. The class fact is the property the
    # F2P test observes; the per-group multiplicity is the grouped structure it
    # deconstructs.
    Ensures(Forall(int, lambda k: (Implies(0 <= k and k < len(Result()),
            len(Result()[k]) == names[k] and all_tag(Result()[k], cls)),
            [[Result()[k]]])))
    # post-conditions-end
    # impl-start
    res = PSeq()  # type: PSeq[PSeq[int]]
    i = 0
    while i < len(names):
        # invariants-start
        Invariant(Acc(list_pred(names), 1 / 2))
        Invariant(all_nonneg(ToSeq(names)))
        Invariant(0 <= i and i <= len(names))
        Invariant(len(res) == i)
        Invariant(Forall(int, lambda k: (Implies(0 <= k and k < len(res),
                len(res[k]) == names[k] and all_tag(res[k], cls)),
                [[res[k]]])))
        # invariants-end
        nonneg_at(ToSeq(names), i)
        sub = expand_entry(DEFAULT_CLS(), names[i])
        grp = ToSeq(sub)  # type: PSeq[int]
        old = res
        res = res + PSeq(grp)
        Assert(len(res) == i + 1)
        Assert(res[i] == grp)
        Assert(Forall(int, lambda k: (Implies(0 <= k and k < i, res[k] == old[k]), [[res[k]]])))
        i = i + 1
    return res
    # impl-end
