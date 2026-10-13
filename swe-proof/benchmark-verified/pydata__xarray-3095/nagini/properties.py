# properties.py — PBT falsification battery for pydata__xarray-3095.
#
# NOT a Nagini module; a record of adversarial cases the runner
# (swebench_nagini.pbt) executes and stamps RESULT on. Spec cases are full
# model.py variants that share the FROZEN spec (region-surgery: edits live ONLY
# inside the # impl-start / # impl-end region, which spec_view elides — so
# same_spec holds by construction) and are checked by Nagini verify; the axiom
# case is a real-callee probe checked in Docker.
#
# DEFENDED SURFACE (what this spec protects — see model.py / refinement.md):
#
#   adapter_copy(self: IndexWrapper, deep: bool) -> int    [the modeled site]
#     Requires Acc(self.array_kind, 1/2)        <-- READ-ONLY input (half perm)
#     Requires Acc(self.stored_dtype, 1/2)      <-- READ-ONLY input (half perm)
#     Requires self.stored_dtype != NO_DTYPE
#     Requires self.array_kind   != NO_DTYPE
#     Ensures  Acc(self.array_kind, 1/2)        <-- frame: caller keeps its half
#     Ensures  Acc(self.stored_dtype, 1/2)      <-- frame: caller keeps its half
#     Ensures  self.array_kind   == Old(self.array_kind)    <-- original unchanged
#     Ensures  self.stored_dtype == Old(self.stored_dtype)  <-- original unchanged
#     Ensures  Result() == Old(self.stored_dtype)           <-- LOAD-BEARING
#
#   The LOAD-BEARING discriminator: the duplicate reports the element type the
#   ORIGINAL was created with (Old(self.stored_dtype)) — NOT the type re-derived
#   from the duplicated buffer (array_kind). These two DISAGREE exactly in the
#   fixed-width-text case (array_kind == OBJECT_DTYPE != stored_dtype); for
#   numeric dtypes they coincide. So a wrong impl that returns array_kind is
#   correct on the numeric sub-domain but wrong on text — the prepatch bug and
#   the F2P regression test_copy[str-True].
#
#   ORACLE GROUNDEDNESS (directive 2 / ungrounded-oracle ECHO is N/A here):
#   the only @Pure helper is derive_dtype(array_kind, given) = (given if given !=
#   NO_DTYPE else array_kind) — fully unfoldable and GROUNDED entirely in its two
#   int args; it is NOT an opaque answer-key. The load-bearing postcondition is
#   pinned to Old(self.stored_dtype), a fact of the read-only INPUT, not to any
#   oracle value. There is therefore no "wrong echo of an answer key" to build:
#   any value the impl returns must equal the input's own Old(stored_dtype). The
#   ungrounded-oracle-echo class is N/A; the honest cheapest correct impl (return
#   self.stored_dtype, which == derive_dtype(array_kind, stored_dtype) since
#   stored_dtype != NO_DTYPE) is the positive control below. See 'assessment'.
#
#   No @ContractOnly axioms (meta.axioms == []). The changed dtype-determination
#   is modelled DEEPLY (derive_dtype + the verified adapter_copy body); the only
#   kind-A item is an A-REFERENCE validated == the real PandasIndexAdapter
#   construction/copy + IndexVariable.copy by axiom_check.py (G-AX). The single
#   AXIOM_TEST below re-runs that faithfulness check, strengthened with fuzz over
#   the caller-reachable dtype domain, self-contained in-container (apply_gold,
#   since the new copy method + the `else: dtype = np.dtype(dtype)` branch exist
#   only post-patch).
from pathlib import Path

INSTANCE = "pydata__xarray-3095"
FLOAT_ENCODING = None  # meta.json float_encoding == null

_BASE = (Path(__file__).parent / "model.py").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# ===========================================================================
# Anchor INSIDE the impl region (between # impl-start / # impl-end). Editing
# only this keeps spec_view (hence same_spec) byte-identical. The whole gold
# impl body is a unique anchor.
# ===========================================================================
_IMPL_GOLD = """    # Mirror the fix: rebuild the wrapper supplying the ORIGINAL element type,
    # so its reported type is carried over rather than re-derived.
    array_kind = self.array_kind
    dtype = self.stored_dtype
    duplicate = IndexWrapper(array_kind, derive_dtype(array_kind, dtype))
    return duplicate.stored_dtype"""

assert _IMPL_GOLD in _BASE, "impl anchor drift: adapter_copy body not verbatim"


# ===========================================================================
# (1) POSITIVE CONTROL — structurally different but CORRECT (verify).
# The gold stages two locals (array_kind, dtype), reconstructs an IndexWrapper
# via derive_dtype, and returns the duplicate's stored_dtype. This variant
# reorders the local reads (stored_dtype first) and binds the supplied element
# type through a named local `supplied` BEFORE the array_kind read, then returns
# the duplicate's stored_dtype. Since stored_dtype != NO_DTYPE (precondition),
# derive_dtype(array_kind, supplied) == supplied == stored_dtype, so the rebuilt
# wrapper's stored_dtype == Old(self.stored_dtype). No loop / branch / fold lemma
# is involved (assignment-only region), so this cannot fail for a proof-trigger
# reason. If a faithful correct impl could NOT verify => SPEC-TOO-STRONG.
# ===========================================================================
_IMPL_POS = """    # Structurally different but correct: read stored_dtype first, bind the
    # supplied element type to a named local, then read array_kind, and rebuild.
    supplied = self.stored_dtype
    array_kind = self.array_kind
    duplicate = IndexWrapper(array_kind, derive_dtype(array_kind, supplied))
    return duplicate.stored_dtype"""

# ===========================================================================
# (2) POSITIVE CONTROL / cheapest honest impl — direct carry-over (verify).
# The honest cheapest correct implementation: return the original's stored
# dtype directly (it equals derive_dtype(array_kind, stored_dtype) since
# stored_dtype != NO_DTYPE, and equals Old(self.stored_dtype) since self is not
# mutated). This is the grounded answer the postcondition pins (directive 2
# positive control in lieu of an ungrounded-oracle echo). Reads self.array_kind
# once to keep the field live, then returns self.stored_dtype. Must verify.
# ===========================================================================
_IMPL_DIRECT = """    # Cheapest honest correct impl: carry the original element type over
    # directly. derive_dtype(array_kind, stored_dtype) == stored_dtype here
    # (stored_dtype != NO_DTYPE), and self is untouched, so the result equals
    # Old(self.stored_dtype).
    kept = self.stored_dtype
    return kept"""

# ===========================================================================
# (3) ADMISSIBILITY — the precondition admits a normal F2P-shaped input
# (verify). Cannot add a top-level caller (that leaves the impl region and
# breaks same_spec). Instead, in-region: construct a FRESH wrapper with the
# fixed-width-text witness shape the F2P exercises — array_kind == OBJECT_DTYPE
# (re-derivation of a text buffer collapses to object) and a distinct
# stored_dtype != NO_DTYPE, the case where array_kind != stored_dtype — and
# Assert it satisfies adapter_copy's Requires (both != NO_DTYPE). Then reach the
# normal gold return. If the Requires were vacuous / over-strong (e.g. forbade
# the text witness) this construction or assertion could not stand =>
# PRECOND-TOO-STRONG. Uses literal codes (OBJECT_DTYPE == 0, a text code 5).
# ===========================================================================
_IMPL_ADMISS = """    # admissibility: the precondition admits the fixed-width-text witness the
    # F2P exercises, where the re-derivable buffer type (object) differs from the
    # stored element type. Build it explicitly and confirm it meets the Requires.
    text_code = 5  # type: int                     # a fixed-width-text element code
    witness = IndexWrapper(OBJECT_DTYPE, text_code)  # array_kind=object != stored
    Assert(witness.stored_dtype != NO_DTYPE)         # adapter_copy Requires (stored)
    Assert(witness.array_kind != NO_DTYPE)           # adapter_copy Requires (kind)
    Assert(witness.array_kind != witness.stored_dtype)  # the discriminating case
    # normal gold computation for the actual self.
    array_kind = self.array_kind
    dtype = self.stored_dtype
    duplicate = IndexWrapper(array_kind, derive_dtype(array_kind, dtype))
    return duplicate.stored_dtype"""

# ===========================================================================
# (4) FRAME-MUTATION — write the read-only input self.stored_dtype (reject).
# MANDATORY: self is held at Acc(self.stored_dtype, 1/2) only. A value-NEUTRAL
# write `self.stored_dtype = self.stored_dtype` needs FULL (1/1) permission, so
# Nagini rejects for INSUFFICIENT PERMISSION. The rest of the impl is the gold
# carry-over, so the rejection is attributable to the write, not a value
# mismatch. A byte-fuzzer never thinks to mutate the read-only input — this is
# the project's #1 weakness class. The Old-equality clauses + the half-perm are
# what block a wrong impl from satisfying Result() == Old(self.stored_dtype)
# vacuously by overwriting stored_dtype.
# ===========================================================================
_IMPL_FRAME = """    # FRAME MUTATION: write back into the read-only half-permission input.
    array_kind = self.array_kind
    dtype = self.stored_dtype
    self.stored_dtype = dtype  # value-neutral, but needs FULL permission
    duplicate = IndexWrapper(array_kind, derive_dtype(array_kind, dtype))
    return duplicate.stored_dtype"""

# ===========================================================================
# (5) PARTIAL-DOMAIN / prepatch re-derivation (reject). THE pre-patch bug
# (model_prepatch.py): rebuild the wrapper WITHOUT supplying the original
# element type, so the duplicate's type is RE-DERIVED from the buffer:
# derive_dtype(array_kind, NO_DTYPE) == array_kind. This agrees with the gold on
# the numeric sub-domain (array_kind == stored_dtype) but DIVERGES on text
# (array_kind == OBJECT_DTYPE != stored_dtype), so the load-bearing
# Result() == Old(self.stored_dtype) fails on the text witness.
# ===========================================================================
_IMPL_REDERIVE = """    # PARTIAL-DOMAIN: re-derive the dtype from the duplicated buffer instead of
    # carrying over the original (the pre-patch bug). Correct on numeric inputs,
    # wrong on fixed-width text.
    array_kind = self.array_kind
    duplicate = IndexWrapper(array_kind, derive_dtype(array_kind, NO_DTYPE))
    return duplicate.stored_dtype"""

# ===========================================================================
# (6) PARTIAL-DOMAIN / constant object code (reject). Always return OBJECT_DTYPE
# (the lossy fallback). Correct only on the sub-domain where the original's
# stored_dtype IS the object code; wrong on every other element type (int,
# float, text, datetime). Violates Result() == Old(self.stored_dtype) whenever
# Old(self.stored_dtype) != OBJECT_DTYPE.
# ===========================================================================
_IMPL_CONSTOBJ = """    # PARTIAL-DOMAIN: collapse every duplicate to the generic object code
    # (the lossy fallback). Correct only when the original is already object.
    array_kind = self.array_kind
    return OBJECT_DTYPE"""


SPEC_TESTS = [
    {
        "id": "pos-control-reorder-locals",
        "kind": "soundness",
        "expect": "verify",
        "module": _swap(_BASE, _IMPL_GOLD, _IMPL_POS),
        "rationale": "Structurally different but correct: read stored_dtype first, "
                     "bind the supplied element type to a named local `supplied`, then "
                     "read array_kind and rebuild via derive_dtype. Since stored_dtype "
                     "!= NO_DTYPE (precondition), derive_dtype(array_kind, supplied) == "
                     "supplied == stored_dtype, so the duplicate's stored_dtype == "
                     "Old(self.stored_dtype). Assignment-only region (no loop/branch/"
                     "fold lemma), so it cannot fail for a proof-trigger reason. Must "
                     "verify, else SPEC-TOO-STRONG.",
    },
    {
        "id": "pos-control-direct-carryover",
        "kind": "soundness",
        "expect": "verify",
        "module": _swap(_BASE, _IMPL_GOLD, _IMPL_DIRECT),
        "rationale": "The honest cheapest correct impl: return self.stored_dtype "
                     "directly. It equals derive_dtype(array_kind, stored_dtype) "
                     "(stored_dtype != NO_DTYPE) and equals Old(self.stored_dtype) "
                     "(self untouched). This is the grounded positive control standing "
                     "in for the N/A ungrounded-oracle-echo class (directive 2): the "
                     "postcondition is pinned to a fact of the input, so the cheapest "
                     "honest answer IS correct and must verify, else SPEC-TOO-STRONG.",
    },
    {
        "id": "admissibility-text-witness",
        "kind": "admissibility",
        "expect": "verify",
        "module": _swap(_BASE, _IMPL_GOLD, _IMPL_ADMISS),
        "rationale": "Constructs in-region the fixed-width-text witness the F2P "
                     "exercises — IndexWrapper(OBJECT_DTYPE, text_code) with array_kind "
                     "== object != stored_dtype, both != NO_DTYPE — and Asserts it meets "
                     "adapter_copy's Requires (stored_dtype != NO_DTYPE, array_kind != "
                     "NO_DTYPE) and the discriminating array_kind != stored_dtype. If "
                     "the precondition were vacuous or forbade the text witness the "
                     "construction/assertions could not stand => PRECOND-TOO-STRONG. "
                     "Source: the two != NO_DTYPE Requires + IndexWrapper.__init__.",
    },
    {
        "id": "frame-mutation-write-stored-dtype",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _IMPL_GOLD, _IMPL_FRAME),
        "refinement": "A faithful real patch in which PandasIndexAdapter.copy mutated "
                      "self before returning the duplicate (e.g. self._dtype = "
                      "self._dtype or rebinding self.array) would write through the "
                      "original adapter the caller still holds. The gold copy only READS "
                      "self (self.array, self._dtype) and builds a NEW PandasIndexAdapter; "
                      "IndexVariable.copy and assert_identical rely on the ORIGINAL "
                      "variable being unchanged after w = v.copy(...) (test_copy asserts "
                      "assert_identical(v, w) with v still intact), so a self-mutating "
                      "copy would corrupt the original v and the F2P assertion would not "
                      "faithfully hold — the patch would not resolve.",
        "rationale": "adapter_copy holds only Acc(self.stored_dtype, 1/2). The "
                     "value-neutral write self.stored_dtype = dtype needs FULL (1/1) "
                     "permission, so Nagini rejects for INSUFFICIENT PERMISSION. The "
                     "rest is the gold carry-over, so the rejection is attributable to "
                     "the write. Source: the permission system + the Acc(...,1/2) "
                     "Requires; the Ensures(self.stored_dtype == Old(self.stored_dtype)) "
                     "frame clause is what the write would otherwise try to defeat.",
    },
    {
        "id": "partial-domain-rederive-prepatch",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _IMPL_GOLD, _IMPL_REDERIVE),
        "refinement": "This IS the pre-patch behaviour (model_prepatch.py / the inlined "
                      "PandasIndexAdapter(self._data.array.copy(deep=True)) caller): "
                      "reconstruct WITHOUT passing self._dtype, so __init__ re-derives "
                      "the dtype from the copied pandas Index. For a fixed-width-text "
                      "('<U*') index that copied Index is object-dtype, so the re-"
                      "derivation collapses to object (np.dtype('O')) — casting <U* to "
                      "object. test_copy[str-True] asserts assert_identical(v, w) and "
                      "the unicode dtype is preserved, so the faithful patch FAILS the "
                      "F2P and does NOT resolve.",
        "rationale": "Returns derive_dtype(array_kind, NO_DTYPE) == array_kind. On the "
                     "numeric sub-domain array_kind == stored_dtype so it agrees, but on "
                     "the text witness array_kind == OBJECT_DTYPE != stored_dtype, so the "
                     "load-bearing Result() == Old(self.stored_dtype) fails. Source: the "
                     "Result() == Old(self.stored_dtype) postcondition clause (the "
                     "discriminator G-DIFF / the prepatch failure point, model_prepatch "
                     "line 100).",
    },
    {
        "id": "partial-domain-const-object",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _IMPL_GOLD, _IMPL_CONSTOBJ),
        "refinement": "A faithful real patch that hard-coded the duplicate's dtype to "
                      "np.dtype('O') regardless of the original (e.g. always passing "
                      "dtype=object to the reconstruction) would report object for every "
                      "copied index. test_copy[int-True]/[float-True]/[str-True] all "
                      "assert the ORIGINAL dtype is preserved (int64/float64/<U*), so the "
                      "duplicate's object dtype mismatches and the F2P/P2P copy tests "
                      "FAIL — the patch does not resolve. It happens to pass only the "
                      "(untested-as-new) already-object case.",
        "rationale": "Returns the constant OBJECT_DTYPE. Correct only when "
                     "Old(self.stored_dtype) == OBJECT_DTYPE; for int/float/text/"
                     "datetime element codes Old(self.stored_dtype) != OBJECT_DTYPE, so "
                     "Result() == Old(self.stored_dtype) fails. Source: the "
                     "Result() == Old(self.stored_dtype) postcondition clause.",
    },
]


# ===========================================================================
# AXIOM lane — one A-reference faithfulness probe (axiom-soundness). meta.axioms
# == [] (no @ContractOnly axiom), but the changed dtype-determination is modelled
# DEEPLY as derive_dtype/adapter_copy, an A-reference. PBT_PLAN §2.4: a deep model
# must equal the real callee on every caller-reachable input. This probe runs the
# REAL PandasIndexAdapter / IndexVariable in-container and asserts the deep model's
# claims hold, strengthened with fuzz over the caller-reachable dtype domain
# (text/int/float/datetime/object) x deep in {True, False}:
#   - supplied dtype is used verbatim by the real __init__ (derive_dtype, given
#     branch);                                                          [F1a]
#   - re-deriving (dtype=None) from a COPY of a text adapter's pandas Index
#     collapses to object — array_kind != stored_dtype is REAL for text  [F1b]
#     (this is exactly the model's array_kind == OBJECT_DTYPE != stored_dtype);
#   - the real PandasIndexAdapter.copy(deep=D) reports the original dtype for
#     every element type and deep in {True, False} (== Result() ==
#     Old(self.stored_dtype));                                          [F2]
#   - the F2P end-to-end IndexVariable.copy(deep=D) preserves '<U*'.    [F3]
# apply_gold=True: the new copy method + the `else: dtype = np.dtype(dtype)`
# branch exist only post-patch. Self-contained; opens nothing on disk; stdlib +
# numpy/pandas/xarray only (present in the eval image). exit 0 iff every
# obligation holds. CALLER-DOMAIN CONTAINMENT: the model can only reach
# array_kind/stored_dtype int codes whose real-dtype pre-images are the element
# types pandas/numpy produce for the F2P matrix (text/int/float) plus the object
# fallback — all covered by the fuzz buffers; there is no caller-reachable dtype
# the deep model would mis-handle (derive_dtype is total over int x int).
# ===========================================================================
_AX_PROBE = r'''
import sys
import numpy as np
import pandas as pd

from xarray.core.indexing import PandasIndexAdapter
from xarray.core.variable import IndexVariable

OBJECT = np.dtype('O')


def fail(msg):
    print("AXIOM FAIL: " + msg)
    sys.exit(1)


def derive_dtype(array_kind, given_dtype):
    # model.py's derive_dtype over real np.dtype objects (None == NO_DTYPE).
    if given_dtype is not None:
        return given_dtype
    return array_kind


# caller-reachable element types (the F2P matrix + datetime + the object case).
buffers = [
    ("text",  np.array(['foo', 'bar', 'baz']).astype(str)),       # '<U*'
    ("text2", (0.5 * np.arange(10)).astype(str)),                 # the F2P data
    ("int",   np.arange(7)),
    ("float", 0.5 * np.arange(7)),
    ("dt",    pd.date_range('2000-01-01', periods=4).values),     # datetime64
    ("obj",   np.array([object(), object()], dtype=object)),      # already object
]

# --- F1a: a supplied dtype is used verbatim by the real __init__ -------------
for name, buf in buffers:
    for D in (OBJECT, np.dtype('<U7'), np.dtype('int64'), np.dtype('float64')):
        a = PandasIndexAdapter(buf, dtype=D)
        if a.dtype != D:
            fail("supplied dtype not preserved on %r: gave %r want %r"
                 % (name, a.dtype, D))
        if derive_dtype(a.dtype, D) != D:
            fail("derive_dtype disagrees (supplied) on %r" % name)

# --- F1b: re-derivation of fixed-width text collapses to object (lossy) ------
# array_kind != stored_dtype is REAL for text (model's discriminating case).
text_buf = (0.5 * np.arange(10)).astype(str)        # '<U32'
original = PandasIndexAdapter(text_buf)             # dtype re-derived once
original_dtype = original.dtype
if original_dtype == OBJECT:
    fail("setup: original text adapter already object-typed")
# pre-patch reconstruction path: re-derive from a copy of the stored Index.
rederived = PandasIndexAdapter(original.array.copy(deep=True), dtype=None)
if rederived.dtype != OBJECT:
    fail("re-derived text dtype did not collapse to object, got %r"
         % rederived.dtype)
# array_kind (re-derived, object) and stored_dtype (original, <U*) DISAGREE.
if derive_dtype(rederived.dtype, None) == original_dtype:
    fail("model assumes array_kind != stored_dtype for text but they match")

# --- F2: the real PandasIndexAdapter.copy preserves the original dtype -------
# (== model Result() == Old(self.stored_dtype)) for every element type, both deep.
for name, buf in buffers:
    orig = PandasIndexAdapter(buf)                  # dtype re-derived once
    od = orig.dtype
    for deep in (True, False):
        dup = orig.copy(deep=deep)
        if dup.dtype != od:
            fail("copy(deep=%r) changed dtype on %r: %r -> %r"
                 % (deep, name, od, dup.dtype))
        # mirror the deep model: derive_dtype(array_kind, od) == od (supplied).
        if derive_dtype(od, od) != od:
            fail("deep model copy carry-over disagrees on %r" % name)
# also a supplied-dtype adapter (the <U* carry-over, array_kind != stored).
sup = PandasIndexAdapter(rederived.array, original._dtype)  # carry over <U*
for deep in (True, False):
    dup = sup.copy(deep=deep)
    if dup.dtype != original_dtype:
        fail("copy of carried-over <U* adapter (deep=%r) lost dtype: %r"
             % (deep, dup.dtype))

# --- F3: the F2P regression end-to-end (IndexVariable.copy preserves <U*) -----
for deep in (True, False):
    v = IndexVariable('x', (0.5 * np.arange(10)).astype(str), {'foo': 'bar'})
    w = v.copy(deep=deep)
    if w.dtype != v.dtype:
        fail("IndexVariable.copy(deep=%r) changed dtype: %r -> %r"
             % (deep, v.dtype, w.dtype))
    if w.dtype == OBJECT and v.dtype != OBJECT:
        fail("IndexVariable.copy(deep=%r) cast unicode -> object" % deep)

print("AXIOM OK: derive_dtype + adapter_copy A-reference faithful to real "
      "PandasIndexAdapter/IndexVariable; supplied dtype verbatim; text "
      "re-derivation collapses to object (array_kind != stored_dtype real); "
      "copy(deep=True/False) preserves the original dtype across "
      "text/int/float/datetime/object; F2P IndexVariable.copy preserves '<U*'.")
sys.exit(0)
'''

AXIOM_TESTS = [
    {
        "id": "ax-ref-derive-copy-faithful",
        "axiom": "derive_dtype/adapter_copy",
        "kind": "axiom-soundness",
        "expect": "holds",
        "apply_gold": True,
        "probe": _AX_PROBE,
        "rationale": "A-reference faithfulness (no @ContractOnly axiom). Runs the REAL "
                     "PandasIndexAdapter / IndexVariable in-container and asserts the "
                     "deep model's claims on the caller-reachable dtype domain "
                     "(text/int/float/datetime/object x deep in {True,False}): a "
                     "supplied dtype is used verbatim (derive_dtype given branch); "
                     "re-deriving text collapses to object so array_kind != stored_dtype "
                     "is REAL (the discriminating case); the real copy(deep=D) preserves "
                     "the original dtype (== Result() == Old(self.stored_dtype)); and the "
                     "F2P IndexVariable.copy preserves '<U*'. If the real callee "
                     "disagreed on any caller-reachable input the A-reference would be "
                     "UNSOUND. apply_gold (the copy method + the np.dtype(dtype) else "
                     "branch are post-patch). Mirrors/strengthens axiom_check.py F1-F3.",
    },
]
