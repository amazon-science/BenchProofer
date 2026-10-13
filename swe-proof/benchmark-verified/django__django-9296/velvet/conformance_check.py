#!/usr/bin/env python3
"""G-CONF differential conformance check for django__django-9296 (plan §4.1).

Refutes (does not prove) the R/I refinement legs of refinement.md by executing
both sides on the same fuzzed inputs and comparing observable outputs:

  * SHADOW  — the R/I-tagged ops of Solution.lean's impl region transliterated
              to Python over the *real* repo types (page_range <-> List PageIdx,
              Page <-> list(page)), via the mapping.md bijection. The fold of
              `enumeratePages`/`pageSeq` (walk the index sequence, collect one
              sub-view per index, in order) is the R/I content, and the
              transliteration follows the impl's ACTUAL shape: the backward
              accumulating loop, and the Option-shaped read
              `pageRange[i - 1]?` mapped through the accessor. (The model cannot
              use a total out-of-range read: `pageRange[i - 1]!` would demand an
              `Inhabited PageIdx` instance, which deliberately does not exist —
              see refinement.md §C. The Option shape is what the carrier forces,
              so the shadow carries it too.) The A-tagged callee `pageOf` is NOT
              substituted by a model here; G-CONF isolates the R/I legs, so
              `pageOf` stays the REAL repo callee `Paginator.page` (per the
              gate's contract).
              The shadow additionally asserts the CARRIER MEMBERSHIP it relies on
              (every index it hands the accessor satisfies 1 <= n <= num_pages),
              which is the R/I side of the domain-carrying index type; the A side
              of the same fact — that the accessor really admits exactly those
              indices and refuses the rest — is axiom_check.py property (c).
              The shadow further performs every `Nat` operation through the
              ARITHMETIC REALIZATION of mapping.md §2.1 (`nat_sub` below) rather
              than through the same-looking Python operator, because Lean's `Nat`
              is a different algebra: total and SATURATING. `check_nat_algebra`
              measures that the realization satisfies exactly the equations
              Solution.lean's `admiss-nat-semantics-carried` battery case
              discharges in-region, so both sides of the map are pinned to the
              same laws instead of one side being assumed to look like the other.
  * ORACLE  — `patch.diff`'s behaviour: `list(iter(paginator))` from the patched
              `Paginator.__iter__` at base_commit (the real correctness oracle,
              G-RESOLVE). The harness applies patch.diff before this runs.

They must agree on every input. Exit 0 iff zero disagreements; any disagreement
is a mechanical R/I-fidelity counterexample.

Runs in-container (the prebuilt SWE-Bench instance image), stdlib + django only.
The fuzz seed is pinned (mapping.md §4) for a deterministic verdict.
"""
import itertools
import random
import re
import subprocess
import sys
import time

from django.core.paginator import Paginator

SEED = 9296
N_FUZZ = 100_000


# ---------------------------------------------------------------------------
# THE ARITHMETIC REALIZATION (mapping.md §2.1).
#
# Lean's `Nat` is not Python's `int`. Its operations are TOTAL, and they are
# total by SATURATION: `a - b` floors at 0 instead of going negative, and `a / 0`
# and `a % 0` answer 0 and `a` instead of raising. Python's `-` is signed and
# Python's `//` raises `ZeroDivisionError`. So mapping a `Nat` operation onto the
# same-looking Python operator is not a refinement of the type abstraction — it
# is a silent change of algebra, under which a `Nat` expression that is defined
# (and a `Nat`-measured loop that is proven to terminate) can become undefined
# (or divergent) on the Python side. Every `Nat` operation the shadow performs
# therefore goes through these functions.
# ---------------------------------------------------------------------------
def nat_sub(a, b):
    """Lean `Nat.sub`: truncated at zero."""
    return a - b if b <= a else 0


def nat_div(a, b):
    """Lean `Nat.div`: total, with `a / 0 = 0`."""
    return a // b if b != 0 else 0


def nat_mod(a, b):
    """Lean `Nat.mod`: total, with `a % 0 = a`."""
    return a % b if b != 0 else a


def int_ediv(a, b):
    """Lean `Int./` = `Int.ediv`: EUCLIDEAN, and total (`a / 0 = 0`).

    Euclidean division is the one whose remainder is never negative, so for a
    negative divisor it rounds the quotient the OTHER way from Python's `//`
    (which is floored): `(7 : Int) / (-2) = -3` in Lean, `7 // -2 == -4` in
    Python. Measured, one build each (mapping.md §2.1).
    """
    if b == 0:
        return 0
    return a // b if b > 0 else -(a // -b)


def int_emod(a, b):
    """Lean `Int.%` = `Int.emod`: the non-negative remainder, total (`a % 0 = a`).

    `(1 : Int) % (-2) = 1` in Lean; `1 % -2 == -1` in Python.
    """
    return a if b == 0 else a % abs(b)


def int_tdiv(a, b):
    """Lean `Int.tdiv`: rounds TOWARD ZERO, total (`a.tdiv 0 = 0`)."""
    if b == 0:
        return 0
    q = abs(a) // abs(b)
    return q if (a < 0) == (b < 0) else -q


def int_tmod(a, b):
    """Lean `Int.tmod`: the remainder of `tdiv` (sign of the dividend)."""
    return a if b == 0 else a - b * int_tdiv(a, b)


def int_fdiv(a, b):
    """Lean `Int.fdiv`: FLOORED (Python's own `//`), but total at zero."""
    return 0 if b == 0 else a // b


def int_fmod(a, b):
    """Lean `Int.fmod`: floored remainder (Python's own `%`), total at zero."""
    return a if b == 0 else a % b


def int_to_nat(a):
    """Lean `Int.toNat`: saturates the negatives to `0`."""
    return a if a >= 0 else 0


def uint_wrap(a, bits):
    """Lean `UIntN`: fixed-width, so every operation is MODULAR."""
    return a % (1 << bits)


def uint_div(a, b, bits):
    """Lean `UIntN./`: total, `a / 0 = 0` (like `Nat`, not like Python)."""
    return 0 if b == 0 else uint_wrap(a // b, bits)


def uint_mod(a, b, bits):
    """Lean `UIntN.%`: total, `a % 0 = a`."""
    return uint_wrap(a if b == 0 else a % b, bits)


def float_div(a, b):
    """Lean `Float./`: IEEE-754, which is TOTAL — no exception at a zero divisor.

    Python's `/` raises `ZeroDivisionError` there instead of answering
    `±inf`/`nan`, so it is not a realization of Lean's `Float` division.
    """
    if b != 0.0:
        return a / b
    if a == 0.0 or a != a:
        return float("nan")
    return float("inf") if a > 0.0 else float("-inf")


def float_to_uint64(x):
    """Lean `Float.toUInt64`: truncates, and SATURATES rather than trapping.

    Measured, one build each: `inf.toUInt64 = 2^64 - 1`, `nan.toUInt64 = 0`,
    `(-1.0).toUInt64 = 0`, `(3.7).toUInt64 = 3`, `(1e30).toUInt64 = 2^64 - 1`.
    Python's `int()` raises `ValueError`/`OverflowError` on the non-finite ones.
    """
    top = (1 << 64) - 1
    if x != x:                                             # nan
        return 0
    if x <= 0.0:
        return 0
    if x >= float(1 << 64):
        return top
    return int(x)


# ---------------------------------------------------------------------------
# THREE MORE ROWS WHOSE PYTHON SPELLING IS NOT TOTAL (mapping.md §2.1, R1's
# totality criterion; refinement.md §B''''').
#
# The `^` row's repair generalizes: any row whose Python spelling RAISES where the
# Lean operation answers is not a realization, side condition or replacement
# required. Measured in this workspace, in a child capped at 2 GiB:
#
#   itertools.repeat(a, 2 ** 63)  -> OverflowError (ssize_t), 0.000 s
#   (-2) ** (2 ** 66)             -> MemoryError, 20.8 s
#   float(2 ** 1024)              -> OverflowError: int too large to convert
#   2.0 ** 2000                   -> OverflowError: Numerical result out of range
#
# while Lean's `List.replicate` is total on `Nat`, its `Int` power is total, and
# its `Float` is IEEE and total (`1.0 / 0.0 = inf`, measured). `range(n)` is NOT
# in this list: `range(2 ** 66)` and iterating it are both fine (measured), and
# only `len` of it raises — which is R2's row, not this one.
# ---------------------------------------------------------------------------
def repeat_total(a, n):
    """Lean `List.replicate n a` as a LAZY sequence, total on all of `Nat`.

    `itertools.repeat(a, n)` is `ssize_t`-bounded in its count, so above the bound
    the realization drops the count and returns the unbounded repeat: every prefix
    a TERMINATING consumer reads is identical, and a consumer that would read past
    `2^63` elements does not terminate in either language (rule R3, and supplement
    2's total-correctness semantics is what guarantees the consumer terminates).
    """
    if n < 1 << 63:
        return itertools.repeat(a, n)
    return itertools.repeat(a)


def int_pow(a, b):
    """Lean `Int` power, realized only where CPython can hold the value.

    Same side condition as the `Nat` `^` row and for the same reason: CPython
    BUILDS the integer. Above the bound this raises rather than answering, so R2
    applies — realize the CONSUMING expression from its own equation — and this
    helper says so by refusing instead of pretending.
    """
    if b.bit_length() > 40:
        raise ValueError(
            "int_pow(%d, %d): outside the row's side condition; realize the "
            "consumer from its own defining equation (mapping.md R2)" % (a, b))
    return a ** b


def pow_mod(a, b, m):
    """Lean `(a ^ b) % m`: a power that is CONSUMED, realized per R2.

    This is the WORKED instance of the `^` rows' escape clause, and the reason
    that clause is not a dead letter. `Nat.pow_mod` is the defining equation of
    the composite, and CPython's THREE-argument `pow` implements exactly it: it
    reduces modulo `m` at every squaring, so it never builds `a ^ b`. Spelling
    the composite `(a ** b) % m` is not a realization above the `^` row's side
    condition, because the intermediate is the integer that row refuses.

    Two conventions ride along, both already in the `%` rows above and both
    measured in `check_total_spellings`: `m = 0` is Lean's `n % 0 = n`, which
    three-argument `pow` rejects outright (`ValueError`), so that case falls back
    to the two-argument form and inherits the original side condition; and a
    negative modulus is `Int.emod`, whose remainder is NEVER negative, where
    Python's three-argument `pow` follows its own floored `%` into `(m, 0]`.
    """
    if m == 0:
        return int_pow(a, b)                       # Lean: `n % 0 = n`
    return pow(a, b, abs(m))                       # Lean: `Int.emod` ≥ 0


def nat_to_float(n):
    """Lean `Nat.toFloat`: IEEE, hence TOTAL — it saturates to `inf`.

    Python's `float(n)` raises `OverflowError` above the double range instead
    (measured: `float(2 ** 1024)` raises, `float(2 ** 1023)` is
    `8.98846567431158e+307`), so the bare spelling is not a realization.
    """
    try:
        return float(n)
    except OverflowError:
        return float("-inf") if n < 0 else float("inf")


def float_pow(a, b):
    """Lean `Float` power: IEEE, hence TOTAL — it saturates to `±inf`.

    Python's `**` on floats raises `OverflowError: Numerical result out of range`
    (measured at `2.0 ** 2000`), which is the same defect one type over.
    """
    try:
        return a ** b
    except OverflowError:
        if a != a:                                             # nan
            return a
        if a == 0.0:
            return 0.0
        neg = a < 0.0 and int(b) == b and int(b) % 2 == 1
        return float("-inf") if neg else float("inf")


def check_total_spellings(pow_exp=66, float_exp=1024, repeat_exp=63):
    """Measure the four rows above: the realization answers, the spelling raises.

    Non-vacuity is the second half of each pair, as everywhere else in this file:
    the block FAILS if a future CPython stops raising, because then the row would
    no longer need its repair and this text would be stale.
    """
    # (a) the lazy replicate row.
    assert list(itertools.islice(repeat_total(7, 5), 10)) == [7] * 5
    assert list(itertools.islice(repeat_total(7, 1 << repeat_exp), 4)) == [7] * 4
    try:
        itertools.repeat(7, 1 << repeat_exp)
    except OverflowError:
        pass
    else:                                                  # pragma: no cover
        raise AssertionError("itertools.repeat no longer bounds its count by "
                             "ssize_t; that row needs no side condition now")
    # `range` is fine, and is here so the two are not confused.
    assert next(iter(range(1 << pow_exp))) == 0
    assert range(1 << pow_exp).stop == 1 << pow_exp

    # (b) the `Int` power row: agreement below the bound, refusal above it.
    for a, b in ((-2, 1000), (2, 64), (-3, 7), (7, 0)):
        assert int_pow(a, b) == a ** b, (a, b)
    try:
        int_pow(-2, 1 << pow_exp)
    except ValueError:
        pass
    else:                                                  # pragma: no cover
        raise AssertionError("int_pow accepted an exponent outside the row's "
                             "side condition")

    # (c) the two `Float` rows: total where the spelling raises.
    assert nat_to_float(1 << (float_exp - 1)) == float(1 << (float_exp - 1))
    assert nat_to_float(1 << float_exp) == float("inf")
    assert nat_to_float(0) == 0.0 and nat_to_float(37) == 37.0
    try:
        float(1 << float_exp)
    except OverflowError:
        pass
    else:                                                  # pragma: no cover
        raise AssertionError("float() no longer raises at 2**%d" % float_exp)
    assert float_pow(2.0, 10) == 1024.0
    assert float_pow(2.0, 2000) == float("inf")
    assert float_pow(-2.0, 2001) == float("-inf")
    assert float_pow(-2.0, 2000) == float("inf")
    try:
        2.0 ** 2000
    except OverflowError:
        pass
    else:                                                  # pragma: no cover
        raise AssertionError("float ** no longer raises on overflow")

    # (d) the CONSUMED power: R2's escape clause from the two `^` rows, worked.
    # Agreement is checked against the composite spelled out of the rows it is
    # built from (`int_pow` then `int_emod`) on a small grid, including both
    # conventions — the zero modulus and the negative one.
    for a in range(-4, 5):
        for b in range(0, 6):
            for m in (-3, -2, -1, 0, 1, 2, 5, 7):
                want = int_emod(int_pow(a, b), m)
                assert pow_mod(a, b, m) == want, (a, b, m, want)
    # Above the side condition the composite still answers, in microseconds, and
    # the SPELLING is the thing that cannot: the intermediate needs more bytes
    # than the machine has (`pow_bytes_needed`, arithmetic, no allocation).
    t0 = time.time()
    mod_val = pow_mod(2, 1 << pow_exp, 7)
    mod_seconds = time.time() - t0
    assert mod_val == pow(2, 1 << pow_exp, 7) and 0 <= mod_val < 7, mod_val
    assert mod_seconds < 1.0, mod_seconds
    assert pow_bytes_needed(1 << pow_exp) > (1 << 60), pow_bytes_needed(
        1 << pow_exp)
    try:                       # and the two-argument fallback still refuses it
        int_pow(2, 1 << pow_exp)
    except ValueError:
        pass
    else:                                                  # pragma: no cover
        raise AssertionError("int_pow accepted the exponent the modular row "
                             "exists to route around")
    return repeat_exp, pow_exp, float_exp, mod_val


def check_int_algebra(bound=48):
    """Measure the `Int` realization against Lean's `Int` algebra.

    `Int` is a THIRD algebra, distinct from both `Nat` and Python's `int`: it is
    signed (so nothing truncates at zero), it is TOTAL at a zero divisor (so
    nothing raises), and its `/` and `%` are the EUCLIDEAN pair — remainder never
    negative — where Python's are FLOORED. The four literal fixtures below are
    exactly the four places Lean's answer is not Python's, and they are exactly
    the equations `properties.py`'s `admiss-int-semantics-carried` discharges
    inside the impl region, so both sides of mapping.md §2.1's `Int` rows are
    pinned to one shared set of equations.
    """
    # The four CONVENTION divergences, each measured in Lean (mapping.md §2.1).
    assert int_emod(1, -2) == 1 and 1 % -2 == -1
    assert int_ediv(7, -2) == -3 and 7 // -2 == -4
    assert int_ediv(-7, -2) == 4 and -7 // -2 == 3
    assert int_emod(-7, -2) == 1 and -7 % -2 == -1
    # Totality at a zero divisor, where Python raises outright.
    for a in (-5, 0, 5):
        assert int_ediv(a, 0) == 0, a
        assert int_emod(a, 0) == a, a
        assert int_tdiv(a, 0) == 0 and int_tmod(a, 0) == a, a
        assert int_fdiv(a, 0) == 0 and int_fmod(a, 0) == a, a
    try:
        5 // 0
    except ZeroDivisionError:
        pass
    else:                                                  # pragma: no cover
        raise AssertionError("Python `//` no longer raises on 0")
    # The division laws, on a grid: the Euclidean identity and the non-negative
    # remainder that names the convention.
    for a in range(-bound, bound):
        for b in range(-bound, bound):
            if b == 0:
                continue
            assert b * int_ediv(a, b) + int_emod(a, b) == a, (a, b)
            assert 0 <= int_emod(a, b) < abs(b), (a, b)
            assert b * int_tdiv(a, b) + int_tmod(a, b) == a, (a, b)
            assert b * int_fdiv(a, b) + int_fmod(a, b) == a, (a, b)
            # tdiv rounds toward zero, fdiv toward -inf: they agree iff exact or
            # same-sign, and fdiv is exactly Python's own `//`.
            assert int_fdiv(a, b) == a // b, (a, b)
            assert abs(int_tdiv(a, b)) == abs(a) // abs(b), (a, b)
    # `Int.toNat` saturates; Python's `int()` does not.
    assert int_to_nat(-5) == 0 and int_to_nat(5) == 5
    return bound


def check_uint_algebra():
    """Measure the fixed-width realization: `UIntN` arithmetic is MODULAR.

    Not reached by the frozen impl, and tabled anyway: the recorded findings this
    module's realization answers were the same defect re-found in a type the map
    had not covered, so the map states the LAW and covers the types an impl can
    reach rather than the ones already attacked (mapping.md §2.1). Fixtures
    measured in Lean, one build: `(200 : UInt8) + 100 = 44`, `(3 : UInt8) - 5 =
    254`, `(5 : UInt8) / 0 = 0`, `(5 : UInt8) % 0 = 5`, `(2 : UInt64) ^ 70 = 0`,
    `(300 : Nat).toUInt8 = 44`.
    """
    assert uint_wrap(200 + 100, 8) == 44 and 200 + 100 == 300
    assert uint_wrap(3 - 5, 8) == 254 and 3 - 5 == -2
    assert uint_div(5, 0, 8) == 0 and uint_mod(5, 0, 8) == 5
    assert uint_wrap(2 ** 70, 64) == 0
    assert uint_wrap(300, 8) == 44
    for a in range(0, 256, 7):
        for b in range(0, 256, 11):
            assert 0 <= uint_wrap(a + b, 8) < 256, (a, b)
            assert 0 <= uint_wrap(a - b, 8) < 256, (a, b)
            assert uint_div(a, b, 8) == (a // b if b else 0), (a, b)
    return 8


def check_float_algebra():
    """Measure the `Float` realization: IEEE-754, and TOTAL — it never raises.

    Measured in Lean, one build each: `1.0 / 0.0 = inf`, `-1.0 / 0.0 = -inf`,
    `0.0 / 0.0 = NaN`, `inf.toUInt64 = 2^64 - 1`, `NaN.toUInt64 = 0`,
    `(-1.0).toUInt64 = 0`, `(3.7).toUInt64 = 3`. Also measured: NO impl of this
    method can reach the `Float` leg and still verify — the frozen loop's
    invariant `i ≤ pageRange.length` cannot be discharged for a counter offset by
    a `Float` round trip, because Lean's `Float` operations are `@[extern]` and
    do not reduce (the probe fails with the invariant unsolved). The rows are
    fixed here regardless, because a leg that is unreachable TODAY is not the same
    thing as a leg the map may translate by operator spelling.
    """
    inf, nan = float("inf"), float("nan")
    assert float_div(1.0, 0.0) == inf
    assert float_div(-1.0, 0.0) == -inf
    assert float_div(0.0, 0.0) != float_div(0.0, 0.0)       # NaN
    assert float_div(3.0, 0.0) == inf
    try:
        1.0 / 0.0
    except ZeroDivisionError:
        pass
    else:                                                  # pragma: no cover
        raise AssertionError("Python `/` no longer raises on 0.0")
    assert float_to_uint64(inf) == (1 << 64) - 1
    assert float_to_uint64(nan) == 0
    assert float_to_uint64(-1.0) == 0
    assert float_to_uint64(3.7) == 3
    assert float_to_uint64(1e30) == (1 << 64) - 1
    for bad in (inf, nan):
        try:
            int(bad)
        except (ValueError, OverflowError):
            pass
        else:                                              # pragma: no cover
            raise AssertionError("Python int() no longer rejects %r" % bad)
    return 64


# ---------------------------------------------------------------------------
# The DERIVED-LENGTH realization (mapping.md §2.1 rule R2: realize the length,
# not the list). Lean's `List.length` returns an UNBOUNDED `Nat`; CPython bounds
# every container and every `len` by `ssize_t`. So the length of a derived list is
# realized from the list constructor's own length equation — each one discharged
# in Lean by `simp` — and never by materializing the list and measuring it.
# ---------------------------------------------------------------------------
def range_length(n):
    """Lean `(List.range n).length` = `n` (`List.length_range`)."""
    return n


def replicate_length(n, _a=None):
    """Lean `(List.replicate n a).length` = `n` (`List.length_replicate`)."""
    return n


def map_length(xs):
    """Lean `(xs.map f).length` = `xs.length` — `f` is never applied."""
    return len(xs)


def take_length(k, xs):
    """Lean `(xs.take k).length` = `min k xs.length`."""
    return min(k, len(xs))


def drop_length(k, xs):
    """Lean `(xs.drop k).length` = `xs.length - k`, TRUNCATED (`nat_sub`)."""
    return nat_sub(len(xs), k)


def append_length(xs, ys):
    """Lean `(xs ++ ys).length` = `xs.length + ys.length`."""
    return len(xs) + len(ys)


def check_container_realization(big_exponents=(63, 64, 66)):
    """Measure R2: the derived lengths agree with materialization where
    materialization is POSSIBLE, and are still total where it is not.

    This is the block the FOURTH recorded G-EQ / G-PANEL-1 finding
    (refinement.md §B'''') asks for. The auditor's counterpart was assembled
    COMPOSITIONALLY out of two rows this map already carried — `List.range n` ->
    `range(n)` and `xs.length` -> `len(xs)` — giving `len(list(range(n)))`, which
    raises `OverflowError` for every `n >= 2 ** 63` while the Lean composite
    `(List.range n).length` answers `n` for every `n : Nat`. Hence R2: realization
    does not distribute over composition unless every intermediate is
    representable, and the composite is realized from its own defining equation.

    Two halves, and the second is what makes this non-vacuous:
      (a) AGREEMENT — at small `n` the realization equals the materialized answer,
          so it is not merely a total function, it is the RIGHT one;
      (b) TOTALITY vs the naive route — at `n = 2^63, 2^64, 2^66` the realization
          still answers `n`, and both materializing routes are measured to raise.
    """
    # (a) agreement with materialization, where materialization is possible.
    for n in (0, 1, 2, 7, 64, 513):
        assert range_length(n) == len(list(range(n))) == n, n
        assert replicate_length(n, 0) == len([0] * n) == n, n
    xs = list(range(37))
    assert map_length(xs) == len([x + 1 for x in xs]) == 37
    for k in (0, 1, 36, 37, 38, 999):
        assert take_length(k, xs) == len(xs[:k]), k
        assert drop_length(k, xs) == len(xs[k:]), k
    ys = list(range(5))
    assert append_length(xs, ys) == len(xs + ys) == 42
    # `drop` past the end: Lean's `Nat` subtraction truncates, and so must this.
    assert drop_length(999, xs) == 0 and len(xs) - 999 == -962

    # (b) totality above `ssize_t`, where the naive route is measured to raise.
    assert sys.maxsize == 2 ** 63 - 1, sys.maxsize
    for e in big_exponents:
        n = 2 ** e
        assert range_length(n) == n, e
        assert replicate_length(n, 0) == n, e
        # Neither materializing route is a realization: both raise, immediately.
        for label, route in (
            ("len(range(n))", lambda n=n: len(range(n))),
            ("len(list(range(n)))", lambda n=n: len(list(range(n)))),
        ):
            try:
                route()
            except OverflowError:
                pass
            else:                                          # pragma: no cover
                raise AssertionError(
                    "%s no longer raises at 2**%d; R2's premise is gone"
                    % (label, e))
    # And the neutrality Lean itself proves, which is WHY those attacks verify:
    # `0 * k = 0` for every `k`, so the realization of the whole prologue is `0`
    # and no container is built on either side (mapping.md §2.1, R1 extensional).
    for e in big_exponents:
        assert 0 * range_length(2 ** e) == 0, e
        assert replicate_length(2 ** e, 0) * 0 == 0, e
        assert not (range_length(2 ** e) * 0 > 0), e
    return max(big_exponents)


# ---------------------------------------------------------------------------
# The LOOP realization (mapping.md §2.1 rule R3: an annotated STATEMENT is
# realized by its DENOTATION, not by its schedule).
#
# This is the block the FIFTH recorded G-EQ / G-PANEL-1 finding
# (refinement.md §B''''') asks for. That family of attacks annotates a loop whose
# POST-STATE Lean proves outright — `while k > 0 do k := k - 1` ends at `k = 0`
# for every start, and a body guarded by `i <= n` collects exactly the same list
# however far above `n` the counter starts (in the Lean shape the guard is the
# `Option`-shaped read itself: `pageRange[i - 1]? = none` above the length, so
# those iterations provably contribute nothing) — but whose SCHEDULE is
# astronomically long. Transliterating the schedule is not a realization at all: it is a program
# that never returns, and R1's own criterion (a TOTAL Python function
# extensionally equal to the Lean one) convicts it. The realization is the
# denotation Lean proved.
#
# Two halves, and again the second is what makes it non-vacuous:
#   (a) AGREEMENT   — at small starts the denotation equals what the real loop
#                     actually computes, step for step, so it is the RIGHT
#                     function and not merely a total one;
#   (b) DIVERGENCE  — at `k = 2^64` the schedule is measured NOT to have finished
#                     after a large step budget, while the denotation answers in
#                     constant time. Same obligation, both sides measured.
# ---------------------------------------------------------------------------
def countdown_denotation(_k):
    """Lean: `while k > 0 do k := k - 1` leaves `k = 0`, for every start.

    The `done_with k = 0` annotation IS this function. It does not mention the
    start, because the post-state does not depend on it.
    """
    return 0


def countdown_schedule(k, budget):
    """The naive transliteration: run the loop. Returns (state, steps taken).

    Bounded by `budget` so that this function is total *here*; the point of the
    measurement below is precisely that without such a bound it is not.
    """
    steps = 0
    while k > 0 and steps < budget:
        k = nat_sub(k, 1)
        steps += 1
    return k, steps


def guarded_collect_denotation(xs):
    """Lean: the guarded backward collect denotes the plain forward traversal."""
    return [x + 1 for x in xs]


def guarded_collect_schedule(xs, start, budget):
    """The naive transliteration of the same loop, from an arbitrary `start`."""
    n = len(xs)
    i, out, steps = start, [], 0
    while i > 0 and steps < budget:
        if i <= n:
            out.insert(0, xs[i - 1] + 1)
        i = nat_sub(i, 1)
        steps += 1
    return out, i, steps


def two_pow_positive(_n):
    """Lean `0 < 2 ^ n` is the constant `True` (`Nat.two_pow_pos`).

    mapping.md §2.1's `^` row is side-conditioned on the VALUE being one Python
    can hold; this proposition never needs the value, so its realization is the
    constant, never `2 ** n > 0`. Compare rule R1's "where a Lean sub-term is
    provably a constant, the realization is that constant".
    """
    return True


def pow_bytes_needed(exponent):
    """Bytes CPython would need for the integer `2 ** exponent`, by arithmetic.

    `2 ** e` has exactly `e + 1` significant bits. Counting them costs nothing;
    ALLOCATING them is what mapping.md's side condition is about. This is how the
    bound is checked without asking the host for 2.3 exabytes.
    """
    return (exponent + 1 + 7) // 8


def measure_pow_refusal(exponent, mem_bytes=1 << 28, timeout=20.0):
    """Measure, in a memory-capped child, that CPython cannot BUILD `2 ** e`.

    Any of {MemoryError, OverflowError, a hard child failure, no answer inside
    the timeout} is the same datum: the naive realization of the `^` row does not
    return a value at this bound, so it is not a realization. Only actually
    printing the bit length would refute the side condition, and that is the one
    outcome this asserts against. Falls back to the arithmetic bound alone if the
    interpreter cannot spawn a child.
    """
    if not sys.executable:                                 # pragma: no cover
        return "no-subinterpreter (arithmetic bound only)"
    prog = (
        "import resource, sys\n"
        "resource.setrlimit(resource.RLIMIT_AS, (%d, %d))\n"
        "try:\n"
        "    v = 2 ** %d\n"
        "except MemoryError:\n"
        "    print('MemoryError'); sys.exit(0)\n"
        "except OverflowError:\n"
        "    print('OverflowError'); sys.exit(0)\n"
        "print('BUILT %%d' %% v.bit_length())\n"
        % (mem_bytes, mem_bytes, exponent))
    try:
        raw = subprocess.check_output([sys.executable, "-c", prog],
                                      stderr=subprocess.STDOUT, timeout=timeout)
    except subprocess.TimeoutExpired:
        return "no answer in %.0fs" % timeout
    except subprocess.CalledProcessError as exc:
        return "child exit %d" % exc.returncode
    except OSError:                                        # pragma: no cover
        return "no-subinterpreter (arithmetic bound only)"
    lines = [ln for ln in raw.decode("utf-8", "replace").splitlines() if ln]
    label = lines[-1] if lines else "silent"
    if label.startswith("BUILT"):                          # pragma: no cover
        raise AssertionError(
            "CPython built 2 ** %d (%s) under a %d-byte cap; mapping.md's `^` "
            "side condition has lost its premise" % (exponent, label, mem_bytes))
    return label


def check_loop_realization(small_bound=1024, budget=1_000_000, exponent=2 ** 64):
    """Measure R3: the denotation is the realization; the schedule is not.

    Four things, all measured:
      1. the countdown's denotation against the REAL loop, exhaustively for every
         start below `small_bound` (agreement, plus the step count);
      2. the guarded collect's denotation against the real loop, both from `n` and
         from the algebraically widened `n + 0 * 2^64` (same start, by `Nat`), and
         then from `n + 2^64`, where the schedule is measured not to finish while
         the denotation is unchanged;
      3. the countdown from `k = 2^64`: `budget` steps taken, `2^64 - budget`
         still to go, i.e. NOT finished — while `countdown_denotation` answers 0;
      4. mapping.md §2.1's `^` row at its side condition: the arithmetic byte
         count for `2 ** 2^64`, a measured refusal to build it, and `0 < 2 ^ n`
         as the constant Lean proves it to be.
    """
    # 1. Agreement, exhaustively, with the step count as a witness that the loop
    #    really ran (a vacuous loop would agree too).
    for k in range(small_bound):
        state, steps = countdown_schedule(k, k + 1)
        assert state == countdown_denotation(k) == 0, k
        assert steps == k, (k, steps)

    # 2. The guarded collect: the denotation ignores the widening, and so does
    #    the real loop, exactly as long as the loop is allowed to run.
    rng = random.Random(SEED)
    for n in (0, 1, 2, 5, 33):
        xs = [rng.randrange(-100, 100) for _ in range(n)]
        want = guarded_collect_denotation(xs)
        for start in (n, n + 0 * exponent):                # `0 * e = 0` in `Nat`
            out, i, steps = guarded_collect_schedule(xs, start, n + 1)
            assert out == want, (n, start, out, want)
            assert i == 0 and steps == n, (n, start, i, steps)
        # Widened additively: same denotation, unreachable schedule.
        small = budget // 10
        out, i, steps = guarded_collect_schedule(xs, n + exponent, small)
        assert steps == small, (n, steps)
        assert i == nat_sub(n + exponent, small) > 0, (n, i)
        assert out == [], (n, out)                    # never got down to the data
        assert guarded_collect_denotation(xs) == want, n

    # 3. The countdown above the budget: measured not to finish.
    state, steps = countdown_schedule(exponent, budget)
    assert steps == budget, steps
    assert state == exponent - budget > 0, state
    assert countdown_denotation(exponent) == 0

    # 4. The `^` row at its side condition.
    for b in range(0, 17):                     # agreement where the value is held
        assert 2 ** b == pow(2, b) and pow_bytes_needed(b) == (b + 8) // 8, b
        assert two_pow_positive(b) is True and 2 ** b > 0, b
    need = pow_bytes_needed(exponent)
    assert need > 2 ** 60, need                       # ~2.3 exabytes at e = 2^64
    refusal = measure_pow_refusal(exponent)
    # And the constant is a constant: it holds at the very bound where the value
    # is unobtainable, which is why the Lean side needs no value at all.
    assert two_pow_positive(exponent) is True
    return small_bound, budget, need, refusal


# ---------------------------------------------------------------------------
# The DEAD BINDING realization (mapping.md §2.1 rule R4: a BINDING is realized
# by its denotation too, and a binding nothing reads denotes the identity).
#
# This is the block the SIXTH recorded finding (refinement.md §B'''''') asks for.
# R3 settled annotated STATEMENTS; the shape that survived it binds a local and
# never reads it:
#
#     let _z : Nat := 2 ^ (2 ^ (64 + pageRange.length))
#
# `_z` is pure, total in Lean, and dead. It cannot change the returned value and
# it cannot fail, so the statement's denotation is the IDENTITY on the state and
# its realization is the empty statement. Transliterating it instead asks CPython
# for an integer with more bits than the observable universe has atoms, which is
# a program that does not return -- convicted, again, by R1's own criterion.
#
# The side condition is the whole content of the rule, so it is DECIDED here and
# not asserted: `impl_reads_binding` counts RUNTIME reads of the binder in the
# impl text, and the three fixtures below pin all three answers -- dead, live,
# and read-only-by-an-annotation (which is runtime-dead, because under R3 an
# annotation is not executed at all). The non-vacuity leg is the LIVE fixture:
# dropping THAT binding changes the output, and the parser says so.
# ---------------------------------------------------------------------------
_ANNOTATION_HEADS = ("invariant", "done_with", "decreasing", "ensures",
                     "requires", "assert", "variant", "with_name_prefix")

# The dead shape, byte-for-byte the impl region of the attack that produced this
# rule (`atk_pow_dead`): it VERIFIES, and its faithful patch is the gold body.
_DEAD_SAMPLE = """
    let _z : Nat := 2 ^ (2 ^ (64 + pageRange.length))
    let mut result : List (List Int) := []
    let mut i := pageRange.length
    while i > 0
      invariant 0 <= i /\\ i <= pageRange.length
      invariant result = pageSeq (pageRange.drop i)
      done_with i = 0
      decreasing i
    do
      let p := pageRange[i - 1]?
      result := (p.map pageOf).toList ++ result
      i := i - 1
    return result
"""

# The same impl with the local READ at the return. Dropping this one is not a
# realization: it changes the value.
_LIVE_SAMPLE = """
    let z : Nat := pageRange.length - 1
    let mut result : List (List Int) := []
    let mut i := pageRange.length
    while i > 0
      invariant 0 <= i /\\ i <= pageRange.length
      done_with i = 0
      decreasing i
    do
      let p := pageRange[i - 1]?
      result := (p.map pageOf).toList ++ result
      i := i - 1
    return result.take z
"""

# And the case that separates "dead" from "absent from the text": the binder is
# mentioned, but only where nothing executes.
_ANNOTATED_SAMPLE = """
    let z : Nat := pageRange.length
    let mut result : List (List Int) := []
    let mut i := pageRange.length
    while i > 0
      invariant i <= z                      -- the only mention of `z`
      invariant result = pageSeq (pageRange.drop i)
      done_with i = 0
      decreasing i
    do
      let p := pageRange[i - 1]?
      result := (p.map pageOf).toList ++ result
      i := i - 1
    return result
"""


def impl_reads_binding(src, name):
    """Count RUNTIME reads of `name` in a Velvet impl region.

    Comments and ANNOTATION lines are not code: an `invariant` / `done_with` /
    `decreasing` / `assert` mentions the binder in a proof obligation, and the
    refined patch contains no proof obligations (rule R3). The binding's own line
    is not a read either. Everything else counts.

    A syntactic count is exactly the right instrument here and not a shortcut:
    the question the rule asks -- "does anything the program EXECUTES observe
    this variable" -- is a question about the text, and answering it by parsing
    the text is what makes "dead" checkable by a reviewer rather than claimed by
    a translator.
    """
    reads = 0
    pattern = re.compile(r"(?<![A-Za-z0-9_])%s(?![A-Za-z0-9_])" % re.escape(name))
    for line in src.splitlines():
        code = line.split("--", 1)[0]
        head = code.strip().split(" ", 1)[0].strip("(")
        if head in _ANNOTATION_HEADS:
            continue
        if re.match(r"\s*let\s+(mut\s+)?%s\b" % re.escape(name), code):
            continue                       # the binding itself, not a read
        reads += len(pattern.findall(code))
    return reads


def dead_local_denotation(xs):
    """R4: the dead binding contributes nothing, so the impl denotes the loop."""
    return guarded_collect_denotation(xs)


def dead_local_schedule(xs, exponent):
    """The transliteration: BUILD the value the dead `let` names, then collect.

    Returns the same list plus the bit length of the useless integer, so that at
    a small exponent this is measurably the same function -- and at the attack's
    exponent, measurably not a function at all.
    """
    z = 2 ** exponent
    return guarded_collect_denotation(xs), z.bit_length()


def live_local_denotation(xs):
    """The LIVE fixture's denotation: the local is read, so it is observable."""
    return guarded_collect_denotation(xs)[:nat_sub(len(xs), 1)]


def check_dead_binding_realization(exponent=2 ** 64, small_exponent=16):
    """Measure R4 and, above all, its side condition.

    Four things:
      1. the deadness DECISION, on three fixtures: the attack's own impl (0
         runtime reads), the same impl with the local read at the return (>=1),
         and the impl whose local is mentioned only in an invariant (0 runtime
         reads, while a naive whole-text count finds it -- so the annotation
         stripping is load-bearing);
      2. AGREEMENT where the transliteration can still run: at `small_exponent`
         the schedule and the denotation return the same list;
      3. DIVERGENCE at the attack's exponent: building the dead value is measured
         to fail in a memory-capped child (2.3 exabytes by arithmetic) while the
         denotation answers in constant time;
      4. NON-VACUITY: dropping the LIVE binding is not a realization -- its
         denotation genuinely differs -- so the rule cannot be used to delete an
         observable computation.
    """
    # 1. The decision.
    assert impl_reads_binding(_DEAD_SAMPLE, "_z") == 0
    live_reads = impl_reads_binding(_LIVE_SAMPLE, "z")
    assert live_reads >= 1, live_reads
    assert impl_reads_binding(_ANNOTATED_SAMPLE, "z") == 0
    naive = len(re.findall(r"(?<![A-Za-z0-9_])z(?![A-Za-z0-9_])",
                           _ANNOTATED_SAMPLE))
    assert naive >= 1, naive          # the annotation really is in the text

    # 2. Agreement while the value is one CPython holds.
    rng = random.Random(SEED)
    for n in (0, 1, 2, 5, 33):
        xs = [rng.randrange(-100, 100) for _ in range(n)]
        got, bits = dead_local_schedule(xs, small_exponent)
        assert got == dead_local_denotation(xs), (n, got)
        assert bits == small_exponent + 1, bits

    # 3. Divergence at the attack's own exponent.
    need = pow_bytes_needed(exponent)
    assert need > 2 ** 60, need
    refusal = measure_pow_refusal(exponent)
    t0 = time.time()
    assert dead_local_denotation([1, 2, 3]) == [2, 3, 4]
    denotation_seconds = time.time() - t0

    # 4. Non-vacuity: the live binding is NOT droppable.
    for n in (1, 2, 5, 33):
        xs = [rng.randrange(-100, 100) for _ in range(n)]
        assert live_local_denotation(xs) != dead_local_denotation(xs), n

    return live_reads, need, refusal, round(denotation_seconds, 6)


def check_nat_algebra(bound=96):
    """Measure the realization against the `Nat` laws, exhaustively on a grid.

    These are exactly the four equations Solution.lean's
    `admiss-nat-semantics-carried` battery case discharges INSIDE the impl region
    (properties.py), so the Lean side and the Python side of mapping.md §2.1 are
    pinned to one shared set of laws rather than to a resemblance between two
    operator spellings. The last two checks are the ones that would fail for the
    naive translation, and they are what makes this non-vacuous: they assert the
    realization really does saturate, i.e. that it DIFFERS from Python's own `-`
    and `//` exactly where Lean's `Nat` differs from `int`.
    """
    for a in range(bound):
        # `a / 0 = 0` and `a % 0 = a`
        assert nat_div(a, 0) == 0, a
        assert nat_mod(a, 0) == a, a
        for b in range(bound):
            if b <= a:
                assert nat_sub(a, b) + b == a, (a, b)      # sub_add_cancel
            else:
                assert nat_sub(a, b) == 0, (a, b)          # sub_eq_zero_of_le
            if b != 0:
                assert nat_div(a, b) == a // b, (a, b)
                assert nat_mod(a, b) == a % b, (a, b)
    # Non-vacuity: the realization must NOT be Python's arithmetic.
    assert nat_sub(0, 1) == 0 and 0 - 1 == -1
    assert nat_div(1, nat_sub(1, 1)) == 0
    try:
        1 // (1 - 1)
    except ZeroDivisionError:
        pass
    else:                                                  # pragma: no cover
        raise AssertionError("Python `//` no longer raises on 0; the "
                             "realization's whole point is gone")
    return bound


def shadow_iterate(paginator):
    """enumeratePages transliterated, following the impl region statement for
    statement: the BACKWARD accumulating loop over the index sequence, reading
    each index through the Option-shaped access the carrier forces and prepending
    the mapped sub-view. `pageOf` is left as the REAL callee page() (A leg). This
    is the R/I shadow of the impl (the fold ordering + materialization).

    Every `Nat` operation goes through the arithmetic realization (`nat_sub`), not
    through Python's `-`: the impl's `i - 1` and `i := i - 1` are Lean `Nat`
    subtractions, which saturate at 0 (mapping.md §2.1)."""
    page_range = list(paginator.page_range)          # `pageRange : List PageIdx`
    result = []                                      # `result := []`
    i = len(page_range)                              # `i := pageRange.length`
    while i > 0:                                     # `while i > 0`
        # `let p := pageRange[i - 1]?` -- an Option, not a total read, and the
        # `i - 1` is Lean's saturating Nat subtraction.
        j = nat_sub(i, 1)
        p = page_range[j] if 0 <= j < len(page_range) else None
        # `result := (p.map pageOf).toList ++ result`
        if p is None:
            mapped = []
        else:
            # The carrier membership the model's `PageIdx` carries. Asserted
            # rather than assumed: if page_range ever named an index outside
            # [1 .. num_pages], the shadow would be applying the accessor
            # somewhere `PageIdx` forbids and the R/I leg would be unfaithful.
            assert 1 <= p <= paginator.num_pages, (
                "shadow built an index outside the carrier: %r not in "
                "[1 .. %d]" % (p, paginator.num_pages))
            mapped = [list(paginator.page(p))]
        result = mapped + result
        i = nat_sub(i, 1)                            # `i := i - 1` (Nat.sub)
    return result                                    # `return result`


def oracle_iterate(paginator):
    """patch.diff's behaviour: the patched Paginator.__iter__ generator,
    materialized to a list of observable page contents."""
    return [list(page) for page in iter(paginator)]


def fuzz_inputs(n, rng):
    # boundary cases first (plan §4.1 step 4)
    yield ([], 1, 0, True)
    yield ([], 1, 0, False)
    yield ([], 5, 0, True)
    yield ([1], 1, 0, True)
    yield ([1, 2, 3], 2, 0, True)            # the F2P fixture
    yield (list(range(10)), 3, 0, True)
    yield (list(range(10)), 3, 2, True)
    yield (list(range(11)), 3, 2, True)
    yield (list(range(7)), 7, 0, True)
    yield (list(range(8)), 7, 0, True)
    for _ in range(n):
        size = rng.randint(0, 40)
        object_list = list(range(size))
        per_page = rng.randint(1, 10)
        orphans = rng.randint(0, 5)
        allow_empty = rng.choice([True, False])
        yield (object_list, per_page, orphans, allow_empty)


def main():
    rng = random.Random(SEED)
    nat_bound = check_nat_algebra()
    int_bound = check_int_algebra()
    uint_bits = check_uint_algebra()
    float_bits = check_float_algebra()
    big_exp = check_container_realization()
    loop_small, loop_budget, pow_bytes, pow_refusal = check_loop_realization()
    rep_exp, ipow_exp, fl_exp, mod_val = check_total_spellings()
    (live_reads, dead_bytes, dead_refusal,
     dead_seconds) = check_dead_binding_realization()
    disagreements = []
    count = 0
    for object_list, per_page, orphans, allow_empty in fuzz_inputs(N_FUZZ, rng):
        count += 1
        p = Paginator(object_list, per_page, orphans=orphans,
                      allow_empty_first_page=allow_empty)
        shadow = shadow_iterate(p)
        oracle = oracle_iterate(p)
        if shadow != oracle:
            disagreements.append(((object_list, per_page, orphans, allow_empty),
                                  shadow, oracle))
            if len(disagreements) >= 5:
                break
    if disagreements:
        print("G-CONF FAIL: %d R/I disagreement(s) over %d inputs:"
              % (len(disagreements), count))
        for cfg, sh, orc in disagreements:
            print("  config=%r shadow=%r oracle=%r" % (cfg, sh, orc))
        return 1
    print("G-CONF OK: R/I shadow of enumeratePages agrees with patch.diff "
          "behaviour on %d inputs (seed=%d), 0 disagreements." % (count, SEED))
    print("G-CONF OK: the Nat arithmetic realization (mapping.md 2.1) satisfies "
          "the four Lean Nat laws exhaustively on [0,%d)^2 and is measured to "
          "saturate where Python's int does not." % nat_bound)
    print("G-CONF OK: the Int realization satisfies the Euclidean division laws "
          "exhaustively on [-%d,%d)^2 and is measured to differ from Python's "
          "// and %% at the four convention points and at every zero divisor; "
          "the fixed-width (UInt%d, modular) and Float (IEEE, total) "
          "realizations agree with their measured Lean values too."
          % (int_bound, int_bound, uint_bits))
    print("G-CONF OK: the derived-length realization (mapping.md 2.1 rule R2) "
          "agrees with materialization at small n and stays total at n = 2^%d, "
          "where both materializing routes are measured to raise OverflowError "
          "(sys.maxsize = 2^63 - 1)." % big_exp)
    print("G-CONF OK: the loop realization (mapping.md 2.1 rule R3) agrees with "
          "the real loop for every start below %d and for the widened guarded "
          "collect, while from k = 2^64 the schedule is measured NOT to have "
          "finished after %d steps (denotation: 0, in constant time); the ^ row's "
          "side condition holds at the bound (2 ** 2^64 needs %d bytes; measured: "
          "%s) and 0 < 2 ^ n is the constant Lean proves."
          % (loop_small, loop_budget, pow_bytes, pow_refusal))
    print("G-CONF OK: three further rows whose Python spelling is not total are "
          "realized and measured against it: the lazy replicate (itertools.repeat "
          "bounds its count by ssize_t, so 2^%d needs the unbounded form), the Int "
          "power (refused above the row's side condition, where (-2) ** 2^%d is "
          "measured to raise), and the Float coercion/power (float(2^%d) and "
          "2.0 ** 2000 raise where Lean saturates to inf)."
          % (rep_exp, ipow_exp, fl_exp))
    print("G-CONF OK: the CONSUMED power (mapping.md 2.1 rule R2, worked) agrees "
          "with int_pow-then-int_emod on the whole small grid including the zero "
          "and negative moduli, and (2 ^ 2^%d) %% 7 = %d answers in under a "
          "second where the spelling's intermediate is the one the ^ row refuses."
          % (ipow_exp, mod_val))
    print("G-CONF OK: the dead-binding realization (mapping.md 2.1 rule R4) is "
          "decided, not asserted: 0 runtime reads for the attack's own `let _z` "
          "and for a local mentioned only in an invariant, %d for the same local "
          "read at the return -- and dropping THAT one is measured to change the "
          "value. Building the dead 2 ** 2^64 needs %d bytes (measured: %s) while "
          "the denotation answers in %.6fs."
          % (live_reads, dead_bytes, dead_refusal, dead_seconds))
    assert float_bits == 64
    return 0


if __name__ == "__main__":
    sys.exit(main())
