"""Twin-artifact model for sphinx-doc__sphinx-9258.

Behaviour under specification (stated as desired behaviour, not as an edit):

  A type specification written for a parameter/attribute/variable is a single
  text string naming one or more types. When several alternative types are
  offered, they are written with a separating token between them, and each
  individual type name must be turned into its OWN cross-reference so that every
  named type links independently; the separating token itself is rendered as
  plain literal text, never as a cross-reference.

  In particular, when the separating token is the vertical bar with the usual
  surrounding spaces (" | "), a specification of the form

      <name-1> | <name-2> | ... | <name-k>

  must produce, in order, the cross-reference for <name-1>, then the literal
  separator, then the cross-reference for <name-2>, the literal separator, and
  so on — k cross-references interleaved with k-1 literal separators. Each
  cross-reference carries exactly the corresponding type name (with the padding
  whitespace stripped); each literal separator carries the separator text
  exactly as written. A specification naming a single type (no separator) yields
  exactly one cross-reference carrying that whole name.

  The defect this specification forbids is treating such a bar-separated
  specification as one indivisible name: that would emit a single, useless
  cross-reference for the entire string rather than one per type.

The type specification is modelled as a ``List[int]`` of Unicode code points
(Nagini bans ``str`` indexing); the bar separator is the code point 124 ('|')
optionally padded by whitespace (``is_space``, the full Unicode whitespace set,
not merely the ASCII space 32).

The ordered output is modelled TWICE, at two strengths.

  * ``render_nodes`` (the primary obligation) pins the WHOLE node stream over
    EVERY specification, with no domain restriction: how many nodes there are,
    the kind of each one, and the exact code points each one carries. Its
    postcondition is a single sequence equality against the pure ``rendered``
    fold, which lays the nodes out as `<carried code points> <kind marker>` per
    node (-1 cross-reference, -2 literal separator) and closes with -3. Since
    code points are non-negative, no marker can be confused with carried text, so
    that one equality determines the node list uniquely — payload included. The
    separator vocabulary it tokenises against is ``sep_end``: the padded bar, the
    bracket/comma tokens with their optional ``or``, the whitespace-bounded word
    ``or``, and the three-dot run, tried in that order.

  * ``split_render`` (retained) pins the node *kinds* alone — a ``List[bool]``
    whose k-th entry is True iff the k-th node is a cross-reference — via the pure
    ``marks`` fold, which is the kind projection of ``rendered``: same node
    stream, kinds read and carried text ignored. It is stated over EVERY
    specification too, with no domain restriction, so the number of nodes and the
    alternation of cross-reference and literal separator are pinned for the full
    separator vocabulary and not merely for a bar-only shape. It is strictly
    weaker than ``render_nodes`` and is kept because a kind sequence is the most
    direct statement of one link per named type.

Both are verified producing implementations, and neither carries a domain
restriction: no obligation below is conditioned on the shape of the
specification. The bar-structure reading (``kinds`` over ``first_bar``, with its
well-formedness predicate ``well_formed`` and the trimmed-segment helpers
``seg_text``/``strip_left``/``strip_right``) is kept in the pure region as an
auxiliary description of the same behaviour on the bar-only shape, and is
checked out-of-band; it is not the obligation of either function.

No callee is axiomatized: the desired behaviour is modelled deeply by the pure
folds and the verified implementation, whose equality to the real behaviour is
checked out-of-band by axiom_check.py (G-AX), not consumed as an axiom.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List
from nagini_contracts.contracts import *
from nagini_contracts.obligations import MustTerminate


# axioms-start
# (No consumed @ContractOnly axioms. The desired behaviour — a bar-separated
#  specification becomes one cross-reference per named type, interleaved with
#  literal separators — is modelled DEEPLY by the pure folds and the verified
#  `split_render` impl. The deep model is validated == the real behaviour
#  out-of-band by axiom_check.py / G-AX as an A-reference.)
# axioms-end


# pure-start
@Pure
def is_space(c: int) -> bool:
    """`c` is a whitespace code point. Whitespace is what pads a separator and
    what gets stripped from a type name, and it is NOT just the ASCII space:
    the full set is TAB..CR (9-13), the information separators (28-31), the
    ASCII space (32), NEL (133), NBSP (160), OGHAM SPACE MARK (5760), the
    EN/EM-quad..HAIR SPACE run (8192-8202), LINE/PARAGRAPH SEPARATOR (8232,
    8233), NARROW NBSP (8239), MEDIUM MATHEMATICAL SPACE (8287) and
    IDEOGRAPHIC SPACE (12288). Modelling only code point 32 would make the
    padding/trimming and the separator-word recognition below disagree with the
    real behaviour on every specification padded by any other whitespace."""
    return ((9 <= c and c <= 13) or (28 <= c and c <= 32) or c == 133 or
            c == 160 or c == 5760 or (8192 <= c and c <= 8202) or
            c == 8232 or c == 8233 or c == 8239 or c == 8287 or c == 12288)


@Pure
def first_bar(s: PSeq[int], i: int) -> int:
    """Index of the first bar ('|', code point 124) at or after `i`, clamped to
    `len(s)` when there is none (total in `i` so callers carry no upper-bound
    well-definedness obligation). Front-recursive: one auto-unfold per step."""
    Requires(0 <= i)
    Ensures(Result() >= i)
    Ensures(Implies(i <= len(s), Result() <= len(s)))
    Ensures(Implies(i <= len(s), Forall(int, lambda k:
                    (Implies(i <= k and k < Result(), s[k] != 124), [[s[k]]]))))
    Ensures(Implies(Result() < len(s), s[Result()] == 124))
    if i >= len(s):
        return i
    if s[i] == 124:
        return i
    return first_bar(s, i + 1)


@Pure
def kinds(s: PSeq[int], i: int) -> PSeq[bool]:
    """Rendered-node kinds for the suffix s[i:], in order: True (a cross-
    reference) for the current bar-separated segment, then — if a bar follows —
    False (the literal separator) and the kinds of the rest after that bar.
    Front-recursive so a single unfold is available per loop step; with b bars
    in the suffix it has length 2*b + 1, alternating True, False, True, ..."""
    Requires(0 <= i)
    Ensures(len(Result()) >= 1)
    Ensures(len(Result()) % 2 == 1)
    Ensures(Result()[0])
    if first_bar(s, i) >= len(s):
        return PSeq(True)
    return PSeq(True) + (PSeq(False) + kinds(s, first_bar(s, i) + 1))


@Pure
def strip_left(s: PSeq[int], i: int, j: int) -> int:
    """First index in [i, j) whose code point is not whitespace, or j if all are
    whitespace. Total in `i, j`; front-recursive in `i`."""
    Requires(0 <= i and i <= j)
    Ensures(i <= Result() and Result() <= j)
    if i >= j:
        return i
    if i >= len(s):
        return i
    if not is_space(s[i]):
        return i
    return strip_left(s, i + 1, j)


@Pure
def strip_right(s: PSeq[int], i: int, j: int) -> int:
    """One past the last non-whitespace index in [i, j), i.e. the upper bound
    after trimming trailing whitespace; equals i if [i, j) is all whitespace.
    Total; front-recursive in `j`."""
    Requires(0 <= i and i <= j)
    Ensures(i <= Result() and Result() <= j)
    if i >= j:
        return j
    if j - 1 >= len(s):
        return j
    if not is_space(s[j - 1]):
        return j
    return strip_right(s, i, j - 1)


@Pure
def seg_text(s: PSeq[int], i: int, j: int) -> PSeq[int]:
    """The trimmed type-name in the segment [i, j): the slice with leading and
    trailing whitespace removed. The Ensures exposes the definition so callers
    can discharge equality without nested-application congruence."""
    Requires(0 <= i and i <= j)
    Ensures(Result() == s.take(strip_right(s, strip_left(s, i, j), j)).drop(
        strip_left(s, i, j)))
    a = strip_left(s, i, j)
    b = strip_right(s, a, j)
    return s.take(b).drop(a)


@Pure
def no_other_sep(s: PSeq[int], i: int) -> bool:
    """The suffix s[i:] contains NONE of the non-bar separator triggers, so the
    vertical bar is the ONLY token that acts as a separator. Forbidden, position
    by position: any of the bracket/comma characters ``[ ] ( ) ,`` (code points
    91, 93, 40, 41, 44); a run of three dots ``...`` (a space-or-trailing
    ellipsis token, code point 46); and the whitespace-bounded word ``or``
    ('o'=111, 'r'=114 with whitespace on BOTH sides — whitespace per `is_space`,
    i.e. any whitespace code point and not merely the ASCII space, since the
    word acts as a separator however it is padded). Within a suffix free of all
    of these, the only segment boundary is the bar, so the bar-structure split
    is an exact, strictly-alternating tokenisation. Total in `i`;
    front-recursive."""
    Requires(0 <= i)
    if i >= len(s):
        return True
    if s[i] == 91 or s[i] == 93 or s[i] == 40 or s[i] == 41 or s[i] == 44:
        return False
    if s[i] == 46 and i + 2 < len(s) and s[i + 1] == 46 and s[i + 2] == 46:
        return False
    if (is_space(s[i]) and i + 3 < len(s) and s[i + 1] == 111 and
            s[i + 2] == 114 and is_space(s[i + 3])):
        return False
    return no_other_sep(s, i + 1)


@Pure
def well_formed(s: PSeq[int], i: int) -> bool:
    """The suffix s[i:] is a well-formed alternative-type specification on which
    the bar-structure split is exact: (a) every bar-separated segment names a
    non-empty type (has a non-whitespace character), AND (b) the suffix contains
    none of the other separator triggers (`no_other_sep`), so the vertical bar is
    the only delimiter. It characterises the shape — the realistic union-type
    field, e.g. ``int | str`` — on which the bar split coincides with the full
    tokenisation, strictly alternating. Specifications that also exercise the
    bracket/comma/ellipsis/`or` separators (e.g. ``List[int]``, ``Dict[str,
    str]``, ``str or int``) do NOT satisfy it, and neither does a specification
    with a segment made of nothing but whitespace (e.g. a bar with nothing but
    padding beside it), since the padding then belongs to the separator and names
    no type. This is a description only: NO obligation in this model is
    restricted to it, so the behaviour on every other shape is pinned just the
    same, by `rendered` and by `marks`. Front-recursive."""
    Requires(0 <= i)
    if not no_other_sep(s, i):
        return False
    if len(seg_text(s, i, first_bar(s, i))) == 0:
        return False
    if first_bar(s, i) >= len(s):
        return True
    return well_formed(s, first_bar(s, i) + 1)


@Pure
def sep_end(s: PSeq[int], i: int) -> int:
    """One past the end of the separator token that STARTS at index `i`, or -1
    when no separator starts there.

    A separator is one of four tokens, tried at `i` in this order — the first one
    that applies determines the token's extent, so the order is part of the
    model:

      1. optional padding whitespace, then one of the bracket/comma characters
         ``[ ] ( ) ,`` (code points 91, 93, 40, 41, 44), then optionally the word
         ``or`` (111, 114) preceded by optional padding and followed by exactly
         one whitespace, then any further padding whitespace;
      2. at least one whitespace, the word ``or``, at least one whitespace;
      3. optional padding whitespace, the vertical bar (124), optional padding
         whitespace;
      4. the three-dot run ``...`` (46, 46, 46), with no padding.

    Whitespace is `is_space` throughout — the full whitespace set, not merely
    code point 32 — so a separator is recognised however it is padded. Total in
    `i`; the recursion is `strip_left`'s.

    Each result is returned through `+ 0` so that it is known to be a plain
    integer. Python's ``bool`` is a subtype of ``int``, so a value known only to
    be an ``int`` is not yet known to be a number rather than a truth value, and
    two indices that agree as numbers are interchangeable inside the folds below
    only once they are known to be numbers."""
    Requires(0 <= i and i <= len(s))
    Ensures(Result() == -1 or (i < Result() and Result() <= len(s)))
    a = strip_left(s, i, len(s))
    if a < len(s) and (s[a] == 91 or s[a] == 93 or s[a] == 40 or s[a] == 41 or
                       s[a] == 44):
        c = strip_left(s, a + 1, len(s))
        if (c + 2 < len(s) and s[c] == 111 and s[c + 1] == 114 and
                is_space(s[c + 2])):
            return strip_left(s, c + 3, len(s)) + 0
        return strip_left(s, a + 1, len(s)) + 0
    if (i < len(s) and is_space(s[i]) and a + 2 < len(s) and s[a] == 111 and
            s[a + 1] == 114 and is_space(s[a + 2])):
        return strip_left(s, a + 2, len(s)) + 0
    if a < len(s) and s[a] == 124:
        return strip_left(s, a + 1, len(s)) + 0
    if i + 2 < len(s) and s[i] == 46 and s[i + 1] == 46 and s[i + 2] == 46:
        return i + 3
    return -1


@Pure
def next_sep(s: PSeq[int], i: int) -> int:
    """The position of the LEFTMOST separator token at or after `i`, clamped to
    `len(s)` when the suffix holds none. Everything strictly between `i` and this
    position is type-name text: no separator starts anywhere in it. Total in `i`;
    front-recursive, and its result is likewise read as a plain integer."""
    Requires(0 <= i and i <= len(s))
    Ensures(i <= Result() and Result() <= len(s))
    Ensures(Implies(Result() < len(s), sep_end(s, Result()) > Result()))
    if i >= len(s):
        return i + 0
    if sep_end(s, i) >= 0:
        return i + 0
    return next_sep(s, i + 1)


@Pure
def rendered(s: PSeq[int], i: int) -> PSeq[int]:
    """The ORDERED RENDERED-NODE STREAM for the suffix s[i:]: every node, in
    order, with the exact code points it carries and its kind.

    Encoding — for each node, the code points that node carries, then a marker
    naming its kind: -1 for a cross-reference, -2 for a literal separator. The
    stream is closed by -3. Code points are non-negative, so no marker can be
    confused with carried text, and the stream therefore determines the node list
    exactly: the number of nodes, each node's kind, and the exact text of each
    node.

    Definition, at a position `i` where a node may start: let j be the leftmost
    separator position (`next_sep`) and e its end (`sep_end`).
      * no separator remains (j == len(s)): if any text remains it is one final
        cross-reference carrying s[i:]; otherwise no node remains;
      * a separator starts later than `i` (j > i): the text s[i:j] is one
        cross-reference, s[j:e] is one literal separator, and the rest follows
        from e;
      * a separator starts right at `i` (j == i): s[i:e] is one literal
        separator and the rest follows from e — no empty cross-reference is
        emitted for the absent text before it.

    So each cross-reference carries the specification's own characters between
    two separators VERBATIM, padding included, and each literal separator carries
    the separator token's own characters, padding included. Nothing is trimmed,
    normalised or dropped, and a node is emitted for a stretch of text only when
    that stretch is non-empty. This is stated for EVERY specification, with no
    domain restriction: the four separator tokens of `sep_end` are all recognised,
    so a specification that mixes the vertical bar with brackets, commas, `or` or
    an ellipsis is covered too."""
    Requires(0 <= i and i <= len(s))
    Ensures(len(Result()) >= 1)
    Ensures(Result()[len(Result()) - 1] == -3)
    if next_sep(s, i) >= len(s):
        if i < len(s):
            return (s.take(len(s)).drop(i) + PSeq(-1)) + PSeq(-3)
        return PSeq(-3)
    if next_sep(s, i) > i:
        return ((s.take(next_sep(s, i)).drop(i) + PSeq(-1)) +
                (s.take(sep_end(s, next_sep(s, i))).drop(next_sep(s, i)) +
                 PSeq(-2))) + rendered(s, sep_end(s, next_sep(s, i)))
    return (s.take(sep_end(s, next_sep(s, i))).drop(i) + PSeq(-2)) + \
        rendered(s, sep_end(s, next_sep(s, i)))


@Pure
def marks(s: PSeq[int], i: int) -> PSeq[bool]:
    """The KIND of every rendered node for the suffix s[i:], in order: True for a
    cross-reference, False for a literal separator. The same case analysis as
    `rendered`, reading only the kinds and none of the carried text, so it is the
    kind projection of that node stream. Stated for EVERY specification, with no
    domain restriction: all four separator tokens of `sep_end` are recognised, so
    a specification that mixes the vertical bar with a bracket, comma, `or` or an
    ellipsis is covered as well. The empty sequence is written `PSeq(True).drop(1)`
    because it arises only for a specification with nothing left to render."""
    Requires(0 <= i and i <= len(s))
    if next_sep(s, i) >= len(s):
        if i < len(s):
            return PSeq(True)
        return PSeq(True).drop(1)
    if next_sep(s, i) > i:
        return (PSeq(True) + PSeq(False)) + marks(s, sep_end(s, next_sep(s, i)))
    return PSeq(False) + marks(s, sep_end(s, next_sep(s, i)))
# pure-end


def split_render(target: List[int]) -> List[bool]:
    # pre-conditions-start
    # The type specification is read-only (directive 5: fractional permission).
    Requires(Acc(list_pred(target), 1 / 2))
    # NO domain restriction. Every specification is claimed, including the ones
    # that mix the vertical bar with a bracket, comma, `or` or ellipsis
    # separator: whatever the separators are, the kind sequence below is the one
    # required. Narrowing this to a bar-only shape would leave the kinds on every
    # other shape unstated and therefore free.
    # The rendering must COMPLETE (total correctness): without this obligation
    # every Ensures below is claimed only of runs that reach the return, so an
    # implementation that never gets there satisfies the whole postcondition
    # vacuously. Level 5 is strictly above every callee it invokes (next_sep_idx
    # at 4, sep_end_idx at 3).
    Requires(MustTerminate(5))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(target), 1 / 2))
    Ensures(Acc(list_pred(Result())))
    # The rendered-node kind sequence is exactly the kind projection of the node
    # stream: one cross-reference per stretch of type-name text, one literal
    # separator per separator token, in order (xref, separator, xref, ...) for a
    # specification that starts with a type name. This pins both the NUMBER of
    # nodes and that each separator is a literal (False), never a cross-reference
    # — so a bar-separated spec is split into one link per type — and it pins them
    # for EVERY specification, the ones using the other separator tokens too.
    Ensures(ToSeq(Result()) == marks(ToSeq(target), 0))
    # post-conditions-end
    # impl-start
    result = []  # type: List[bool]
    n = len(target)
    i = 0
    while True:
        # invariants-start
        Invariant(Acc(list_pred(target), 1 / 2))
        Invariant(Acc(list_pred(result)))
        Invariant(0 <= i and i <= n)
        Invariant(n == len(target))
        Invariant(n == len(ToSeq(target)))
        # telescoping fold: what is emitted, concatenated with the kinds of the
        # remaining suffix, is the whole kind sequence.
        Invariant(ToSeq(result) + marks(ToSeq(target), i) ==
                  marks(ToSeq(target), 0))
        # The condition is the constant `True`, so the bound comes from what the
        # break counts down: the loop leaves via `break` as soon as no separator
        # remains at or after i, and otherwise resumes at i = e, the end of a
        # separator that starts at j >= i and ends strictly after it (sep_end's
        # postcondition), so the scan index rises by at least one per pass and at
        # most n - i + 1 passes remain. It strictly decreases because only i
        # changes (n is a local fixed before the loop, pinned by
        # Invariant(n == len(target))), and it stays >= 1 because
        # Invariant(0 <= i and i <= n) holds on entry to every pass (so it never
        # reaches the unsatisfiable 0); the pass on which no separator remains is
        # the one that breaks.
        Invariant(MustTerminate(n - i + 1))
        # invariants-end
        # `+ 0` reads the boundary as the plain integer it is; see `sep_end`.
        j = next_sep_idx(target, i) + 0
        if j >= n:
            if i < n:
                Assert(marks(ToSeq(target), i) == PSeq(True))
                # the trailing text is one cross-reference.
                result.append(True)
            else:
                Assert(marks(ToSeq(target), i) == PSeq(True).drop(1))
            break
        e = sep_end_idx(target, j) + 0
        Assert(j < e and e <= n)
        if j > i:
            Assert(marks(ToSeq(target), i) ==
                   (PSeq(True) + PSeq(False)) + marks(ToSeq(target), e))
            # the text before the separator is one cross-reference.
            result.append(True)
        else:
            Assert(marks(ToSeq(target), i) ==
                   PSeq(False) + marks(ToSeq(target), e))
        # the separator itself is one literal node.
        result.append(False)
        i = e
    return result
    # impl-end


def first_bar_idx(s: List[int], i: int) -> int:
    # pre-conditions-start
    Requires(Acc(list_pred(s), 1 / 2))
    Requires(0 <= i and i <= len(s))
    # Locating the next separator must COMPLETE: level 2 sits strictly below its
    # caller's 3 and leaves room below itself for the obligations of the built-in
    # operations it performs.
    Requires(MustTerminate(2))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(s), 1 / 2))
    Ensures(ToSeq(s) == Old(ToSeq(s)))
    Ensures(i <= Result() and Result() <= len(s))
    Ensures(Result() == first_bar(ToSeq(s), i))
    # post-conditions-end
    # impl-start
    k = i
    while k < len(s):
        # invariants-start
        Invariant(Acc(list_pred(s), 1 / 2))
        Invariant(ToSeq(s) == Old(ToSeq(s)))
        Invariant(i <= k and k <= len(s))
        Invariant(first_bar(ToSeq(s), i) == first_bar(ToSeq(s), k))
        # At most len(s) - k + 1 passes remain: the sequence is held read-only by
        # the invariant above so its length cannot change, and k rises by exactly
        # one per pass, so the bound strictly decreases; the guard k < len(s) keeps
        # it >= 2 on entry to a pass (so it never reaches the unsatisfiable 0).
        Invariant(MustTerminate(len(s) - k + 1))
        # invariants-end
        if s[k] == 124:
            Assert(first_bar(ToSeq(s), k) == k)
            return k
        k = k + 1
    Assert(first_bar(ToSeq(s), k) == k)
    return k
    # impl-end


def slice_trim(s: List[int], i: int, j: int) -> List[int]:
    # pre-conditions-start
    Requires(Acc(list_pred(s), 1 / 2))
    Requires(0 <= i and i <= j and j <= len(s))
    # Trimming the segment must COMPLETE: level 2 sits strictly below its caller's
    # 3 and leaves room for the list allocation it performs (at level 1 the
    # allocation's own obligation has nowhere below the caller to go).
    Requires(MustTerminate(2))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(s), 1 / 2))
    Ensures(ToSeq(s) == Old(ToSeq(s)))
    Ensures(Acc(list_pred(Result())))
    Ensures(ToSeq(Result()) == seg_text(ToSeq(s), i, j))
    # post-conditions-end
    # impl-start
    a = i
    while a < j and is_space(s[a]):
        # invariants-start
        Invariant(Acc(list_pred(s), 1 / 2))
        Invariant(ToSeq(s) == Old(ToSeq(s)))
        Invariant(i <= a and a <= j and j <= len(s))
        Invariant(strip_left(ToSeq(s), i, j) == strip_left(ToSeq(s), a, j))
        # At most j - a + 1 passes remain: the compound guard terminates on the
        # counter alone (the whitespace test only makes the scan stop sooner), j is
        # a parameter the loop never changes, and a rises by exactly one per pass,
        # so the bound strictly decreases; the guard a < j keeps it >= 2 on entry to
        # a pass.
        Invariant(MustTerminate(j - a + 1))
        # invariants-end
        a = a + 1
    Assert(strip_left(ToSeq(s), a, j) == a)
    # `a` is now strip_left(s, i, j); reference that nested form directly so the
    # final equality with seg_text needs no nested-application congruence.
    b = j
    while b > a and is_space(s[b - 1]):
        # invariants-start
        Invariant(Acc(list_pred(s), 1 / 2))
        Invariant(ToSeq(s) == Old(ToSeq(s)))
        Invariant(a <= b and b <= j and j <= len(s))
        Invariant(a == strip_left(ToSeq(s), i, j))
        Invariant(strip_right(ToSeq(s), strip_left(ToSeq(s), i, j), j) ==
                  strip_right(ToSeq(s), strip_left(ToSeq(s), i, j), b))
        # At most b - a + 1 passes remain: this scan counts DOWN, the compound
        # guard terminates on the counter alone (the whitespace test only makes it
        # stop sooner), a is fixed for the whole loop (it was settled by the previous
        # scan), and b drops by exactly one per pass, so the bound strictly
        # decreases; the guard b > a keeps it >= 2 on entry to a pass.
        Invariant(MustTerminate(b - a + 1))
        # invariants-end
        b = b - 1
    Assert(strip_right(ToSeq(s), strip_left(ToSeq(s), i, j), b) == b)
    out = []  # type: List[int]
    t = a
    while t < b:
        # invariants-start
        Invariant(Acc(list_pred(s), 1 / 2))
        Invariant(ToSeq(s) == Old(ToSeq(s)))
        Invariant(a <= t and t <= b and b <= len(s))
        Invariant(a == strip_left(ToSeq(s), i, j))
        Invariant(b == strip_right(ToSeq(s), strip_left(ToSeq(s), i, j), j))
        Invariant(Acc(list_pred(out)))
        Invariant(ToSeq(out) == ToSeq(s).take(t).drop(a))
        # At most b - t + 1 passes remain: b is fixed for the whole loop (settled
        # by the trailing-space scan) and t rises by exactly one per pass, so the
        # bound strictly decreases; the guard t < b keeps it >= 2 on entry to a
        # pass.
        Invariant(MustTerminate(b - t + 1))
        # invariants-end
        out.append(s[t])
        t = t + 1
    Assert(ToSeq(out) == ToSeq(s).take(b).drop(a))
    return out
    # impl-end


def render_nodes(target: List[int]) -> List[int]:
    # pre-conditions-start
    # The type specification is read-only (directive 5: fractional permission).
    Requires(Acc(list_pred(target), 1 / 2))
    # NO domain restriction. Every specification is claimed, including the ones
    # that mix the vertical bar with a bracket, comma, `or` or ellipsis
    # separator: whatever the separators are, the node stream below is the one
    # required. Narrowing this to a bar-only shape would leave the behaviour on
    # every other shape unstated and therefore free.
    # The rendering must COMPLETE (total correctness): without this obligation
    # every Ensures below is claimed only of runs that reach the return, so an
    # implementation that never gets there satisfies the whole postcondition
    # vacuously. Level 5 is strictly above every callee it invokes (next_sep_idx
    # at 4, sep_end_idx at 3, copy_span at 2).
    Requires(MustTerminate(5))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(target), 1 / 2))
    Ensures(Acc(list_pred(Result())))
    # The WHOLE rendered-node stream is pinned: the number of nodes, the kind of
    # each node, and the exact code points each node carries — the specification's
    # own characters over that node's stretch, padding included, with nothing
    # trimmed, normalised, reordered or dropped. Because the marker code points
    # -1/-2/-3 cannot occur in carried text, this single equality determines the
    # node list uniquely; in particular a bar-separated specification cannot be
    # answered with one cross-reference over the whole string (that stream carries
    # the bar and its padding inside a cross-reference node instead of in a
    # literal separator node of its own), and the separator text cannot be
    # silently dropped, re-padded or emitted as a cross-reference.
    Ensures(ToSeq(Result()) == rendered(ToSeq(target), 0))
    # post-conditions-end
    # impl-start
    out = []  # type: List[int]
    n = len(target)
    i = 0
    while True:
        # invariants-start
        Invariant(Acc(list_pred(target), 1 / 2))
        Invariant(Acc(list_pred(out)))
        Invariant(0 <= i and i <= n)
        Invariant(n == len(target))
        Invariant(n == len(ToSeq(target)))
        # telescoping fold: what has been emitted, concatenated with the node
        # stream of the remaining suffix, is the whole node stream.
        Invariant(ToSeq(out) + rendered(ToSeq(target), i) ==
                  rendered(ToSeq(target), 0))
        # The condition is the constant `True`, so the bound comes from what the
        # break counts down: the loop leaves via `break` as soon as no separator
        # remains at or after i, and otherwise resumes at i = e, the end of a
        # separator that starts at j >= i and ends strictly after it (sep_end's
        # postcondition), so the scan index rises by at least one per pass and at
        # most n - i + 1 passes remain. It strictly decreases because only i
        # changes (n is a local fixed before the loop, pinned by
        # Invariant(n == len(target))), and it stays >= 1 because
        # Invariant(0 <= i and i <= n) holds on entry to every pass (so it never
        # reaches the unsatisfiable 0); the pass on which no separator remains is
        # the one that breaks.
        Invariant(MustTerminate(n - i + 1))
        # invariants-end
        # `+ 0` reads the boundary as the plain integer it is; see `sep_end`.
        j = next_sep_idx(target, i) + 0
        if j >= n:
            if i < n:
                Assert(rendered(ToSeq(target), i) ==
                       (ToSeq(target).take(n).drop(i) + PSeq(-1)) + PSeq(-3))
                # the trailing text is one cross-reference carrying it verbatim.
                copy_span(out, target, i, n)
                out.append(-1)
            else:
                Assert(rendered(ToSeq(target), i) == PSeq(-3))
            out.append(-3)
            break
        e = sep_end_idx(target, j) + 0
        Assert(j < e and e <= n)
        if j > i:
            Assert(rendered(ToSeq(target), i) ==
                   ((ToSeq(target).take(j).drop(i) + PSeq(-1)) +
                    (ToSeq(target).take(e).drop(j) + PSeq(-2))) +
                   rendered(ToSeq(target), e))
            # the text before the separator is one cross-reference carrying
            # exactly the specification's characters over [i, j).
            copy_span(out, target, i, j)
            out.append(-1)
        else:
            Assert(rendered(ToSeq(target), i) ==
                   (ToSeq(target).take(e).drop(i) + PSeq(-2)) +
                   rendered(ToSeq(target), e))
        # the separator itself is one literal node carrying [j, e) verbatim.
        copy_span(out, target, j, e)
        out.append(-2)
        i = e
    return out
    # impl-end


def next_sep_idx(s: List[int], i: int) -> int:
    # pre-conditions-start
    Requires(Acc(list_pred(s), 1 / 2))
    Requires(0 <= i and i <= len(s))
    # Locating the leftmost separator must COMPLETE: level 4 sits strictly below
    # its caller's 5 and strictly above the sep_end_idx (3) it invokes per step.
    Requires(MustTerminate(4))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(s), 1 / 2))
    Ensures(ToSeq(s) == Old(ToSeq(s)))
    Ensures(i <= Result() and Result() <= len(s))
    Ensures(Result() == next_sep(ToSeq(s), i))
    # post-conditions-end
    # impl-start
    k = i
    while k < len(s):
        # invariants-start
        Invariant(Acc(list_pred(s), 1 / 2))
        Invariant(ToSeq(s) == Old(ToSeq(s)))
        Invariant(i <= k and k <= len(s))
        Invariant(next_sep(ToSeq(s), i) == next_sep(ToSeq(s), k))
        # At most len(s) - k + 1 passes remain: the sequence is held read-only by
        # the invariant above so its length cannot change, and k rises by exactly
        # one per pass, so the bound strictly decreases; the guard k < len(s) keeps
        # it >= 2 on entry to a pass (so it never reaches the unsatisfiable 0).
        Invariant(MustTerminate(len(s) - k + 1))
        # invariants-end
        if sep_end_idx(s, k) >= 0:
            Assert(next_sep(ToSeq(s), k) == k)
            return k
        k = k + 1
    Assert(next_sep(ToSeq(s), k) == k)
    return k
    # impl-end


def sep_end_idx(s: List[int], i: int) -> int:
    # pre-conditions-start
    Requires(Acc(list_pred(s), 1 / 2))
    Requires(0 <= i and i <= len(s))
    # Measuring the separator token that starts at `i` must COMPLETE: level 3 sits
    # strictly below its caller's 4 and strictly above the strip_left_idx (2) it
    # invokes.
    Requires(MustTerminate(3))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(s), 1 / 2))
    Ensures(ToSeq(s) == Old(ToSeq(s)))
    Ensures(Result() == sep_end(ToSeq(s), i))
    # post-conditions-end
    # impl-start
    n = len(s)
    a = strip_left_idx(s, i, n)
    if a < n and (s[a] == 91 or s[a] == 93 or s[a] == 40 or s[a] == 41 or
                  s[a] == 44):
        c = strip_left_idx(s, a + 1, n)
        if (c + 2 < n and s[c] == 111 and s[c + 1] == 114 and
                is_space(s[c + 2])):
            return strip_left_idx(s, c + 3, n)
        return strip_left_idx(s, a + 1, n)
    if (i < n and is_space(s[i]) and a + 2 < n and s[a] == 111 and
            s[a + 1] == 114 and is_space(s[a + 2])):
        return strip_left_idx(s, a + 2, n)
    if a < n and s[a] == 124:
        return strip_left_idx(s, a + 1, n)
    if i + 2 < n and s[i] == 46 and s[i + 1] == 46 and s[i + 2] == 46:
        return i + 3
    return -1
    # impl-end


def strip_left_idx(s: List[int], i: int, j: int) -> int:
    # pre-conditions-start
    Requires(Acc(list_pred(s), 1 / 2))
    Requires(0 <= i and i <= j and j <= len(s))
    # Skipping padding whitespace must COMPLETE: level 2 sits strictly below its
    # caller's 3 and leaves room below itself for the obligations of the built-in
    # operations it performs.
    Requires(MustTerminate(2))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(s), 1 / 2))
    Ensures(ToSeq(s) == Old(ToSeq(s)))
    Ensures(i <= Result() and Result() <= j)
    Ensures(Result() == strip_left(ToSeq(s), i, j))
    # post-conditions-end
    # impl-start
    a = i
    while a < j and is_space(s[a]):
        # invariants-start
        Invariant(Acc(list_pred(s), 1 / 2))
        Invariant(ToSeq(s) == Old(ToSeq(s)))
        Invariant(i <= a and a <= j and j <= len(s))
        Invariant(strip_left(ToSeq(s), i, j) == strip_left(ToSeq(s), a, j))
        # At most j - a + 1 passes remain: the compound guard terminates on the
        # counter alone (the whitespace test only makes the scan stop sooner), j is
        # a parameter the loop never changes, and a rises by exactly one per pass,
        # so the bound strictly decreases; the guard a < j keeps it >= 2 on entry to
        # a pass.
        Invariant(MustTerminate(j - a + 1))
        # invariants-end
        a = a + 1
    Assert(strip_left(ToSeq(s), a, j) == a)
    return a
    # impl-end


def copy_span(out: List[int], s: List[int], i: int, j: int) -> None:
    # pre-conditions-start
    Requires(Acc(list_pred(s), 1 / 2))
    Requires(list_pred(out))
    Requires(0 <= i and i <= j and j <= len(s))
    # Appending the span must COMPLETE: level 2 sits strictly below its caller's 5
    # and leaves room for the built-in append it performs.
    Requires(MustTerminate(2))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(s), 1 / 2))
    Ensures(list_pred(out))
    Ensures(ToSeq(s) == Old(ToSeq(s)))
    # exactly the specification's own code points over [i, j) are appended, in
    # order, with nothing trimmed or substituted.
    Ensures(ToSeq(out) == Old(ToSeq(out)) + Old(ToSeq(s)).take(j).drop(i))
    # post-conditions-end
    # impl-start
    t = i
    while t < j:
        # invariants-start
        Invariant(Acc(list_pred(s), 1 / 2))
        Invariant(list_pred(out))
        Invariant(ToSeq(s) == Old(ToSeq(s)))
        Invariant(i <= t and t <= j and j <= len(s))
        Invariant(ToSeq(out) == Old(ToSeq(out)) + ToSeq(s).take(t).drop(i))
        # At most j - t + 1 passes remain: j is a parameter the loop never changes
        # and t rises by exactly one per pass, so the bound strictly decreases; the
        # guard t < j keeps it >= 2 on entry to a pass.
        Invariant(MustTerminate(j - t + 1))
        # invariants-end
        out.append(s[t])
        t = t + 1
    # impl-end
