"""Twin-artifact model for astropy__astropy-14508.

Behaviour under specification (stated as desired behaviour, not as an edit):

  A finite signed number is rendered to a bounded-width decimal field. The field
  width is capped at 20 characters. The desired rendering reproduces the number
  exactly using as FEW significant digits as the number requires:

    * whenever the exact rendering already fits within the 20-character cap, the
      field reads back to the original number (round-trips) AND it spends only
      the minimal number of significant digits needed to do so — it carries no
      spurious trailing digits;

    * the field carries a leading minus sign exactly when the number rendered is
      a negative one, and no sign otherwise, so a rendering never invents or
      discards the number's sign;

    * only when the exact rendering would exceed the cap is it trimmed to 20
      characters. The trim preserves a trailing exponent marker `E...` if one is
      present (the significand is shortened and the exponent suffix is kept in
      full); otherwise the field is cut to its first 20 characters.

The rendered field is modelled as `List[int]` of code points (Nagini bans `str`
indexing); the specification is carried by `PSeq[int]` via `ToSeq`. The number
being rendered is carried by a PAIR: an interpreted real `value` (verified with
`--float-encoding=real`) together with a sign flag `neg`. The pair is what a
signed finite number refines to, and the pair rather than the real alone because
an interpreted real identifies a negative zero with a positive one while a signed
number does not — a renderer that reproduces the number exactly therefore
distinguishes them, so the sign travels alongside the value instead of being
recovered from it. Away from zero the flag is pinned by the value's own sign (the
pre-conditions say so, so no state that denotes no number is admitted); only at a
zero value does the flag carry what the real alone cannot. Three opaque
numeric quantities carry the theory: `parse_dec` reads a decimal field back to a
real number, `sig_count` is the number of significant digits a field spends, and
`min_sig` is the fewest significant digits a number needs to be reproduced
exactly. Two candidate renderers are available: `shortest_field` (minimal
significant digits) and `padded_field` (a wider preset precision); the routine
selects the former. Their provenance and executable soundness check are in
mapping.md / axiom_check.py.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List
from nagini_contracts.contracts import *
from nagini_contracts.obligations import MustTerminate


# axioms-start
@Pure
@ContractOnly
def parse_dec(field: PSeq[int]) -> float:
    """Read a decimal field (a sequence of code points) back to the real number
    it denotes. Opaque: the value-reconstruction theory the round-trip property
    is stated over (the inverse of decimal rendering)."""
    Requires(len(field) >= 0)


@Pure
@ContractOnly
def sig_count(field: PSeq[int]) -> int:
    """The number of significant digits the field `field` spends. Opaque count
    over the field's digit run (independent of sign, decimal point, exponent)."""
    Requires(len(field) >= 0)
    Ensures(Result() >= 0)


@Pure
@ContractOnly
def min_sig(value: float) -> int:
    """The fewest significant digits any decimal field needs to read back to
    `value` exactly. A property of the number's digits alone — a sign costs no
    significant digits, so this does not depend on the sign flag; at least one."""
    Ensures(Result() >= 1)


@Pure
@ContractOnly
def shortest_field_len(value: float, neg: bool) -> int:
    """The length of the minimal-significant-digit exact field for the number
    `(value, neg)` denotes. A property of that number alone (it is
    `len(shortest_field(value, neg))`); used to state whether the desired
    rendering fits the cap without re-deriving it. It depends on the sign flag as
    well as the value, because a negative number's field carries one more
    character (the sign) than the corresponding positive one's."""
    Ensures(Result() >= 1)


@Pure
@ContractOnly
def shortest_seq(value: float, neg: bool) -> PSeq[int]:
    """The minimal-significant-digit exact rendering of the number `(value, neg)`
    denotes, AS A VALUE (the pure sequence content of
    `shortest_field(value, neg)`). A property of that number alone, so the
    desired bounded rendering can be pinned structurally against it — the bounded
    field must be *produced by* trimming this exact rendering, not merely match it
    in length. Round-trips, spends the minimal significant digits, signs the field
    exactly when the number is negative, and any exponent suffix `E...` is
    short."""
    Ensures(len(Result()) == shortest_field_len(value, neg))
    Ensures(parse_dec(Result()) == value)
    Ensures(sig_count(Result()) == min_sig(value))
    # The exact rendering carries a leading minus (code point 45) exactly when
    # the number rendered is a negative one. A negative zero is a negative
    # number, which is why the sign is carried alongside the magnitude: the
    # real value alone cannot say which of the two zeros is being rendered.
    Ensures(Implies(neg, len(Result()) >= 2 and Result()[0] == 45))
    Ensures(Implies(not neg, len(Result()) >= 1 and Result()[0] != 45))
    Ensures(Implies(0 <= e_index(Result()),
                    len(Result()) - e_index(Result()) <= 5))


@ContractOnly
def shortest_field(value: float, neg: bool) -> List[int]:
    """Render the number `(value, neg)` denotes exactly, using the minimal number
    of significant digits, with any exponent marker written in upper case `E`.
    Provenance + G-AX soundness in mapping.md / axiom_check.py. Rendering a
    number is bounded, loop-free work, so it always terminates (level 1: callable
    from a body holding level 2 without leaking the caller's obligation)."""
    Requires(MustTerminate(2))
    Ensures(Acc(list_pred(Result())))
    # The materialized field carries exactly the pure exact-rendering value, so
    # round-trip, minimal-significant-digit, sign, length and suffix-bound
    # properties all transfer from `shortest_seq`.
    Ensures(ToSeq(Result()) == shortest_seq(value, neg))


@ContractOnly
def padded_field(value: float, neg: bool) -> List[int]:
    """Render the number `(value, neg)` denotes to a wider preset precision. The
    weaker candidate renderer: it yields a non-empty field with the same
    exponent-suffix shape, but spends a preset precision rather than the minimal
    significant digits — it may carry spurious trailing digits, and its contract
    pins neither the field's content nor its sign. Provenance + G-AX soundness in
    mapping.md / axiom_check.py. Rendering a number is bounded, loop-free work, so
    it always terminates (level 1: callable from a body holding level 2 without
    leaking the caller's obligation)."""
    Requires(MustTerminate(6))
    Ensures(Acc(list_pred(Result())))
    Ensures(len(Result()) >= 1)
    Ensures(Implies(0 <= e_index(ToSeq(Result())),
                    len(Result()) - e_index(ToSeq(Result())) <= 5))
# axioms-end


# pure-start
@Pure
def e_index(field: PSeq[int]) -> int:
    """Index of the first exponent marker `E` (code point 69) in `field`, or -1
    if there is none."""
    Ensures(Result() == -1 or (0 <= Result() and Result() < len(field)))
    Ensures(Implies(0 <= Result() and Result() < len(field),
                    field[Result()] == 69))
    return e_index_from(field, 0)


@Pure
def e_index_from(field: PSeq[int], i: int) -> int:
    """First index >= i of the exponent marker `E` in `field`, or -1."""
    Requires(0 <= i and i <= len(field))
    Ensures(Result() == -1 or (i <= Result() and Result() < len(field)))
    Ensures(Implies(0 <= Result() and Result() < len(field),
                    field[Result()] == 69))
    if i == len(field):
        return -1
    if field[i] == 69:
        return i
    return e_index_from(field, i + 1)
# pure-end


def format_float_field(value: float, neg: bool) -> List[int]:
    # pre-conditions-start
    # The renderer is applied to finite numbers (the only values that reach it);
    # no input mutation, so no list inputs to protect with fractions.
    Requires(MustTerminate(10))
    # `(value, neg)` denotes a signed finite number: away from zero the sign flag
    # agrees with the value's own sign, so the pair says nothing a signed number
    # could not. Only at a zero value is the flag free, and there it says which of
    # the two zeros is being rendered — the one distinction an interpreted real
    # cannot make. These two clauses admit every signed finite number and exclude
    # only the pairs that denote none.
    Requires(Implies(value > 0.0, not neg))
    Requires(Implies(value < 0.0, neg))
    # pre-conditions-end
    # post-conditions-start
    # The rendered field never exceeds the 20-character cap and is non-empty.
    Ensures(Acc(list_pred(Result())))
    Ensures(1 <= len(Result()) and len(Result()) <= 20)
    # When the exact rendering of the number already fits the cap, the field IS
    # that exact rendering: it reads back to the number (round-trips), spends only
    # the minimal significant digits the number needs (no spurious trailing
    # digits), and carries the number's sign — a leading minus exactly when the
    # number rendered is negative, including when its magnitude is zero.
    Ensures(Implies(shortest_field_len(value, neg) <= 20,
                    ToSeq(Result()) == shortest_seq(value, neg)))
    # When even the minimal rendering would exceed the cap, the field is the
    # exact rendering TRIMMED to 20 characters — pinned by content, not merely by
    # length, so a result that drops or mangles the rendering cannot satisfy it.
    # If the exact rendering carries no exponent marker, the field is its first
    # 20 characters; if it carries an exponent marker at index `idx`, the
    # significand is shortened and the whole exponent suffix is kept:
    # `take(20 - (len - idx))` of the significand, then `drop(idx)` (the suffix).
    Ensures(Implies(shortest_field_len(value, neg) > 20
                    and e_index(shortest_seq(value, neg)) < 0,
                    ToSeq(Result()) == shortest_seq(value, neg).take(20)))
    Ensures(Implies(shortest_field_len(value, neg) > 20
                    and 0 <= e_index(shortest_seq(value, neg)),
                    ToSeq(Result())
                    == shortest_seq(value, neg).take(
                        20 - (shortest_field_len(value, neg)
                              - e_index(shortest_seq(value, neg))))
                    + shortest_seq(value, neg).drop(
                        e_index(shortest_seq(value, neg)))))
    # post-conditions-end
    # impl-start
    vs = shortest_field(value, neg)
    n = len(vs)
    if n <= 20:
        return vs
    # Over the cap: trim to 20 characters, preserving any exponent suffix. The
    # carrier `vs` IS the exact rendering (ToSeq(vs) == shortest_seq(value, neg)),
    # so the trim is stated structurally against it via take/drop/concat.
    idx = e_index(ToSeq(vs))
    result = []  # type: List[int]
    old_seq = ToSeq(result)  # type carrier for the per-append step (see below)
    if idx < 0:
        j = 0
        while j < 20:
            # invariants-start
            Invariant(Acc(list_pred(vs)) and Acc(list_pred(result)))
            Invariant(0 <= j and j <= 20 and n == len(vs) and n > 20)
            Invariant(n == shortest_field_len(value, neg))
            Invariant(ToSeq(vs) == shortest_seq(value, neg))
            Invariant(idx == e_index(ToSeq(vs)) and idx < 0)
            Invariant(len(result) == j)
            Invariant(ToSeq(result) == ToSeq(vs).take(j))
            Invariant(MustTerminate(20 - j + 1))
            # invariants-end
            old_seq = ToSeq(result)
            result.append(vs[j])
            Assert(ToSeq(result) == old_seq + PSeq(vs[j]))
            Assert(ToSeq(vs).take(j) + PSeq(ToSeq(vs)[j]) == ToSeq(vs).take(j + 1))
            j = j + 1
        Assert(ToSeq(result) == shortest_seq(value, neg).take(20))
    else:
        keep = 20 - (n - idx)
        j = 0
        while j < keep:
            # invariants-start
            Invariant(Acc(list_pred(vs)) and Acc(list_pred(result)))
            Invariant(0 <= idx and idx < n and n == len(vs) and n > 20)
            Invariant(n == shortest_field_len(value, neg))
            Invariant(ToSeq(vs) == shortest_seq(value, neg))
            Invariant(idx == e_index(ToSeq(vs)))
            Invariant(keep == 20 - (n - idx) and keep >= 0 and keep <= idx)
            Invariant(0 <= j and j <= keep and len(result) == j)
            Invariant(ToSeq(result) == ToSeq(vs).take(j))
            Invariant(MustTerminate(keep - j + 1))
            # invariants-end
            old_seq = ToSeq(result)
            result.append(vs[j])
            Assert(ToSeq(result) == old_seq + PSeq(vs[j]))
            Assert(ToSeq(vs).take(j) + PSeq(ToSeq(vs)[j]) == ToSeq(vs).take(j + 1))
            j = j + 1
        Assert(ToSeq(result) == ToSeq(vs).take(keep))
        k = idx
        while k < n:
            # invariants-start
            Invariant(Acc(list_pred(vs)) and Acc(list_pred(result)))
            Invariant(0 <= idx and idx <= k and k <= n and n == len(vs) and n > 20)
            Invariant(n == shortest_field_len(value, neg))
            Invariant(ToSeq(vs) == shortest_seq(value, neg))
            Invariant(idx == e_index(ToSeq(vs)))
            Invariant(keep == 20 - (n - idx) and keep >= 0)
            Invariant(len(result) == keep + (k - idx))
            Invariant(ToSeq(result)
                      == ToSeq(vs).take(keep)
                      + ToSeq(vs).drop(idx).take(k - idx))
            Invariant(MustTerminate(n - k + 1))
            # invariants-end
            old_seq = ToSeq(result)
            result.append(vs[k])
            Assert(ToSeq(result) == old_seq + PSeq(vs[k]))
            Assert(ToSeq(vs).drop(idx)[k - idx] == ToSeq(vs)[k])
            Assert(ToSeq(vs).drop(idx).take(k - idx) + PSeq(ToSeq(vs).drop(idx)[k - idx])
                   == ToSeq(vs).drop(idx).take(k - idx + 1))
            k = k + 1
        Assert(ToSeq(vs).drop(idx).take(n - idx) == ToSeq(vs).drop(idx))
        Assert(ToSeq(result)
               == shortest_seq(value, neg).take(keep)
               + shortest_seq(value, neg).drop(idx))
    return result
    # impl-end
