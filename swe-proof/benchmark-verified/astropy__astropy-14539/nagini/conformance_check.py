#!/usr/bin/env python3
"""G-CONF differential conformance check for astropy__astropy-14539 (nagini).

Refutes (never proves) the refinement leg no other gate covers: does the MODEL
of `model.py` agree with the REAL gold-patched repository code it claims to
model? The gate applies `patch.diff` to /testbed and sets `PYTHONPATH` before
this script runs, so the oracle below is a CALL INTO THE PATCHED REPO.


SHADOW (provenance "direct" — on nagini the model IS Python)
------------------------------------------------------------
The `# impl-start` / `# impl-end` regions of model.py's three functions, copied
VERBATIM with only the contract calls deleted (`Requires`, `Ensures`,
`Invariant`, `Assert`, `MustTerminate`, `Acc`, and the
`# invariants-start`/`-end` markers). Nothing renamed, nothing restructured,
both comparator bodies kept as two separate byte-identical copies exactly as
model.py has them (a merged "they're the same anyway" shadow would test the
merge, not the model):

  * `count_differing_rows(fmt, row_mismatches)` — the dispatcher; its impl
    region is the ONLY place the gold patch's behaviour lives
    (`is_vla_descriptor(ToSeq(fmt))` selects the comparator).
  * `compare_row_aware(fmt, row_mismatches)`   — the row-aware comparator body.
  * `compare_elementwise(fmt, row_mismatches)` — the element-wise comparator body.

Their dependencies come across too, contracts stripped: the whole
`# pure-start`/`# pure-end` region (`contains_cp`, `is_vla_descriptor`,
`row_granular_count`) and a `PSeq` / `ToSeq` shim realizing the Nagini carriers
as an immutable tuple sequence (`take`/`drop`/`+`/`len`/`[]`/`==`). The impl
regions call `is_vla_descriptor` -> `contains_cp`; `row_granular_count` is the
postcondition's fold and is checked as a SECOND leg (see "Two legs" below).
This bundle consumes NO `@ContractOnly` axiom (model.py's `axioms` region is
empty), so there is no axiomatized body to stand in for.


ORACLE — CALLED, not transliterated
-----------------------------------
mapping.md §1 binds `count_differing_rows` to the per-column body of
`TableDataDiff._diff` (`astropy/io/fits/diff.py:1429-1465`; the changed `elif`
at 1452, the `diff_total += len(set(diffs[0]))` accumulation at 1465). That is
driven directly:

    ta = fits.BinTableHDU.from_columns([fits.Column("K", format=fmt, array=a)])
    tb = fits.BinTableHDU.from_columns([fits.Column("K", format=fmt, array=b)])
    TableDataDiff(ta.data, tb.data, numdiffs=0).diff_total

The tables carry exactly ONE common column, so `diff_total` IS that column's
contribution — precisely the quantity `count_differing_rows` returns. Nothing
about the comparison is re-authored here: the format test, the route choice, the
per-row `np.allclose`, the `np.where`, and the `len(set(...))` accumulation are
all the patched repo's own code. Replacing `elif "P" in col.format or "Q" in
col.format` with anything else changes this oracle, which is the whole point.

`numdiffs=0` is passed only to skip the `diff_values` bookkeeping loop
(diff.py:1467-1485); it runs strictly AFTER `diff_total += len(set(diffs[0]))`
and cannot affect the modeled quantity.

The oracle is allowed to RAISE, and a raise is recorded as a disagreement
(the shadow always returns a count). That is not defensive noise — it is the
observable the patch is about, and it is what makes this check capable of
failing: run unpatched, the `QJ(2)` boundary inputs send a Q-marked
variable-length column down `np.where(arra != arrb)` on an object array of
multi-element sub-arrays, which raises `ValueError: The truth value of an array
with more than one element is ambiguous`. Confirmed: with `apply_gold=False`
this script reports disagreements and exits 1; with the gold patch it exits 0.


TYPE BRIDGE (mapping.md §2, inverted)
-------------------------------------
The model works over abstract carriers; the real function wants a real FITS
column pair. Both directions are explicit, and BOTH are read back off the REAL
materialized data so that FITS's own padding/truncation/dtype choices can never
manufacture a spurious disagreement:

  * `col.format` (a `str`) -> `fmt: List[int]` of Unicode code points:
    `fmt = [ord(c) for c in str(ta.columns["K"].format)]`, i.e. the code points
    of the format string the real `col.format` test reads ('P' = 80, 'Q' = 81).
    The generator picks a format STRING; the code-point list is derived from the
    constructed column's own `format` attribute, not from the requested string.
  * the two columns -> `row_mismatches: List[int]`: `row_mismatches[i]` is the
    number of positions at which the two stored values in row i disagree, at the
    constructor's default exact tolerances `rtol=atol=0.0` (diff.py:221-222),
    where closeness degenerates to agreement at every aligned position:
    `int(np.count_nonzero(np.asarray(arra[i]) != np.asarray(arrb[i])))`
    computed from `arra = ta.data["K"]`, `arrb = tb.data["K"]` — the very arrays
    `_diff` binds at diff.py:1445-1446. The comparison is left to align the two
    stored values exactly as the real row comparator's `np.allclose` aligns them,
    so a length difference is NOT by itself counted as a difference, and a pair
    with no alignment at all raises here just as it does there (that row is out
    of domain). Same grounding as axiom_check.py's `row_mismatches_of`.

Generation runs in the concrete direction (build a real column pair, then
abstract it), so every input is a genuine FITS column AND, by construction,
satisfies `count_differing_rows`'s `Requires` (the only data precondition is
`row_mismatches[k] >= 0`, and a count of positions is non-negative).


TWO LEGS — impl and postcondition, both against the real function
-----------------------------------------------------------------
Each input is checked twice:
  (I) the copied impl region's return value       == real `diff_total`
  (S) the postcondition's fold
      `row_granular_count(ToSeq(row_mismatches))` == real `diff_total`
Leg (S) is what G-VERIFY proves the impl equal to, so pinning it to the real
function too means a green G-CONF underwrites the spec, not just the code.


INPUT DOMAIN — every restriction is a branch the model does not model or a
documented bound, never a detour around the patched behaviour
--------------------------------------------------------------------------
The domain is NOT finite (row counts and stored values are unbounded), so it is
fuzzed to the required count after the boundary list.

  * `nrows_a == nrows_b`, and either both 0 or both > 0. With unequal row counts
    `_diff` sets `diff_rows` and RETURNS before the column loop
    (diff.py:1409-1411), so the modeled per-column body never runs and there is
    no oracle. Both-zero is kept as a boundary (early return at 1415-1416, and
    the model's empty-`row_mismatches` case, both 0).
  * non-VLA columns whose materialized dtype is FLOATING (`E`, `D`, `2E`, ...)
    are excluded. Those take the *earlier, unchanged* branch
    `np.issubdtype(arra.dtype, np.floating) and ... -> where_not_allclose(...)`
    (diff.py:1447-1451), which is upstream of the patched `elif` — such a column
    never reaches line 1452 in EITHER the pre- or post-patch code, so it carries
    zero information about the behaviour under specification, and model.py's
    `compare_elementwise` binds specifically to the `else` body
    `np.where(arra != arrb)` (diff.py:1462-1463), not to `where_not_allclose`.
    Variable-length FLOAT columns (`PD`/`QD`/`PE`/`QE`) have `object` dtype, so
    they are NOT excluded and are exercised heavily — including NaN and inf,
    where the row-aware `np.allclose` and the bridge's `!=` agree (`allclose`
    reports NaN-vs-NaN as not close, `!=` reports it as a mismatch; equal infs
    are close and `!=`-equal).
  * variable-length columns whose two stored sub-arrays in some row have
    DIFFERENT lengths are IN-DOMAIN whenever those lengths still align
    positionally. The real row-aware comparator judges such a row by that
    alignment, so a length difference is not by itself a difference (e.g. a
    width-1 row against a width-2 row of the same value reports NO difference),
    and `row_mismatches_of` grounds the summary under the very same alignment.
    Only a row whose two stored values cannot be aligned at all is out: there
    the real `np.allclose` raises (`operands could not be broadcast together
    with shapes (2,) (3,)`), so the patched code has no defined value, and the
    input is skipped and counted (`n_skipped_ragged`), never silently dropped.
    Rows ragged *across* rows (the issue's own `QD` repro, `[[0.0], [0.0,
    0.0]]`) are likewise fully in-domain and pinned in the boundary list.
  * character variable-length columns (`PA`/`QA`) are excluded: the real
    row-aware comparator raises `DTypePromotionError` on bytes (numpy cannot
    promote them for the closeness arithmetic), so the patched code has no
    defined value there. Ordinary (non-VLA) character columns `A`/`5A`/`10A`
    ARE included — they must take the element-wise route and they agree.
  * stored values kept in ranges every FITS type accepts (0..7 for `B`/`L`/`X`
    and variable-length `B`/`L`, signed small ints elsewhere) so column
    construction succeeds.

NON-VACUITY, enforced at runtime (the run FAILS if any of these is 0)
--------------------------------------------------------------------
  * both dispatcher branches taken (`n_vla` > 0 and `n_nonvla` > 0);
  * inside each comparator, both the `row_mismatches[i-1] > 0` and the
    `<= 0` paths taken, and the zero-trip loop (`nrows == 0`) reached;
  * at least one column where a naive ELEMENT SUM would diverge from the row
    count (`sum(row_mismatches) > diff_total`), on each route separately, so the
    row-granular discipline is genuinely distinguished from an element-granular
    one rather than coincidentally equal;
  * at least one column with a Q descriptor and no P (`n_q_only` > 0) and one
    with a P and no Q, so the widened predicate is exercised in both halves.

>= 1e5 inputs: 36 boundary columns + fuzz to a checked total of 100_000,
pinned seed SEED = 14539 (recorded in mapping.md § G-CONF). Exit 0 iff zero
disagreements; on a disagreement the input, the shadow value and the oracle
value are printed and the exit code is 1. stdlib + numpy + the astropy under
test only (hypothesis is not needed — the generator is a seeded `random.Random`,
which keeps the verdict reproducible from the pinned seed alone).
"""
import json
import random
import sys

import numpy as np
from astropy.io import fits
from astropy.io.fits.diff import TableDataDiff

SEED = 14539
N_TARGET = 100_000


# ---------------------------------------------------------------------------
# Nagini carrier shims: PSeq is an immutable sequence, ToSeq materializes one.
# ---------------------------------------------------------------------------

class PSeq:
    __slots__ = ("_t",)

    def __init__(self, *items):
        self._t = tuple(items)

    @classmethod
    def _wrap(cls, t):
        s = cls()
        s._t = tuple(t)
        return s

    def take(self, n):
        return PSeq._wrap(self._t[:n])

    def drop(self, n):
        return PSeq._wrap(self._t[n:])

    def __add__(self, other):
        return PSeq._wrap(self._t + other._t)

    def __len__(self):
        return len(self._t)

    def __getitem__(self, i):
        return self._t[i]

    def __eq__(self, other):
        return isinstance(other, PSeq) and self._t == other._t

    def __hash__(self):
        return hash(self._t)


def ToSeq(lst):
    return PSeq._wrap(lst)


# ---------------------------------------------------------------------------
# model.py `# pure-start` / `# pure-end` region, VERBATIM (it has no contracts).
# ---------------------------------------------------------------------------

def contains_cp(s, cp):
    """True iff the code point `cp` occurs in the sequence `s`. Front-recursive
    so a single unfold is available per loop step."""
    if len(s) == 0:
        return False
    return s[0] == cp or contains_cp(s.drop(1), cp)


def is_vla_descriptor(fmt):
    """True iff the layout string carries either of the two designators of
    variable-length storage (80 or 81)."""
    return contains_cp(fmt, 80) or contains_cp(fmt, 81)


def row_granular_count(m):
    """The number of rows that have at least one differing element.
    Front-recursive so a single unfold is available per loop step."""
    if len(m) == 0:
        return 0
    head = 1 if m[0] > 0 else 0  # type: int
    return head + row_granular_count(m.drop(1))


# ---------------------------------------------------------------------------
# Branch-coverage counters. The shadow bodies below are byte-faithful copies of
# the impl regions; coverage is observed from OUTSIDE (never by editing the
# copied code) in `check_one`.
# ---------------------------------------------------------------------------
COV = {
    "vla_route": 0, "nonvla_route": 0,
    "row_aware_diff_row": 0, "row_aware_same_row": 0, "row_aware_empty": 0,
    "elementwise_diff_row": 0, "elementwise_same_row": 0, "elementwise_empty": 0,
    "vla_element_sum_diverges": 0, "nonvla_element_sum_diverges": 0,
    "q_only": 0, "p_only": 0,
    "unequal_length_aligning": 0,
    "wide_magnitude": 0, "wide_magnitude_unresolved": 0,
}


# ---------------------------------------------------------------------------
# SHADOW: model.py `compare_row_aware` impl region, verbatim, contracts stripped.
# ---------------------------------------------------------------------------

def compare_row_aware(fmt, row_mismatches):
    total = 0
    i = len(row_mismatches)
    while i > 0:
        if row_mismatches[i - 1] > 0:
            total = total + 1
        i = i - 1
    return total


# ---------------------------------------------------------------------------
# SHADOW: model.py `compare_elementwise` impl region, verbatim, contracts
# stripped. Kept as a SEPARATE copy exactly as model.py has it.
# ---------------------------------------------------------------------------

def compare_elementwise(fmt, row_mismatches):
    total = 0
    i = len(row_mismatches)
    while i > 0:
        if row_mismatches[i - 1] > 0:
            total = total + 1
        i = i - 1
    return total


# ---------------------------------------------------------------------------
# SHADOW: model.py `count_differing_rows` impl region, verbatim, contracts
# stripped. This is where the behaviour under specification lives.
# ---------------------------------------------------------------------------

def count_differing_rows(fmt, row_mismatches):
    # The layout descriptor selects the applicable comparator. A column that is
    # recognised as holding variable-length sub-arrays must use the row-aware
    # comparator; only a column NOT so recognised may use the element-wise one.
    if is_vla_descriptor(ToSeq(fmt)):
        total = compare_row_aware(fmt, row_mismatches)
    else:
        total = compare_elementwise(fmt, row_mismatches)
    return total


# ---------------------------------------------------------------------------
# Type bridge (mapping.md §2, inverted): real FITS column pair -> carriers.
# ---------------------------------------------------------------------------

def to_cps(fmt_str):
    """`col.format` (str) -> `fmt: List[int]` of Unicode code points."""
    return [ord(c) for c in fmt_str]


def build_columns(fmt_str, a, b):
    """Build the two REAL one-column tables the oracle is driven on."""
    ta = fits.BinTableHDU.from_columns(
        [fits.Column("K", format=fmt_str, array=a)])
    tb = fits.BinTableHDU.from_columns(
        [fits.Column("K", format=fmt_str, array=b)])
    return ta, tb


def row_mismatches_of(arra, arrb, vla):
    """The two columns -> `row_mismatches: List[int]`, grounded in the REAL
    materialized arrays `_diff` binds (diff.py:1445-1446): per row, the number of
    element positions the per-position verdict of the comparator APPLICABLE to
    this column rejects, at the default tolerances rtol=atol=0.0.

    The two real branches do NOT share a per-position verdict, so the grounding
    is branch-relative:

      * row-aware branch (`vla`): the verdict is `np.isclose` at the default
        tolerances, since the real comparator's `np.allclose` IS the conjunction
        of `np.isclose` over the aligned positions. It is deliberately NOT
        `x != y`: closeness is evaluated in a fixed-precision arithmetic whose
        significand is narrower than the 64-bit integer range, so at and above
        2**53 it cannot separate neighbouring values that `!=` separates. An
        exact-inequality grounding would summarise differing rows the real
        comparator calls identical — precisely the 64-bit regime the `Q`
        descriptor exists to carry.
      * element-wise branch: the verdict is the plain inequality `arra != arrb`
        the real `np.where` path applies to the regular ndarray column.

    The count uses the SAME positional alignment the real row comparator uses
    (numpy's own), so a length difference is not by itself a difference: two
    stored values of unequal length that still align agree iff every aligned
    position agrees. Returns None only when some row's two stored values cannot
    be aligned at all — there the real comparator raises, so the row lies
    outside the comparison's domain and has no summary."""
    out = []
    for i in range(len(arra)):
        x = np.asarray(arra[i])
        y = np.asarray(arrb[i])
        try:
            if vla:
                out.append(int(np.count_nonzero(
                    ~np.isclose(x, y, rtol=0.0, atol=0.0))))
            else:
                out.append(int(np.count_nonzero(x != y)))
        except ValueError:
            return None
        except TypeError:
            # A non-numeric (character) column: closeness is undefined there and
            # the real comparator raises too. Out of domain, no summary.
            return None
    return out


# ---------------------------------------------------------------------------
# ORACLE: the real gold-patched per-column comparison, CALLED.
# ---------------------------------------------------------------------------

def oracle(ta, tb):
    """The patched `TableDataDiff._diff` per-column body (diff.py:1429-1465)
    driven on the one-column tables: `diff_total` is that single column's
    contribution. Returns ("ok", n) or ("raise", repr) — a raise is a
    disagreement, not a skip (the shadow always returns a count)."""
    try:
        return ("ok", int(TableDataDiff(ta.data, tb.data, numdiffs=0).diff_total))
    except Exception as e:                      # noqa: BLE001 - observable
        return ("raise", "%s: %s" % (type(e).__name__, e))


# ---------------------------------------------------------------------------
# Domain predicate: is this materialized column pair inside what model.py
# models? (Every exclusion is justified in the module docstring.)
# ---------------------------------------------------------------------------

def in_modeled_domain(fmt_cps, arra, arrb):
    """The non-VLA FLOATING dtype exclusion: such a column takes the earlier,
    unchanged `where_not_allclose` branch (diff.py:1447-1451) and never reaches
    the patched `elif`, so model.py's `compare_elementwise` (bound to the `else`
    body `np.where(arra != arrb)`) does not model it."""
    if is_vla_descriptor(ToSeq(fmt_cps)):
        return True
    return not (np.issubdtype(arra.dtype, np.floating)
                and np.issubdtype(arrb.dtype, np.floating))


# ---------------------------------------------------------------------------
# One differential step.
# ---------------------------------------------------------------------------

def check_one(fmt_str, a, b, stats):
    """Returns None when the input is in-domain and both legs agree, else a
    disagreement dict. Domain exclusions bump a counter and return None."""
    ta, tb = build_columns(fmt_str, a, b)
    arra = ta.data["K"]
    arrb = tb.data["K"]
    real_fmt = str(ta.columns["K"].format)
    fmt_cps = to_cps(real_fmt)

    if not in_modeled_domain(fmt_cps, arra, arrb):
        stats["n_skipped_float_branch"] += 1
        return None
    # The grounding is branch-relative, so the route must be decided first: each
    # comparator's summary uses that comparator's OWN per-position verdict.
    vla = is_vla_descriptor(ToSeq(fmt_cps))
    rm = row_mismatches_of(arra, arrb, vla)
    if rm is None:
        stats["n_skipped_ragged"] += 1
        return None

    orc = oracle(ta, tb)

    # leg (I): the copied impl region; leg (S): the postcondition's fold.
    shadow_impl = count_differing_rows(fmt_cps, rm)
    shadow_spec = row_granular_count(ToSeq(rm))

    # --- coverage, observed from outside the copied bodies -------------------
    tag = "row_aware" if vla else "elementwise"
    COV["vla_route" if vla else "nonvla_route"] += 1
    # A row whose two stored values have unequal length yet still aligns: the
    # class G-PANEL-2's witness came from. In-domain now, so track it.
    _WIDE = 1 << 53
    try:
        if any(int(np.max(np.abs(np.asarray(arra[i]).astype(object)))) >= _WIDE
               for i in range(len(arra)) if np.asarray(arra[i]).size):
            COV["wide_magnitude"] += 1
            if vla:
                # The discriminating sub-case: exact inequality would report a
                # differing row here but the comparator's own verdict does not.
                for i in range(len(arra)):
                    x = np.asarray(arra[i]); y = np.asarray(arrb[i])
                    if x.size and x.size == y.size:
                        exact = int(np.count_nonzero(x != y))
                        close = int(np.count_nonzero(
                            ~np.isclose(x, y, rtol=0.0, atol=0.0)))
                        if exact > 0 and close == 0:
                            COV["wide_magnitude_unresolved"] += 1
                            break
    except (TypeError, ValueError):
        pass
    if any(np.asarray(arra[i]).size != np.asarray(arrb[i]).size
           for i in range(len(arra))):
        COV["unequal_length_aligning"] += 1
    if len(rm) == 0:
        COV[tag + "_empty"] += 1
    if any(v > 0 for v in rm):
        COV[tag + "_diff_row"] += 1
    if any(v <= 0 for v in rm):
        COV[tag + "_same_row"] += 1
    if orc[0] == "ok" and sum(rm) > orc[1]:
        COV["vla_element_sum_diverges" if vla
            else "nonvla_element_sum_diverges"] += 1
    has_p = 80 in fmt_cps
    has_q = 81 in fmt_cps
    if has_q and not has_p:
        COV["q_only"] += 1
    if has_p and not has_q:
        COV["p_only"] += 1

    stats["n_checked"] += 1
    if orc[0] != "ok" or orc[1] != shadow_impl or orc[1] != shadow_spec:
        return {
            "format": real_fmt,
            "a": _jsonable(a), "b": _jsonable(b),
            "row_mismatches": rm,
            "shadow_impl": shadow_impl,
            "shadow_spec_fold": shadow_spec,
            "oracle": list(orc),
        }
    return None


def _jsonable(v):
    if isinstance(v, (list, tuple)):
        return [_jsonable(x) for x in v]
    if isinstance(v, complex):
        return [v.real, v.imag]
    if isinstance(v, (bool, int, float, str)):
        return v
    return repr(v)


# ---------------------------------------------------------------------------
# Inputs: boundary first, then seeded fuzz.
# ---------------------------------------------------------------------------

def boundary_inputs():
    """Boundary cases: empty, singleton, the exact F2P shapes, the issue repro,
    and every branch of both impl regions."""
    # --- the F2P scenarios (test_diff.py TestDiff::test_identical_tables /
    #     test_different_table_data, the QJ(2) column c11/cb11) ---------------
    yield ("QJ(2)", [[0, 1], [2, 3]], [[0, 1], [2, 3]])       # identical -> 0
    yield ("QJ(2)", [[0, 1], [2, 3]], [[1, 2], [3, 4]])       # both differ -> 2
    yield ("PI(2)", [[0, 1], [2, 3]], [[0, 1], [2, 3]])       # P still works
    yield ("PI(2)", [[0, 1], [2, 3]], [[1, 2], [3, 4]])
    # --- the issue repro shape: ragged-ACROSS-rows QD, identical -> 0 --------
    yield ("QD", [[0.0], [0.0, 0.0]], [[0.0], [0.0, 0.0]])
    yield ("PD", [[0.0], [0.0, 0.0]], [[0.0], [0.0, 0.0]])
    yield ("QD", [[1.0], [2.0, 3.0]], [[1.0], [2.0, 9.0]])    # ragged, 1 differs
    # --- rows whose two stored values have UNEQUAL lengths but still ALIGN.
    #     The real comparator judges them by that alignment, so a length
    #     difference alone is not a difference. This is the class G-PANEL-2's
    #     witness came from; it is now in-domain, not excluded.
    yield ("QJ", [[0]], [[0, 0]])                              # aligns -> 0
    yield ("QJ", [[0]], [[0, 1]])                              # aligns -> 1
    yield ("QJ", [[0]], [[1, 1]])                              # row-granular -> 1
    yield ("QJ", [[0, 0]], [[0]])                              # other way -> 0
    yield ("QJ", [[5]], [[5, 5, 5]])                           # 1 vs 3 -> 0
    yield ("QJ", [[1], [2, 2]], [[1, 1], [2]])                 # both align -> 0
    yield ("QD", [[1.0], [2.0, 3.0]], [[1.0, 1.0], [2.0, 3.0]])
    yield ("PJ", [[7]], [[7, 7]])                              # P side too -> 0
    yield ("PJ", [[7]], [[7, 8]])                              # -> 1
    # --- empty / singleton --------------------------------------------------
    yield ("QJ(2)", [], [])                                    # 0 rows, VLA
    yield ("J", [], [])                                        # 0 rows, non-VLA
    yield ("QJ", [[]], [[]])                                   # width-0 row
    yield ("QJ", [[7]], [[7]])                                 # singleton, same
    yield ("QJ", [[7]], [[8]])                                 # singleton, differs
    yield ("J", [3], [3])
    yield ("J", [3], [4])
    # --- VLA: partial-row diff (row-granular vs element sum) ----------------
    yield ("QJ(3)", [[1, 2, 3], [4, 5, 6]], [[1, 9, 3], [4, 5, 6]])   # -> 1
    yield ("QJ(3)", [[1, 2, 3], [4, 5, 6]], [[9, 9, 9], [4, 9, 6]])   # -> 2
    yield ("PJ(3)", [[1, 2, 3]], [[9, 9, 9]])                        # -> 1
    # --- VLA float NaN / inf ------------------------------------------------
    yield ("QD", [[float("nan"), 1.0]], [[float("nan"), 1.0]])
    yield ("QD", [[float("inf")]], [[float("inf")]])
    yield ("QD", [[float("nan")]], [[1.0]])
    yield ("PE", [[0.0, -0.0]], [[-0.0, 0.0]])
    # --- VLA bool / complex -------------------------------------------------
    yield ("QL(2)", [[1, 0], [1, 1]], [[1, 1], [1, 1]])
    yield ("PC(2)", [[1 + 1j, 2 + 2j]], [[1 + 1j, 9 + 2j]])
    yield ("QM(2)", [[1 + 2j, 3 + 0j]], [[1 + 2j, 3 + 0j]])
    yield ("QB(2)", [[1, 2], [3, 4]], [[1, 5], [3, 4]])
    # --- non-VLA: multi-element fixed-width (element sum diverges) ----------
    yield ("2J", [[0, 1], [2, 3]], [[0, 1], [2, 3]])
    yield ("2J", [[0, 1], [2, 3]], [[9, 9], [2, 3]])           # 1 row, 2 elems
    yield ("3I", [[0, 1, 2], [3, 4, 5]], [[0, 1, 9], [3, 4, 5]])
    yield ("4B", [[1, 2, 3, 4], [5, 6, 7, 1]], [[1, 2, 3, 7], [5, 6, 7, 1]])
    yield ("2K", [[1, 2], [3, 4]], [[7, 7], [7, 7]])
    yield ("2L", [[1, 0], [1, 1]], [[1, 1], [1, 1]])
    # --- non-VLA: scalar, bit, text, complex --------------------------------
    yield ("K", [1, 2, 3], [1, 9, 3])
    yield ("2X", [[1, 0], [1, 1]], [[0, 0], [1, 1]])
    yield ("10A", ["foo", "bar"], ["foo", "baz"])
    yield ("5A", ["abcd", "ef"], ["abcd", "ef"])
    yield ("A", ["x", "y"], ["z", "y"])
    yield ("C", [1 + 2j, 3 + 4j], [1 + 2j, 5 + 6j])


# format families. Every entry is (format string, value kind).
VLA_INT = ["PI", "PJ", "PK", "PB", "QI", "QJ", "QK", "QB",
           "PI(4)", "PJ(4)", "QI(4)", "QJ(4)", "QK(4)", "PB(4)", "QB(4)"]
VLA_FLT = ["PD", "PE", "QD", "QE", "PD(4)", "QE(4)", "QD(4)"]
VLA_BIT = ["PL", "QL", "PL(4)", "QL(4)"]
VLA_CPX = ["PC(4)", "PM(4)", "QC(4)", "QM(4)"]
NV_SCALAR_INT = ["I", "J", "K", "B"]
NV_MULTI_INT = ["2I", "3J", "2K", "4B", "2J", "3I"]
NV_BOOL = ["L", "2L", "X", "2X", "8X"]
NV_TEXT = ["A", "3A", "5A", "10A"]
NV_CPX = ["C", "M", "2C", "2M"]

UNSIGNED = ("B", "L", "X")


def _width_of(fmt_str):
    """Leading repeat count of a fixed-width format ('3J' -> 3, 'J' -> 1)."""
    digits = ""
    for ch in fmt_str:
        if ch.isdigit():
            digits += ch
        else:
            break
    return int(digits) if digits else 1


def _int_val(rng, fmt_str):
    """An integer element value for `fmt_str`.

    For the 64-bit codes the value is drawn across the FULL declared range, not
    just small magnitudes. The row-aware comparator's per-position closeness
    verdict is evaluated in a fixed-precision arithmetic whose significand is
    narrower than the 64-bit integer range, so at and above 2**53 it stops
    separating neighbouring values. Confining the generator to |v| <= 7 makes
    that entire regime structurally unreachable, so the check would assert an
    agreement it never tested on exactly the magnitudes the 64-bit descriptor
    exists to carry. The distribution therefore mixes small values, full-range
    magnitudes, and values straddling the 2**53 resolution limit.
    """
    unsigned = any(u in fmt_str for u in UNSIGNED)
    # 64-bit element codes: 'K' (int64) and 'Q' descriptor arrays of them.
    wide = "K" in fmt_str
    if not wide:
        if unsigned:
            return rng.randint(0, 7)
        return rng.randint(-4, 4)
    r = rng.random()
    if r < 0.45:
        return rng.randint(0, 7) if unsigned else rng.randint(-4, 4)
    if r < 0.70:
        return rng.getrandbits(62)
    if r < 0.90:
        return (1 << 53) + rng.randint(-2, 6)
    return rng.choice([1 << 53, (1 << 53) + 1, 1 << 62, (1 << 62) + 1])


def _perturb(rng, row, mk, ragged_ok=False):
    """Copy `row`, then mutate a random subset of its positions. The 0.30 rate
    yields a healthy mix of identical rows, single-element (partial) diffs and
    all-element diffs, so both comparator paths and the row-vs-element-sum
    distinction all fire.

    With probability 0.12 the copy is also RESIZED, so the two stored values of
    a row differ in length. That is the alignment-dependent class: where the two
    lengths still align positionally the real comparator judges the row by that
    alignment (a length difference alone is not a difference) and the input is
    in-domain; where no alignment exists the real comparator raises and the row
    is reported out-of-domain by `row_mismatches_of`. Without this the fuzz would
    only ever build equal-length rows and the class would go untested."""
    out = list(row)
    for k in range(len(out)):
        if rng.random() < 0.30:
            out[k] = mk()
    if ragged_ok and rng.random() < 0.12:
        # Bias toward lengths that broadcast against len(row) (0/1/len) so the
        # aligning half of the class is reached often, not only the raising half.
        w = rng.choice([0, 1, 1, len(out), rng.randint(0, 4)])
        if w <= len(out):
            out = out[:w]
        else:
            out = out + [mk() for _ in range(w - len(out))]
    return out


def fuzz_input(rng):
    """One randomized (format, a, b) inside the modeled domain."""
    roll = rng.random()
    nrows = rng.randint(0, 6)

    if roll < 0.34:                                     # variable-length int
        fmt = rng.choice(VLA_INT)
        mk = lambda: _int_val(rng, fmt)                 # noqa: E731
        rows_a = [[mk() for _ in range(rng.randint(0, 4))] for _ in range(nrows)]
    elif roll < 0.55:                                   # variable-length float
        fmt = rng.choice(VLA_FLT)
        specials = [float("nan"), float("inf"), float("-inf"), 0.0, -0.0]
        mk = lambda: (rng.choice(specials) if rng.random() < 0.15    # noqa: E731
                      else float(rng.randint(-4, 4)))
        rows_a = [[mk() for _ in range(rng.randint(0, 4))] for _ in range(nrows)]
    elif roll < 0.62:                                   # variable-length bool
        fmt = rng.choice(VLA_BIT)
        mk = lambda: rng.randint(0, 1)                  # noqa: E731
        rows_a = [[mk() for _ in range(rng.randint(0, 4))] for _ in range(nrows)]
    elif roll < 0.68:                                   # variable-length complex
        fmt = rng.choice(VLA_CPX)
        mk = lambda: complex(rng.randint(-3, 3), rng.randint(-3, 3))  # noqa: E731
        rows_a = [[mk() for _ in range(rng.randint(0, 4))] for _ in range(nrows)]
    elif roll < 0.78:                                   # non-VLA multi-element
        fmt = rng.choice(NV_MULTI_INT)
        w = _width_of(fmt)
        mk = lambda: _int_val(rng, fmt)                 # noqa: E731
        rows_a = [[mk() for _ in range(w)] for _ in range(nrows)]
    elif roll < 0.85:                                   # non-VLA bool / bit
        fmt = rng.choice(NV_BOOL)
        w = _width_of(fmt)
        mk = lambda: rng.randint(0, 1)                  # noqa: E731
        rows_a = ([[mk() for _ in range(w)] for _ in range(nrows)] if w > 1
                  else [mk() for _ in range(nrows)])
    elif roll < 0.91:                                   # non-VLA text
        fmt = rng.choice(NV_TEXT)
        alpha = "abcXY 0"
        mk = lambda: "".join(rng.choice(alpha)           # noqa: E731
                             for _ in range(rng.randint(0, 4)))
        rows_a = [mk() for _ in range(nrows)]
    elif roll < 0.96:                                   # non-VLA scalar int
        fmt = rng.choice(NV_SCALAR_INT)
        mk = lambda: _int_val(rng, fmt)                 # noqa: E731
        rows_a = [mk() for _ in range(nrows)]
    else:                                               # non-VLA complex
        fmt = rng.choice(NV_CPX)
        w = _width_of(fmt)
        mk = lambda: complex(rng.randint(-3, 3), rng.randint(-3, 3))  # noqa: E731
        rows_a = ([[mk() for _ in range(w)] for _ in range(nrows)] if w > 1
                  else [mk() for _ in range(nrows)])

    if rows_a and isinstance(rows_a[0], list):
        # Only a VARIABLE-length column may have unequal per-row lengths; a
        # fixed-width column would simply fail to build.
        ragged_ok = ("P" in fmt) or ("Q" in fmt)
        rows_b = [_perturb(rng, r, mk, ragged_ok) for r in rows_a]
    elif rows_a and isinstance(rows_a[0], str):
        rows_b = [r if rng.random() < 0.5 else mk() for r in rows_a]
    else:
        rows_b = [r if rng.random() < 0.5 else mk() for r in rows_a]
    return (fmt, rows_a, rows_b)


NON_VACUITY = [
    ("vla_route", "the variable-length dispatcher branch was never taken"),
    ("nonvla_route", "the element-wise dispatcher branch was never taken"),
    ("row_aware_diff_row", "compare_row_aware never saw a differing row"),
    ("row_aware_same_row", "compare_row_aware never saw an equal row"),
    ("row_aware_empty", "compare_row_aware never ran on a zero-row column"),
    ("elementwise_diff_row", "compare_elementwise never saw a differing row"),
    ("elementwise_same_row", "compare_elementwise never saw an equal row"),
    ("elementwise_empty", "compare_elementwise never ran on a zero-row column"),
    ("vla_element_sum_diverges",
     "no variable-length column distinguished the row count from an element sum"),
    ("nonvla_element_sum_diverges",
     "no element-wise column distinguished the row count from an element sum"),
    ("q_only", "no Q-only (64-bit) variable-length descriptor was exercised"),
    ("p_only", "no P-only (32-bit) variable-length descriptor was exercised"),
    ("unequal_length_aligning",
     "no column had a row whose two stored values differ in length yet still "
     "align positionally — the alignment-dependent class went untested"),
    ("wide_magnitude",
     "no column carried a magnitude at or beyond the row-aware comparator's "
     "per-position resolution limit (2**53) — the 64-bit regime the Q "
     "descriptor exists for went untested"),
    ("wide_magnitude_unresolved",
     "no row-aware column had two stored values the per-position closeness "
     "verdict could not separate — the case where that verdict is strictly "
     "coarser than exact inequality went untested, so the branch-relative "
     "grounding was never actually discriminated from an exact one"),
]


def main():
    argv_n = int(sys.argv[1]) if len(sys.argv) > 1 else N_TARGET
    rng = random.Random(SEED)
    stats = {"n_checked": 0, "n_generated": 0,
             "n_skipped_ragged": 0, "n_skipped_float_branch": 0,
             "n_skipped_unbuildable": 0}
    unbuildable_examples = []
    disagreements = []

    def run(fmt, a, b):
        stats["n_generated"] += 1
        try:
            d = check_one(fmt, a, b, stats)
        except Exception as e:                          # noqa: BLE001
            # Column construction failed => this input is not a real FITS
            # column at all and has no oracle. Counted, never silent.
            stats["n_skipped_unbuildable"] += 1
            if len(unbuildable_examples) < 5:
                unbuildable_examples.append(
                    "%s on fmt=%r: %s" % (type(e).__name__, fmt, e))
            return
        if d is not None and len(disagreements) < 10:
            disagreements.append(d)

    n_boundary = 0
    for fmt, a, b in boundary_inputs():
        n_boundary += 1
        run(fmt, a, b)

    while stats["n_checked"] < argv_n:
        fmt, a, b = fuzz_input(rng)
        run(fmt, a, b)

    missing = [msg for key, msg in NON_VACUITY if COV[key] == 0]
    report = {
        "instance": "astropy__astropy-14539",
        "backend": "nagini",
        "seed": SEED,
        "n_boundary": n_boundary,
        "n_generated": stats["n_generated"],
        "n_checked": stats["n_checked"],
        "n_skipped_ragged": stats["n_skipped_ragged"],
        "n_skipped_float_branch": stats["n_skipped_float_branch"],
        "n_skipped_unbuildable": stats["n_skipped_unbuildable"],
        "coverage": dict(COV),
        "mismatches": len(disagreements),
    }
    if unbuildable_examples:
        report["unbuildable_examples"] = unbuildable_examples

    if disagreements:
        print("G-CONF FAIL: %d disagreement(s) between the model.py impl region "
              "and the real patched TableDataDiff._diff over %d inputs:"
              % (len(disagreements), stats["n_checked"]))
        for d in disagreements:
            print("  " + json.dumps(d))
        report["status"] = "fail"
        report["disagreements"] = disagreements
        print(json.dumps(report))
        return 1

    if missing:
        print("G-CONF FAIL: the check ran clean but was VACUOUS on %d "
              "obligation(s):" % len(missing))
        for m in missing:
            print("  " + m)
        report["status"] = "fail"
        report["vacuous"] = missing
        print(json.dumps(report))
        return 1

    print("G-CONF OK: model.py impl regions (count_differing_rows dispatch + "
          "both comparator bodies, verbatim) AND the row_granular_count "
          "postcondition fold agree with the real gold-patched "
          "TableDataDiff._diff per-column diff_total on %d FITS column pairs "
          "(%d boundary + fuzz, seed=%d); every dispatcher/comparator branch "
          "taken, %d variable-length + %d element-wise columns where an element "
          "sum would diverge from the row count, %d Q-only and %d P-only "
          "descriptors, %d columns with an unequal-length but aligning row; "
          "0 disagreements."
          % (stats["n_checked"], n_boundary, SEED,
             COV["vla_element_sum_diverges"],
             COV["nonvla_element_sum_diverges"],
             COV["q_only"], COV["p_only"], COV["unequal_length_aligning"]))
    report["status"] = "pass"
    print(json.dumps(report))
    return 0


if __name__ == "__main__":
    sys.exit(main())
