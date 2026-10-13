"""Twin-artifact model for sphinx-doc__sphinx-7985.

Behaviour under specification (stated as desired behaviour, not as an edit):

  A reference target is classified, without contacting the network, by reading
  it as a sequence of Unicode code points. The classification distinguishes a
  handful of status outcomes, encoded here as small integers:

      UNCHECKED, WORKING, MISSING, IGNORED  (the locally-decidable outcomes),
      and a remotely-handled outcome whose value is opaque to this spec.

  Two opaque predicates over a target abstract the recognition steps and are
  the ONLY string-shape facts this contract uses:

      `is_skippable(t)`  — t matches a recognised non-verifiable form, so it
                           carries no local claim to verify;
      `is_remote(t)`     — t names a remotely-handled resource, delegated to
                           the unchanged remote path.

  The classification of one target is then:

    (1) A skippable target (`is_skippable`) is UNCHECKED — there is nothing to
        verify for it.

    (2) Otherwise, a non-remote target (`not is_remote`) denotes a resource
        decidable from the local source tree:
          - if it is present, the target is WORKING;
          - else if some configured ignore pattern matches it, it is IGNORED;
          - else the target is MISSING.

    (3) A remote target (`is_remote`) is delegated to the unchanged remote
        path, whose outcome is opaque to this specification.

  The decisive content: a non-remote, non-skippable target that is absent
  locally and matches no ignore pattern is MISSING — it is positively
  verified, not silently passed through as an undecided local target.

Strings are modelled as `List[int]` of Unicode code points (Nagini bans `str`
indexing); the specification is carried over `PSeq[int]`. The two recognition
predicates are modelled DEEPLY (spelled-out folds over the code points) and
validated == their real counterparts out-of-band by axiom_check.py (G-AX); see
mapping.md for the concrete forms they recognise. Two genuinely
environment-dependent facts — whether the resource is present locally, and
whether any ignore pattern matches — and the opaque remote outcome enter as
values, not as consumed axioms.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List
from nagini_contracts.contracts import *
from nagini_contracts.obligations import MustTerminate


# axioms-start
# (No consumed axioms. The two string-recognition decisions used by the
#  classification are modelled DEEPLY below (`starts_with`, `has_uri_scheme`)
#  and validated == their real counterparts out-of-band by axiom_check.py /
#  G-AX (the concrete recognised forms are documented in mapping.md), never
#  consumed. The local-presence fact, the ignore-pattern fact, and the opaque
#  remote outcome are plain input values, not axioms.)
# axioms-end


# pure-start
@Pure
def is_lower(c: int) -> bool:
    """A single code point is an ASCII lowercase letter U+0061..U+007A."""
    return 97 <= c and c <= 122


@Pure
def prefix_eq(s: PSeq[int], lit: PSeq[int]) -> bool:
    """The first `len(lit)` code points of `s` equal `lit` code point for code
    point — a LITERAL prefix match. Total: if `s` is shorter than `lit` no such
    match exists, so the result is False. Front-recursive (over both sequences)
    so a single unfold is available per loop step."""
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
def lower_run(s: PSeq[int]) -> int:
    """Length of the maximal leading run of ASCII lowercase letters of `s`.
    Front-recursive so a single unfold is available per loop step."""
    if len(s) == 0:
        return 0
    if not is_lower(s[0]):
        return 0
    return 1 + lower_run(s.drop(1))


@Pure
def all_lower_below(s: PSeq[int], k: int) -> bool:
    """Every code point of `s` strictly below index `k` is lowercase.
    Front-recursive so a single unfold is available per loop step."""
    Requires(0 <= k and k <= len(s))
    if k == 0:
        return True
    return is_lower(s[0]) and all_lower_below(s.drop(1), k - 1)


@Pure
def lemma_lower_run_eq(s: PSeq[int], k: int) -> bool:
    """If `s[0..k)` are all lowercase and the run stops at `k` (end of `s`, or a
    non-lowercase code point there), then the maximal leading lowercase run has
    length exactly `k`. Proven by front-recursion on `s`/`k`."""
    Requires(0 <= k and k <= len(s))
    Requires(all_lower_below(s, k))
    Requires(k == len(s) or not is_lower(s[k]))
    Ensures(Result())
    Ensures(lower_run(s) == k)
    if k == 0:
        return True
    return lemma_lower_run_eq(s.drop(1), k - 1)


@Pure
def lemma_all_lower_extend(s: PSeq[int], k: int) -> bool:
    """Extending an all-lowercase prefix of length `k` by one more lowercase
    code point at index `k` yields an all-lowercase prefix of length `k+1`.
    Proven by front-recursion."""
    Requires(0 <= k and k < len(s))
    Requires(all_lower_below(s, k))
    Requires(is_lower(s[k]))
    Ensures(Result())
    Ensures(all_lower_below(s, k + 1))
    if k == 0:
        Assert(all_lower_below(s.drop(1), 0))
        Assert(is_lower(s[0]))
        return True
    Assert(lemma_all_lower_extend(s.drop(1), k - 1))
    Assert(is_lower(s[0]))
    return True


@Pure
def lit_http() -> PSeq[int]:
    # one of the recognised "remote" leading literals (code points; mapping.md)
    return PSeq(104, 116, 116, 112, 58)


@Pure
def lit_https() -> PSeq[int]:
    # one of the recognised "remote" leading literals (code points; mapping.md)
    return PSeq(104, 116, 116, 112, 115, 58)


@Pure
def lit_hash() -> PSeq[int]:
    # one of the recognised "skippable" leading literals (code points; mapping.md)
    return PSeq(35)


@Pure
def lit_mailto() -> PSeq[int]:
    # one of the recognised "skippable" leading literals (code points; mapping.md)
    return PSeq(109, 97, 105, 108, 116, 111, 58)


@Pure
def has_uri_scheme(s: PSeq[int]) -> bool:
    """Recognises the leading shape described in mapping.md (a maximal leading
    run of ASCII-lowercase code points, of length >= 1, immediately followed by
    the three code points U+003A, U+002F, U+002F). `k` is the length of that
    leading lowercase run; the result is True iff `k >= 1` and code points
    `k, k+1, k+2` are `:`,`/`,`/`."""
    k = lower_run(s)
    return (
        k >= 1
        and len(s) >= k + 3
        and s[k] == 58
        and s[k + 1] == 47
        and s[k + 2] == 47
    )


# Status codes (the local-classification outcomes; the remote branch carries
# its own opaque outcome value).
@Pure
def UNCHECKED() -> int:
    return 0


@Pure
def WORKING() -> int:
    return 1


@Pure
def MISSING() -> int:
    return 2


@Pure
def IGNORED() -> int:
    return 3


@Pure
def classify(s: PSeq[int], file_exists: bool, ignore_match: bool,
             remote: int) -> int:
    """The full per-target classification, as a pure function of the target
    code points and the three environment facts (file present on disk, an
    ignore pattern matches, the opaque remote outcome). Mirrors the decision
    cascade (1)-(3) above."""
    if len(s) == 0 or prefix_eq(s, lit_hash()) or prefix_eq(s, lit_mailto()):
        return UNCHECKED()
    if not (prefix_eq(s, lit_http()) or prefix_eq(s, lit_https())):
        if has_uri_scheme(s):
            return UNCHECKED()
        if file_exists:
            return WORKING()
        if ignore_match:
            return IGNORED()
        return MISSING()
    return remote
# pure-end


def starts_with(target: List[int], lit: List[int]) -> bool:
    # pre-conditions-start
    Requires(Acc(list_pred(target), 1 / 4))
    Requires(Acc(list_pred(lit), 1 / 4))
    Requires(MustTerminate(2))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(target), 1 / 4))
    Ensures(Acc(list_pred(lit), 1 / 4))
    # Result is the LITERAL prefix match of `lit` against `target`.
    Ensures(Result() == prefix_eq(ToSeq(target), ToSeq(lit)))
    # post-conditions-end
    # impl-start
    n = len(lit)
    if n > len(target):
        Assert(lemma_prefix_too_long(ToSeq(target), ToSeq(lit)))
        return False
    ok = True
    i = n
    while i > 0:
        # invariants-start
        Invariant(Acc(list_pred(target), 1 / 4))
        Invariant(Acc(list_pred(lit), 1 / 4))
        Invariant(0 <= i and i <= n and n == len(lit))
        Invariant(n <= len(target))
        Invariant(len(ToSeq(lit).drop(i)) <= len(ToSeq(target).drop(i)))
        Invariant(ok == prefix_eq(ToSeq(target).drop(i), ToSeq(lit).drop(i)))
        # Termination: `i` falls by exactly 1 per pass towards the fixed floor
        # 0, so `i + 1` strictly decreases; the guard `i > 0` makes it >= 2 at
        # every loop head.
        Invariant(MustTerminate(i + 1))
        # invariants-end
        Assert(ToSeq(target).drop(i - 1)[0] == ToSeq(target)[i - 1])
        Assert(ToSeq(lit).drop(i - 1)[0] == ToSeq(lit)[i - 1])
        Assert(ToSeq(target).drop(i - 1).drop(1) == ToSeq(target).drop(i))
        Assert(ToSeq(lit).drop(i - 1).drop(1) == ToSeq(lit).drop(i))
        if target[i - 1] != lit[i - 1]:
            ok = False
        i = i - 1
    Assert(ToSeq(target).drop(0) == ToSeq(target))
    Assert(ToSeq(lit).drop(0) == ToSeq(lit))
    return ok
    # impl-end


def scheme_present(target: List[int]) -> bool:
    # pre-conditions-start
    Requires(Acc(list_pred(target), 1 / 4))
    Requires(MustTerminate(2))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(target), 1 / 4))
    # Result is the leading-shape recognition decision on `target` (mapping.md).
    Ensures(Result() == has_uri_scheme(ToSeq(target)))
    # post-conditions-end
    # impl-start
    n = len(target)
    k = 0
    while k < n and 97 <= target[k] and target[k] <= 122:
        # invariants-start
        Invariant(Acc(list_pred(target), 1 / 4))
        Invariant(0 <= k and k <= n and n == len(target))
        Invariant(all_lower_below(ToSeq(target), k))
        # Termination: the guard's FIRST conjunct `k < n` alone bounds the run --
        # `k` rises by exactly 1 per pass and `n == len(target)` is fixed (target
        # is only read), so `n - k + 1` strictly decreases and is >= 2 at every
        # loop head. The `97 <= target[k]` / `target[k] <= 122` conjuncts only
        # make the loop exit sooner, so they cannot invalidate the bound.
        Invariant(MustTerminate(n - k + 1))
        # invariants-end
        Assert(lemma_all_lower_extend(ToSeq(target), k))
        k = k + 1
    # k is now the maximal leading lowercase run length.
    Assert(k == n or not is_lower(ToSeq(target)[k]))
    Assert(lemma_lower_run_eq(ToSeq(target), k))
    Assert(lower_run(ToSeq(target)) == k)
    if k < 1:
        return False
    if k + 3 > n:
        return False
    res = (target[k] == 58 and target[k + 1] == 47 and target[k + 2] == 47)
    return res
    # impl-end


def check(target: List[int], file_exists: bool, ignore_match: bool,
          remote: int) -> int:
    # pre-conditions-start
    Requires(Acc(list_pred(target), 1 / 2))
    # `remote` carries the opaque outcome of the unchanged remote-handling path.
    # Level 3: strictly above the level-2 callees starts_with / scheme_present,
    # and it leaves room for the list literals this body builds.
    Requires(MustTerminate(3))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(target), 1 / 2))
    # The classification is exactly the decision cascade `classify`.
    Ensures(Result() == classify(ToSeq(target), file_exists, ignore_match,
                                  remote))
    # A locally-decidable target (non-remote, non-skippable) that is absent
    # locally and matches no ignore pattern is MISSING; a present one is
    # WORKING; an ignore-matched one is IGNORED.
    Ensures(Implies(
        len(target) > 0
        and not prefix_eq(ToSeq(target), lit_hash())
        and not prefix_eq(ToSeq(target), lit_mailto())
        and not prefix_eq(ToSeq(target), lit_http())
        and not prefix_eq(ToSeq(target), lit_https())
        and not has_uri_scheme(ToSeq(target))
        and not file_exists
        and not ignore_match,
        Result() == MISSING()))
    Ensures(Implies(
        len(target) > 0
        and not prefix_eq(ToSeq(target), lit_hash())
        and not prefix_eq(ToSeq(target), lit_mailto())
        and not prefix_eq(ToSeq(target), lit_http())
        and not prefix_eq(ToSeq(target), lit_https())
        and not has_uri_scheme(ToSeq(target))
        and file_exists,
        Result() == WORKING()))
    Ensures(Implies(
        len(target) > 0
        and not prefix_eq(ToSeq(target), lit_hash())
        and not prefix_eq(ToSeq(target), lit_mailto())
        and not prefix_eq(ToSeq(target), lit_http())
        and not prefix_eq(ToSeq(target), lit_https())
        and not has_uri_scheme(ToSeq(target))
        and not file_exists
        and ignore_match,
        Result() == IGNORED()))
    # post-conditions-end
    # impl-start
    h = []   # type: List[int]
    h = [35]
    m = [109, 97, 105, 108, 116, 111, 58]  # type: List[int]
    if len(target) == 0 or starts_with(target, h) or starts_with(target, m):
        return UNCHECKED()
    hp = [104, 116, 116, 112, 58]  # type: List[int]
    hsp = [104, 116, 116, 112, 115, 58]  # type: List[int]
    if not (starts_with(target, hp) or starts_with(target, hsp)):
        if scheme_present(target):
            # recognised non-verifiable leading shape: nothing to verify
            return UNCHECKED()
        else:
            if file_exists:
                return WORKING()
            else:
                if ignore_match:
                    return IGNORED()
                else:
                    return MISSING()
    return remote
    # impl-end
