# properties.py — PBT falsification battery for pydata__xarray-6461.
#
# NOT a Nagini module; a record of adversarial cases the runner
# (swebench_nagini.pbt) executes and stamps RESULT on. Spec cases are full
# model.py variants that share the FROZEN spec (region-surgery: edits live ONLY
# inside the # impl-start / # impl-end region, which spec_view elides whole —
# markers, nested invariants and all — so same_spec holds by construction) and
# are checked by Nagini verify.
#
# DEFENDED SURFACE (see model.py / refinement.md / mapping.md):
#
#   attrs_to_keep(present: List[int], x_attrs: int, x_pos: int) -> int
#     Requires Acc(list_pred(present), 1/2)            <-- READ-ONLY input (half perm)
#     Requires x_pos == -1 or (0 <= x_pos < len(present))
#     Requires Implies(0 <= x_pos < len(present), present[x_pos] == x_attrs)
#     Requires Implies(x_pos == -1, x_attrs == 0)
#     Ensures  Acc(list_pred(present), 1/2)            <-- frame: caller keeps its half
#     Ensures  Result() == x_attrs                     <-- LOAD-BEARING
#     impl:    return x_attrs
#
#   This models the keep_attrs callback of xarray.where (keep_attrs is True):
#     gold:  lambda attrs, context: getattr(x, "attrs", {})   (x's OWN attrs)
#     bug :  lambda attrs, context: attrs[1]                   (constant offset 1)
#   `present` = [a.attrs for a in objs] (the DataArray inputs, in arg order);
#   `x_attrs` = getattr(x,"attrs",{}) (0 for a scalar x); `x_pos` = where x's
#   mapping sits in `present` (-1 when x is a scalar, so absent from `present`).
#   The discriminator is the SCALAR second argument (issue: IndexError): then
#   x_pos == -1, x_attrs == 0, yet present may still have length >= 2 (other
#   DataArray args), so the buggy constant read present[1] is out of place / out
#   of range.
#
#   GROUNDED, NOT AN ORACLE ECHO: the load-bearing postcondition Result()==x_attrs
#   is pinned directly to an INPUT PARAMETER (x_attrs), fully unfolded — there is
#   no opaque @Pure answer-key / exact marker to echo without doing the work, and
#   the cheapest honest impl IS the gold `return x_attrs`. The ungrounded-oracle
#   echo class is therefore N/A; the positive control is a branch-reorder +
#   typed-local reshape that stays correct (see 'assessment').
#
#   No @ContractOnly axioms, no @Pure helpers, no deep-model A-reference
#   (meta.axioms == [], deep_model_references == []). getattr(x,"attrs",{}) is the
#   elementary "object's own attrs, else {}" fact captured by the x_attrs param,
#   not a library callee to validate against. Hence AXIOM_TESTS = [].
from pathlib import Path

INSTANCE = "pydata__xarray-6461"
FLOAT_ENCODING = None  # meta.json float_encoding == null

_BASE = (Path(__file__).parent / "model.py").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# ===========================================================================
# The ONE impl region. spec_view elides everything between (and including) the
# # impl-start / # impl-end markers, so editing only the body line BELOW keeps
# spec_signature (hence same_spec) byte-identical. The full region is a unique
# anchor; we replace only the inner `return x_attrs` line.
# ===========================================================================
_IMPL_GOLD = "    # impl-start\n    return x_attrs\n    # impl-end"
assert _IMPL_GOLD in _BASE, "impl anchor drift: gold impl region not verbatim"
assert _BASE.count(_IMPL_GOLD) == 1, "impl anchor not unique"


def _impl(body_lines):
    # body_lines: a list of source lines (no leading 4-space indent baked in;
    # they are supplied already indented). Wrap them between the markers.
    return "    # impl-start\n" + "\n".join(body_lines) + "\n    # impl-end"


# ---------------------------------------------------------------------------
# (1) POSITIVE CONTROL — structurally different but CORRECT (verify).
# Branch on x_pos and route through a typed local; BOTH branches return the same
# value x_attrs (via the local `keep`). Uses the precondition facts that hold on
# each branch (x_attrs == 0 on the scalar branch; present[x_pos] == x_attrs on
# the in-list branch) — kept as Asserts so the proof stays valid. No loop / fold
# lemma is involved. If a faithful correct impl could NOT verify => SPEC-TOO-STRONG.
# ---------------------------------------------------------------------------
_IMPL_POS = _impl([
    "    keep = x_attrs  # type: int",
    "    if x_pos == -1:",
    "        Assert(x_attrs == 0)",
    "        return keep",
    "    Assert(0 <= x_pos and x_pos < len(present))",
    "    Assert(present[x_pos] == x_attrs)",
    "    return keep",
])

# ---------------------------------------------------------------------------
# (2) ADMISSIBILITY — the precondition admits a normal F2P-shaped input (verify).
# Cannot add a top-level caller (that leaves the impl region and breaks
# same_spec). Instead, in-region: read the half-permission input `present`
# (len(present)) and re-derive the three Requires facts as Asserts (they must be
# dischargeable from the precondition), then reach a NORMAL non-raising return.
# This exercises BOTH F2P configurations the spec must admit: the all-DataArray
# case (x_pos in range, present[x_pos] == x_attrs) and the scalar second-arg case
# (x_pos == -1, x_attrs == 0). If the Requires were vacuous / over-strong the
# impl could not both consume the half-permission and return => PRECOND-TOO-STRONG.
# ---------------------------------------------------------------------------
_IMPL_ADMISS = _impl([
    "    Assert(len(present) >= 0)  # half-permission read of `present` is usable",
    "    Assert(x_pos == -1 or (0 <= x_pos and x_pos < len(present)))",
    "    Assert(Implies(0 <= x_pos and x_pos < len(present), present[x_pos] == x_attrs))",
    "    Assert(Implies(x_pos == -1, x_attrs == 0))",
    "    return x_attrs",
])

# ---------------------------------------------------------------------------
# (3) FRAME-MUTATION — write into the read-only half-permission input (reject).
# MANDATORY: `present` is held only at Acc(list_pred(present), 1/2). In the
# guarded branch the index x_pos is in-bounds and the write is VALUE-NEUTRAL
# (the precondition pins present[x_pos] == x_attrs, so writing x_attrs changes
# nothing observable). The postcondition Result() == x_attrs is still satisfied
# by the `return x_attrs`. Yet a write to a list element needs FULL list_pred
# permission; with only the half the Requires grants, Nagini rejects for
# INSUFFICIENT PERMISSION. The spec/Ensures are kept verbatim so the rejection is
# attributable to the write, not to any spec change. A byte-fuzzer never thinks
# to mutate the input.
# ---------------------------------------------------------------------------
_IMPL_FRAME = _impl([
    "    if 0 <= x_pos and x_pos < len(present):",
    "        # FRAME MUTATION: write back into the read-only half-permission input.",
    "        present[x_pos] = x_attrs",
    "    return x_attrs",
])

# ---------------------------------------------------------------------------
# (4) PARTIAL-DOMAIN — bounds-guarded constant-offset read (reject). THIS IS THE
# SEMANTIC HALF OF THE GOLD BUG (model_prepatch_2): read the entry at the CONSTANT
# offset 1 whenever the list is long enough, else fall back to the empty mapping.
# Correct exactly when x's mapping happens to sit at offset 1 (x_pos == 1, the
# all-DataArray F2P case) but WRONG on the sub-domain where it does not — most
# importantly the scalar second argument (x_pos == -1, x_attrs == 0) when other
# DataArray args make len(present) >= 2: it then returns present[1] (some other
# arg's mapping) != 0 == x_attrs. Violates the load-bearing Result() == x_attrs.
# ---------------------------------------------------------------------------
_IMPL_OFFSET_GUARDED = _impl([
    "    if len(present) >= 2:",
    "        return present[1]",
    "    return 0",
])

# ---------------------------------------------------------------------------
# (5) PARTIAL-DOMAIN — unguarded constant-offset read (reject). THIS IS THE
# RAISE HALF OF THE GOLD BUG (model_prepatch / the literal pre-patch body
# `attrs[1]`): read offset 1 unconditionally. When the second argument is a
# scalar with fewer than two DataArray inputs (len(present) < 2) the access
# present[1] is out of range — exactly the reported IndexError. Nagini cannot
# discharge the in-bounds precondition of present[1] (len(present) may be 0 or 1),
# so it rejects. Supporting case: it also confirms the spec senses the raise face
# of the bug, not only the wrong-value face.
# ---------------------------------------------------------------------------
_IMPL_OFFSET_UNGUARDED = _impl([
    "    return present[1]",
])


SPEC_TESTS = [
    {
        "id": "pos-control-branch-typed-local",
        "kind": "soundness",
        "expect": "verify",
        "module": _swap(_BASE, _IMPL_GOLD, _IMPL_POS),
        "rationale": "Structurally different but correct: branch on x_pos and route "
                     "through a typed local `keep`; both branches return x_attrs. The "
                     "branch-local precondition facts (x_attrs == 0 on the scalar "
                     "branch; present[x_pos] == x_attrs in range) are kept as Asserts so "
                     "the proof stays valid. No loop / fold lemma. Must verify, else "
                     "SPEC-TOO-STRONG (a faithful correct impl rejected).",
    },
    {
        "id": "admissibility-readonly-present-both-configs",
        "kind": "admissibility",
        "expect": "verify",
        "module": _swap(_BASE, _IMPL_GOLD, _IMPL_ADMISS),
        "rationale": "Reads the half-permission input `present` (len) and re-derives "
                     "all three Requires facts as Asserts, then reaches a normal "
                     "non-raising return. Covers both F2P configurations the spec must "
                     "admit: all-DataArray (x_pos in range) and scalar second arg "
                     "(x_pos == -1, x_attrs == 0). If a Requires were vacuous / "
                     "over-strong the impl could not both consume the permission and "
                     "return => PRECOND-TOO-STRONG. Source: the four Requires clauses.",
    },
    {
        "id": "frame-mutation-write-present",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _IMPL_GOLD, _IMPL_FRAME),
        "refinement": "A faithful real patch in which the keep_attrs callback wrote "
                      "back into its `attrs` list (e.g. attrs[i] = attrs[i]) would "
                      "mutate the [a.attrs for a in objs] list that apply_ufunc / "
                      "merge_attrs still holds and reads while assembling the output "
                      "DataArray's attributes. The gold callback only READS / returns "
                      "getattr(x,'attrs',{}) and never touches `attrs`; a mutating "
                      "callback would corrupt the very attribute mappings the F2P "
                      "assertion (actual.attrs == {'attr': 'x'} / actual.attrs == {}) "
                      "is built from, so it would not faithfully resolve test_where_attrs.",
        "rationale": "attrs_to_keep holds only Acc(list_pred(present), 1/2). The write "
                     "present[x_pos] = x_attrs (in-bounds via the guard, value-neutral "
                     "since the precondition pins present[x_pos] == x_attrs) needs FULL "
                     "list_pred permission => Nagini rejects for INSUFFICIENT "
                     "PERMISSION. The postcondition Result() == x_attrs is still met by "
                     "`return x_attrs`, so the rejection is attributable solely to the "
                     "write. Source: the permission system + the Acc(...,1/2) Requires.",
    },
    {
        "id": "partial-domain-constant-offset-guarded",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _IMPL_GOLD, _IMPL_OFFSET_GUARDED),
        "refinement": "This IS the bug's semantic half (the pre-patch body, "
                      "bounds-guarded): keep_attrs = lambda attrs, context: attrs[1] "
                      "with a length guard. It returns the second argument's mapping "
                      "ONLY when x sits at offset 1 of [a.attrs for a in objs]; for the "
                      "F2P scalar scenario xr.where(cond, 1, 0, keep_attrs=True) the "
                      "scalar x=1 is absent from objs (x_pos == -1) yet present can be "
                      "non-trivial, so attrs[1] is some other arg's mapping, not the "
                      "expected {} (x_attrs == 0). test_where_attrs asserts "
                      "actual.attrs == {}, so the faithful patch does NOT resolve.",
        "rationale": "Returns present[1] when len(present) >= 2 else 0. On the "
                     "x_pos != 1 sub-domain (notably the scalar x_pos == -1 with "
                     "len(present) >= 2) present[1] != x_attrs, so the load-bearing "
                     "Result() == x_attrs fails. Source: the Result() == x_attrs "
                     "postcondition clause (the spec rejects any constant-offset read).",
    },
    {
        "id": "partial-domain-constant-offset-unguarded-raise",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _IMPL_GOLD, _IMPL_OFFSET_UNGUARDED),
        "refinement": "This IS the literal pre-patch body keep_attrs = lambda attrs, "
                      "context: attrs[1] (model_prepatch). For the reported scalar "
                      "scenario xr.where(DataArray>0, 1, 0) the [a.attrs for a in objs] "
                      "list has length 1 (only cond is a DataArray), so attrs[1] raises "
                      "IndexError: list index out of range — the exact crash the issue "
                      "reports. A faithful patch that kept attrs[1] would still crash on "
                      "the F2P scalar case and NOT resolve test_where_attrs.",
        "rationale": "Unconditional present[1]: Nagini cannot discharge the in-bounds "
                     "precondition of the list access because len(present) may be 0 or "
                     "1 (the scalar case), so it rejects on the array-access bounds "
                     "obligation (the verifier analogue of the IndexError). Supporting "
                     "case for the raise face of the bug. Source: the list-access "
                     "in-bounds proof obligation under Acc(list_pred(present), 1/2).",
    },
]

# No Docker AXIOM_TESTS: meta.axioms == [] (no @ContractOnly axiom) and
# deep_model_references == [] (no A-reference deep model to validate against a
# real callee). The changed operation getattr(x,"attrs",{}) is modelled deeply as
# the x_attrs parameter — the elementary "object's own attrs, else {}" fact, not
# a library callee whose behaviour needs axiom-soundness / containment probes.
# The axiom lane is genuinely vacuous here (G-AX == vacuous in meta.json). See
# 'assessment' in the structured return.
AXIOM_TESTS = []
