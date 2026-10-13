# properties.py — PBT falsification battery for sphinx-doc__sphinx-8056.
#
# NOT a Nagini module; a record of adversarial cases the runner
# (swebench_nagini.pbt) executes and stamps RESULT on. Spec cases are full
# model.py variants that share the FROZEN spec (region-surgery: every edit lives
# ONLY inside the single # impl-start / # impl-end region — which spec_view
# elides, nested invariants included — so same_spec holds by construction) and
# are checked by Nagini verify. Axiom cases are real-callee probes run in the
# instance Docker image.
#
# DEFENDED SURFACE (what this spec protects — see model.py / refinement.md):
#
#   emitted_names(name: List[int], multiple, type_nonempty, desc_nonempty)
#                                                          -> PSeq[PSeq[int]]
#     Requires Acc(list_pred(name), 1/2)   <-- READ-ONLY input (half permission)
#     Ensures  Acc(list_pred(name), 1/2)   <-- frame: caller keeps its half
#     Result() is a PURE PSeq[PSeq[int]] (no heap permission).
#
#   The postcondition has two regimes, gated by  E := multiple and len(name)>0 :
#
#     [E]  EXPANSION regime (the per-comma split — the FIX):
#       (P1)  len(Result()) == num_commas(ToSeq(name)) + 1
#       (P2)  Forall k in [0,len): Result()[k] == trim(split_on_comma(name)[k])
#     [not E]  LEGACY regime (single verbatim entry or drop):
#       (P3)  len(Result()) <= 1
#       (P4)  (len(name)>0 or type_nonempty or desc_nonempty) => len(Result())==1
#       (P5)  (all three empty)                                => len(Result())==0
#       (P6)  len(Result())==1  => Result()[0] == ToSeq(name)   <-- VERBATIM
#
#   ORACLE GROUNDING: P2's oracle  trim(split_on_comma(ToSeq(name))[k])  is a
#   PURE function OF THE INPUT `name` (split/trim are @ContractOnly stand-ins for
#   str.split(',')/str.strip(), fully determined by the input). It is NOT an
#   opaque answer-key. So "echo the oracle" == "produce the correct value": there
#   is no WRONG ungrounded-oracle echo to build. The ungrounded-oracle class is
#   therefore N/A here; in its place the positive control is the cheapest honest
#   impl (branch reorder + local-variable reshape). See 'assessment'.
#
#   BEHAVIOURAL DISCRIMINATOR (F2P test_multiple_parameters, both configs):
#     * napoleon_use_param=True  => multiple=True  => "x1, x2" expands to two
#       :param entries x1 and x2 (P1 count = num_commas+1 = 2; P2 each trimmed).
#     * napoleon_use_param=False => multiple=False => the field stays ONE
#       verbatim entry "x1, x2" (P3/P6). The rivals below each break exactly one
#       of these regimes on a sub-domain the F2P input reaches.
#
#   AXIOMS: three @ContractOnly A-consumed axioms (num_commas, split_on_comma,
#   trim) standing in for the UNCHANGED stdlib callees str.count(',') /
#   str.split(',') / str.strip(). They have a real-callee soundness check
#   (axiom_check.py / G-AX). The AXIOM_TESTS below re-run that check in the
#   instance image as a soundness probe and add a caller-domain containment probe
#   (the model only ever passes the SAME PSeq[int] of code points to all three).
from pathlib import Path

INSTANCE = "sphinx-doc__sphinx-8056"
FLOAT_ENCODING = None  # meta.json float_encoding == null

_BASE = (Path(__file__).parent / "model.py").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# ===========================================================================
# The gold impl body (verbatim anchor, the WHOLE # impl-start..# impl-end
# interior). Editing only this string keeps spec_view (hence same_spec)
# byte-identical, because spec_view elides everything between the impl markers.
# ===========================================================================
_IMPL_GOLD = """    result = PSeq(ToSeq(name)).take(0)  # type: PSeq[PSeq[int]]
    if multiple and len(name) > 0:
        parts = split_on_comma(ToSeq(name))  # type: PSeq[PSeq[int]]
        n = num_commas(ToSeq(name)) + 1
        Assert(len(parts) == n)
        i = 0
        while i < n:
            # invariants-start
            Invariant(Acc(list_pred(name), 1 / 2))
            Invariant(multiple and len(name) > 0)
            Invariant(0 <= i and i <= n)
            Invariant(n == num_commas(ToSeq(name)) + 1)
            Invariant(parts == split_on_comma(ToSeq(name)))
            Invariant(len(result) == i)
            Invariant(Forall(int, lambda k: (
                Implies(0 <= k and k < i, result[k] == trim(parts[k])),
                [[result[k]]])))
            Invariant(MustTerminate(n - i + 1))
            # invariants-end
            piece = trim(parts[i])  # type: PSeq[int]
            old_result = result  # type: PSeq[PSeq[int]]
            result = result + PSeq(piece)
            Assert(len(result) == i + 1)
            Assert(result[i] == piece)
            Assert(Forall(int, lambda k: (
                Implies(0 <= k and k < i, result[k] == old_result[k]),
                [[result[k]]])))
            i = i + 1
        return result
    else:
        if len(name) > 0 or type_nonempty or desc_nonempty:
            result = result + PSeq(ToSeq(name))
            Assert(len(result) == 1)
            Assert(result[0] == ToSeq(name))
        return result"""

assert _IMPL_GOLD in _BASE, "impl anchor drift: emitted_names body not verbatim"


# ===========================================================================
# (1) POSITIVE CONTROL — structurally different but CORRECT (expect verify).
# Branch REORDER: test the LEGACY regime first via `not (multiple and len>0)`,
# then the EXPANSION regime in the else. A local-variable reshape inside the
# legacy branch (stage the verbatim name through a named local `whole`) and a
# reorder of the two trailing framing asserts in the loop. NO loop-direction
# flip and NO fold lemma is introduced (would need an f(a+b)==f(a)+f(b) the
# verifier can't auto-discharge). Every gold proof obligation that is still
# needed is kept VERBATIM (the loop invariants, len/element/prefix asserts).
# If a faithful correct impl cannot verify against this spec => SPEC-TOO-STRONG.
# ===========================================================================
_IMPL_POS = """    result = PSeq(ToSeq(name)).take(0)  # type: PSeq[PSeq[int]]
    if not (multiple and len(name) > 0):
        if len(name) > 0 or type_nonempty or desc_nonempty:
            whole = ToSeq(name)  # type: PSeq[int]
            result = result + PSeq(whole)
            Assert(len(result) == 1)
            Assert(result[0] == ToSeq(name))
        return result
    else:
        parts = split_on_comma(ToSeq(name))  # type: PSeq[PSeq[int]]
        n = num_commas(ToSeq(name)) + 1
        Assert(len(parts) == n)
        i = 0
        while i < n:
            # invariants-start
            Invariant(Acc(list_pred(name), 1 / 2))
            Invariant(multiple and len(name) > 0)
            Invariant(0 <= i and i <= n)
            Invariant(n == num_commas(ToSeq(name)) + 1)
            Invariant(parts == split_on_comma(ToSeq(name)))
            Invariant(len(result) == i)
            Invariant(Forall(int, lambda k: (
                Implies(0 <= k and k < i, result[k] == trim(parts[k])),
                [[result[k]]])))
            Invariant(MustTerminate(n - i + 1))
            # invariants-end
            piece = trim(parts[i])  # type: PSeq[int]
            old_result = result  # type: PSeq[PSeq[int]]
            result = result + PSeq(piece)
            Assert(Forall(int, lambda k: (
                Implies(0 <= k and k < i, result[k] == old_result[k]),
                [[result[k]]])))
            Assert(result[i] == piece)
            Assert(len(result) == i + 1)
            i = i + 1
        return result"""

# ===========================================================================
# (2) ADMISSIBILITY — the precondition admits a normal F2P-shaped input
# (expect verify). Cannot add a top-level caller (that would leave the impl
# region and break same_spec). Instead, in-region: re-derive that the half-
# permission input `name` is usable (read len(name) and ToSeq(name)) and that a
# normal (non-raising) return is reachable, then run the gold body unchanged. If
# the Requires Acc(list_pred(name),1/2) were vacuous / over-strong, the impl
# could not both READ the input and return => PRECOND-TOO-STRONG.
# ===========================================================================
_IMPL_ADMISS = """    # admissibility: the half-permission input `name` is readable (len + ToSeq)
    # and a normal non-raising return is reachable for an F2P-shaped input.
    Assert(len(name) >= 0)
    Assert(ToSeq(name) == ToSeq(name))
    result = PSeq(ToSeq(name)).take(0)  # type: PSeq[PSeq[int]]
    if multiple and len(name) > 0:
        parts = split_on_comma(ToSeq(name))  # type: PSeq[PSeq[int]]
        n = num_commas(ToSeq(name)) + 1
        Assert(len(parts) == n)
        i = 0
        while i < n:
            # invariants-start
            Invariant(Acc(list_pred(name), 1 / 2))
            Invariant(multiple and len(name) > 0)
            Invariant(0 <= i and i <= n)
            Invariant(n == num_commas(ToSeq(name)) + 1)
            Invariant(parts == split_on_comma(ToSeq(name)))
            Invariant(len(result) == i)
            Invariant(Forall(int, lambda k: (
                Implies(0 <= k and k < i, result[k] == trim(parts[k])),
                [[result[k]]])))
            Invariant(MustTerminate(n - i + 1))
            # invariants-end
            piece = trim(parts[i])  # type: PSeq[int]
            old_result = result  # type: PSeq[PSeq[int]]
            result = result + PSeq(piece)
            Assert(len(result) == i + 1)
            Assert(result[i] == piece)
            Assert(Forall(int, lambda k: (
                Implies(0 <= k and k < i, result[k] == old_result[k]),
                [[result[k]]])))
            i = i + 1
        return result
    else:
        if len(name) > 0 or type_nonempty or desc_nonempty:
            result = result + PSeq(ToSeq(name))
            Assert(len(result) == 1)
            Assert(result[0] == ToSeq(name))
        return result"""

# ===========================================================================
# (3) FRAME-MUTATION — write to the read-only input `name` (expect reject).
# MANDATORY: `name` is held only with Acc(list_pred(name), 1/2). Inside the
# EXPANSION branch `multiple and len(name) > 0` holds, so index 0 is in bounds;
# the write  name[0] = name[0]  is value-NEUTRAL (writes back the same element)
# but needs FULL permission. With only the half-permission the Requires grants,
# Nagini rejects for INSUFFICIENT PERMISSION. The gold invariants/asserts are
# kept VERBATIM so the rejection is attributable to the write, not a spec change.
# A byte-fuzzer never thinks to mutate the input — this is the #1 weakness class.
# ===========================================================================
_IMPL_FRAME = """    result = PSeq(ToSeq(name)).take(0)  # type: PSeq[PSeq[int]]
    if multiple and len(name) > 0:
        parts = split_on_comma(ToSeq(name))  # type: PSeq[PSeq[int]]
        n = num_commas(ToSeq(name)) + 1
        Assert(len(parts) == n)
        # FRAME MUTATION: write back into the read-only half-permission input.
        # In-bounds (len(name) > 0 on this branch); value-neutral; yet needs
        # FULL permission, which the Requires does not grant.
        name[0] = name[0]
        i = 0
        while i < n:
            # invariants-start
            Invariant(Acc(list_pred(name), 1 / 2))
            Invariant(multiple and len(name) > 0)
            Invariant(0 <= i and i <= n)
            Invariant(n == num_commas(ToSeq(name)) + 1)
            Invariant(parts == split_on_comma(ToSeq(name)))
            Invariant(len(result) == i)
            Invariant(Forall(int, lambda k: (
                Implies(0 <= k and k < i, result[k] == trim(parts[k])),
                [[result[k]]])))
            Invariant(MustTerminate(n - i + 1))
            # invariants-end
            piece = trim(parts[i])  # type: PSeq[int]
            old_result = result  # type: PSeq[PSeq[int]]
            result = result + PSeq(piece)
            Assert(len(result) == i + 1)
            Assert(result[i] == piece)
            Assert(Forall(int, lambda k: (
                Implies(0 <= k and k < i, result[k] == old_result[k]),
                [[result[k]]])))
            i = i + 1
        return result
    else:
        if len(name) > 0 or type_nonempty or desc_nonempty:
            result = result + PSeq(ToSeq(name))
            Assert(len(result) == 1)
            Assert(result[0] == ToSeq(name))
        return result"""

# ===========================================================================
# (4) PARTIAL-DOMAIN / count off-by-one — drop the LAST run (expect reject).
# Loop `while i < n - 1` builds only `num_commas` entries instead of
# `num_commas + 1`. Agrees with gold on runs with no comma (n==1 => 0 entries...
# actually diverges there too) — it always emits one fewer entry than required.
# Violates P1: len(Result()) == num_commas(ToSeq(name)) + 1. The framing asserts
# are kept verbatim; the failure is the postcondition count, a SPEC reason.
# ===========================================================================
_IMPL_COUNT = """    result = PSeq(ToSeq(name)).take(0)  # type: PSeq[PSeq[int]]
    if multiple and len(name) > 0:
        parts = split_on_comma(ToSeq(name))  # type: PSeq[PSeq[int]]
        n = num_commas(ToSeq(name)) + 1
        Assert(len(parts) == n)
        i = 0
        while i < n - 1:
            # invariants-start
            Invariant(Acc(list_pred(name), 1 / 2))
            Invariant(multiple and len(name) > 0)
            Invariant(0 <= i and i <= n)
            Invariant(n == num_commas(ToSeq(name)) + 1)
            Invariant(parts == split_on_comma(ToSeq(name)))
            Invariant(len(result) == i)
            Invariant(Forall(int, lambda k: (
                Implies(0 <= k and k < i, result[k] == trim(parts[k])),
                [[result[k]]])))
            Invariant(MustTerminate(n - i + 1))
            # invariants-end
            piece = trim(parts[i])  # type: PSeq[int]
            old_result = result  # type: PSeq[PSeq[int]]
            result = result + PSeq(piece)
            Assert(len(result) == i + 1)
            Assert(result[i] == piece)
            Assert(Forall(int, lambda k: (
                Implies(0 <= k and k < i, result[k] == old_result[k]),
                [[result[k]]])))
            i = i + 1
        return result
    else:
        if len(name) > 0 or type_nonempty or desc_nonempty:
            result = result + PSeq(ToSeq(name))
            Assert(len(result) == 1)
            Assert(result[0] == ToSeq(name))
        return result"""

# ===========================================================================
# (5) PARTIAL-DOMAIN / no-trim — emit each run UNTRIMMED (expect reject).
# `result + PSeq(parts[i])` instead of `result + PSeq(trim(parts[i]))`. This is
# exactly the bug of forgetting `.strip()` in the patched loop. The count P1 is
# still right; P2 (Result()[k] == trim(split_on_comma(name)[k])) fails on any run
# with surrounding whitespace — e.g. the F2P "x1, x2" splits to ["x1"," x2"], so
# run 1 would be " x2" not "x2". The loop invariant pins result[k]==trim(parts[k])
# but the impl now stores parts[k]; on a padded run those differ, so the
# invariant (a postcondition-mirroring obligation) cannot close.
# ===========================================================================
_IMPL_NOTRIM = """    result = PSeq(ToSeq(name)).take(0)  # type: PSeq[PSeq[int]]
    if multiple and len(name) > 0:
        parts = split_on_comma(ToSeq(name))  # type: PSeq[PSeq[int]]
        n = num_commas(ToSeq(name)) + 1
        Assert(len(parts) == n)
        i = 0
        while i < n:
            # invariants-start
            Invariant(Acc(list_pred(name), 1 / 2))
            Invariant(multiple and len(name) > 0)
            Invariant(0 <= i and i <= n)
            Invariant(n == num_commas(ToSeq(name)) + 1)
            Invariant(parts == split_on_comma(ToSeq(name)))
            Invariant(len(result) == i)
            Invariant(Forall(int, lambda k: (
                Implies(0 <= k and k < i, result[k] == trim(parts[k])),
                [[result[k]]])))
            Invariant(MustTerminate(n - i + 1))
            # invariants-end
            piece = parts[i]  # type: PSeq[int]
            old_result = result  # type: PSeq[PSeq[int]]
            result = result + PSeq(piece)
            Assert(len(result) == i + 1)
            Assert(result[i] == piece)
            Assert(Forall(int, lambda k: (
                Implies(0 <= k and k < i, result[k] == old_result[k]),
                [[result[k]]])))
            i = i + 1
        return result
    else:
        if len(name) > 0 or type_nonempty or desc_nonempty:
            result = result + PSeq(ToSeq(name))
            Assert(len(result) == 1)
            Assert(result[0] == ToSeq(name))
        return result"""

# ===========================================================================
# (6) PARTIAL-DOMAIN / legacy-branch splits anyway — verbatim violation
# (expect reject). In the LEGACY (not E) branch, emit only the FIRST comma run
# split_on_comma(name)[0] instead of the whole verbatim name. The count P3/P4 is
# satisfied (still <= 1, and ==1 when nonempty), but P6 (Result()[0] ==
# ToSeq(name)) fails on any name containing a comma — e.g. the F2P non-use_param
# config keeps "x1, x2" whole, but this emits "x1". The Assert result[0] ==
# ToSeq(name) (a postcondition-mirroring obligation) cannot be discharged.
# ===========================================================================
_IMPL_LEGACYSPLIT = """    result = PSeq(ToSeq(name)).take(0)  # type: PSeq[PSeq[int]]
    if multiple and len(name) > 0:
        parts = split_on_comma(ToSeq(name))  # type: PSeq[PSeq[int]]
        n = num_commas(ToSeq(name)) + 1
        Assert(len(parts) == n)
        i = 0
        while i < n:
            # invariants-start
            Invariant(Acc(list_pred(name), 1 / 2))
            Invariant(multiple and len(name) > 0)
            Invariant(0 <= i and i <= n)
            Invariant(n == num_commas(ToSeq(name)) + 1)
            Invariant(parts == split_on_comma(ToSeq(name)))
            Invariant(len(result) == i)
            Invariant(Forall(int, lambda k: (
                Implies(0 <= k and k < i, result[k] == trim(parts[k])),
                [[result[k]]])))
            Invariant(MustTerminate(n - i + 1))
            # invariants-end
            piece = trim(parts[i])  # type: PSeq[int]
            old_result = result  # type: PSeq[PSeq[int]]
            result = result + PSeq(piece)
            Assert(len(result) == i + 1)
            Assert(result[i] == piece)
            Assert(Forall(int, lambda k: (
                Implies(0 <= k and k < i, result[k] == old_result[k]),
                [[result[k]]])))
            i = i + 1
        return result
    else:
        if len(name) > 0 or type_nonempty or desc_nonempty:
            first = split_on_comma(ToSeq(name))[0]  # type: PSeq[int]
            result = result + PSeq(first)
            Assert(len(result) == 1)
        return result"""

# ===========================================================================
# (7) PARTIAL-DOMAIN / empty-field not dropped (expect reject). In the LEGACY
# branch, ALWAYS append the (empty) verbatim name, dropping the keep-guard. When
# all three are empty (len(name)==0, type/desc both False) the gold drops the
# field (P5: len==0) but this emits one empty entry. Violates P5. This is the
# bug of removing the legacy `if _name or _type or _desc` guard. The count P3
# (<=1) still holds; P5 (==0 when all empty) fails. The Assert len(result)==0 in
# the all-empty case cannot be discharged.
# ===========================================================================
_IMPL_NODROP = """    result = PSeq(ToSeq(name)).take(0)  # type: PSeq[PSeq[int]]
    if multiple and len(name) > 0:
        parts = split_on_comma(ToSeq(name))  # type: PSeq[PSeq[int]]
        n = num_commas(ToSeq(name)) + 1
        Assert(len(parts) == n)
        i = 0
        while i < n:
            # invariants-start
            Invariant(Acc(list_pred(name), 1 / 2))
            Invariant(multiple and len(name) > 0)
            Invariant(0 <= i and i <= n)
            Invariant(n == num_commas(ToSeq(name)) + 1)
            Invariant(parts == split_on_comma(ToSeq(name)))
            Invariant(len(result) == i)
            Invariant(Forall(int, lambda k: (
                Implies(0 <= k and k < i, result[k] == trim(parts[k])),
                [[result[k]]])))
            Invariant(MustTerminate(n - i + 1))
            # invariants-end
            piece = trim(parts[i])  # type: PSeq[int]
            old_result = result  # type: PSeq[PSeq[int]]
            result = result + PSeq(piece)
            Assert(len(result) == i + 1)
            Assert(result[i] == piece)
            Assert(Forall(int, lambda k: (
                Implies(0 <= k and k < i, result[k] == old_result[k]),
                [[result[k]]])))
            i = i + 1
        return result
    else:
        result = result + PSeq(ToSeq(name))
        Assert(len(result) == 1)
        Assert(result[0] == ToSeq(name))
        return result"""


SPEC_TESTS = [
    {
        "id": "pos-control-branch-reorder",
        "kind": "soundness",
        "expect": "verify",
        "module": _swap(_BASE, _IMPL_GOLD, _IMPL_POS),
        "rationale": "Structurally different but correct: the LEGACY regime is "
                     "tested first via `not (multiple and len(name)>0)` and the "
                     "EXPANSION regime moved to the else; the legacy verbatim name "
                     "is staged through a named local `whole`; the two trailing loop "
                     "framing asserts are reordered (prefix-preservation before the "
                     "per-element pin). NO loop-direction flip and NO fold lemma is "
                     "introduced (forward split-loop kept). Every still-needed gold "
                     "proof obligation is kept verbatim (all loop invariants, the "
                     "len/element/prefix asserts, the legacy len==1 / result[0]==name "
                     "asserts). Must verify, else SPEC-TOO-STRONG.",
    },
    {
        "id": "admissibility-readonly-name",
        "kind": "admissibility",
        "expect": "verify",
        "module": _swap(_BASE, _IMPL_GOLD, _IMPL_ADMISS),
        "rationale": "Re-derives in-region that the half-permission input `name` is "
                     "usable (Assert len(name)>=0 and ToSeq(name)==ToSeq(name)) and "
                     "reaches a normal non-raising return for an F2P-shaped input, "
                     "then runs the gold body unchanged. If Acc(list_pred(name),1/2) "
                     "were vacuous or over-strong the impl could not both READ the "
                     "input and return => PRECOND-TOO-STRONG. Source: the sole "
                     "Requires Acc(list_pred(name),1/2).",
    },
    {
        "id": "frame-mutation-write-name",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _IMPL_GOLD, _IMPL_FRAME),
        "refinement": "A faithful real patch in which the per-field body WROTE back "
                      "into `_name` (e.g. the consumed field's name string list) "
                      "would mutate state the surrounding _consume_fields loop / the "
                      "caller still relies on. The gold patch only READS _name "
                      "(_name.split(','), name.strip()) and never mutates the consumed "
                      "field; _type/_desc ride along verbatim and the loop keeps "
                      "consuming subsequent fields. A mutating variant would corrupt "
                      "the field data the F2P-rendered output is built from and would "
                      "not faithfully resolve test_multiple_parameters.",
        "rationale": "emitted_names holds only Acc(list_pred(name),1/2). The write "
                     "name[0]=name[0] (in-bounds on the multiple-and-nonempty branch, "
                     "value-neutral) needs FULL permission => Nagini rejects for "
                     "INSUFFICIENT PERMISSION. Source: the permission system + the "
                     "Acc(list_pred(name),1/2) Requires. Gold invariants/asserts kept "
                     "verbatim so the rejection is attributable to the write.",
    },
    {
        "id": "partial-domain-count-off-by-one",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _IMPL_GOLD, _IMPL_COUNT),
        "refinement": "A faithful real patch whose new loop dropped the last run "
                      "(e.g. `for name in _name.split(',')[:-1]`) would emit only "
                      "`commas` entries. For the F2P \"x1, x2\" under "
                      "napoleon_use_param=True it emits ONE :param (x1) where the test "
                      "asserts TWO (x1 AND x2). test_multiple_parameters FAILS, so the "
                      "patch does not resolve.",
        "rationale": "Loop `while i < n-1` builds num_commas entries, one fewer than "
                     "required, so P1 (len(Result()) == num_commas(ToSeq(name)) + 1) "
                     "fails. Source: the count postcondition clause P1.",
    },
    {
        "id": "partial-domain-no-trim",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _IMPL_GOLD, _IMPL_NOTRIM),
        "refinement": "This IS the patched loop with the `.strip()` forgotten "
                      "(`fields.append((name, _type, _desc))` instead of "
                      "`name.strip()`). For the F2P \"x1, x2\" the runs are "
                      "['x1', ' x2']; without trim the second :param name is ' x2' "
                      "(leading space) not 'x2', so the rendered ':param x2:' line "
                      "mismatches and test_multiple_parameters FAILS. The faithful "
                      "patch does not resolve.",
        "rationale": "The loop stores parts[i] (untrimmed) but the invariant / "
                     "postcondition P2 pins result[k] == trim(split_on_comma(name)[k]); "
                     "on any run with surrounding whitespace those differ, so the "
                     "content obligation cannot close. Source: the content "
                     "postcondition clause P2 (and its mirroring loop invariant).",
    },
    {
        "id": "partial-domain-legacy-splits-anyway",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _IMPL_GOLD, _IMPL_LEGACYSPLIT),
        "refinement": "A faithful real patch that split the name even in the "
                      "non-`multiple` branch (e.g. always took the first run "
                      "`_name.split(',')[0]`) would, under napoleon_use_param=False, "
                      "emit the field as **x1** instead of the verbatim **x1, x2** the "
                      "F2P test asserts. test_multiple_parameters (the use_param=False "
                      "half) FAILS, so the patch does not resolve.",
        "rationale": "The legacy branch emits split_on_comma(name)[0] (the first run) "
                     "instead of the whole name, so P6 (Result()[0] == ToSeq(name)) "
                     "fails on any name containing a comma; the Assert result[0] == "
                     "ToSeq(name) cannot be discharged. Source: the verbatim "
                     "postcondition clause P6.",
    },
    {
        "id": "partial-domain-empty-field-not-dropped",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _IMPL_GOLD, _IMPL_NODROP),
        "refinement": "A faithful real patch that dropped the legacy keep-guard "
                      "`elif _name or _type or _desc:` and always appended would emit "
                      "a spurious empty field entry for an entirely-empty field. The "
                      "downstream formatter renders one line per entry, so an extra "
                      "blank :param / Parameters line is produced where the gold emits "
                      "none, diverging from the asserted F2P output (and the 40 P2P "
                      "section-rendering tests). The faithful patch does not resolve.",
        "rationale": "The legacy branch always appends, so when len(name)==0 and "
                     "type_nonempty/desc_nonempty are both False it emits one entry "
                     "where P5 ((all empty) => len(Result())==0) requires zero; the "
                     "Assert len(result)==1 is reachable on the all-empty input where "
                     "P5 demands 0. Source: the drop postcondition clause P5.",
    },
]


# ===========================================================================
# AXIOM LANE — three @ContractOnly A-consumed axioms (num_commas, split_on_comma,
# trim) standing in for the UNCHANGED stdlib callees str.count(',') /
# str.split(',') / str.strip(). axiom_check.py (G-AX) already runs the real
# built-ins; these probes re-run that established check IN the instance image
# (soundness) and add a caller-domain containment argument (no library import is
# needed — the callees are pure CPython built-ins, the exact ops the gold patch
# calls). Probes are self-contained (stdlib only), open nothing, exit 0 iff sound.
# ===========================================================================

# Soundness probe: assert the REAL str.count/str.split/str.strip satisfy each
# axiom's Ensures, AND the composed model == the gold per-field computation, on
# boundary + fuzz inputs (incl. the F2P discriminator) across all flag combos.
_PROBE_SOUNDNESS = r'''
import random, sys

def check_num_commas(s):
    # Axiom: Result() >= 0 ; Implies(len==0, Result()==0).
    real = s.count(",")
    assert real >= 0, "count(',') negative on %r" % (s,)
    if s == "":
        assert real == 0, "count(',') on '' is %r" % (real,)

def check_split_len(s):
    # Axiom: len(split_on_comma(s)) == num_commas(s) + 1.
    parts = s.split(",")
    assert len(parts) == s.count(",") + 1, (
        "split length axiom unsound on %r: %d != %d"
        % (s, len(parts), s.count(",") + 1))

def check_trim(s):
    # Axiom: documented str.strip() behaviour (interior substring, non-ws
    # endpoints, idempotent).
    t = s.strip()
    assert t.strip() == t, "strip not idempotent on %r" % (s,)
    assert t in s, "strip result %r not a substring of %r" % (t, s)
    if t:
        assert not t[0].isspace() and not t[-1].isspace(), (
            "strip left surrounding whitespace on %r -> %r" % (s, t))
        assert s.lstrip().rstrip() == t

def model_emitted(name, multiple, type_ne, desc_ne):
    # model.py emitted_names computed with the REAL callees the axioms cover.
    if multiple and len(name) > 0:
        return [piece.strip() for piece in name.split(",")]
    if len(name) > 0 or type_ne or desc_ne:
        return [name]
    return []

def gold_consume(name, multiple, type_ne, desc_ne):
    # gold _consume_fields per-field body (names only; type/desc ride along).
    fields = []
    if multiple and name:
        for n in name.split(","):
            fields.append(n.strip())
    elif name or type_ne or desc_ne:
        fields.append(name)
    return fields

def check_composed(name, multiple, type_ne, desc_ne):
    m = model_emitted(name, multiple, type_ne, desc_ne)
    g = gold_consume(name, multiple, type_ne, desc_ne)
    assert m == g, ("model != gold on name=%r m=%r t=%r d=%r: %r vs %r"
                    % (name, multiple, type_ne, desc_ne, m, g))
    # re-assert the model.py postcondition clauses directly
    if multiple and len(name) > 0:
        assert len(m) == name.count(",") + 1            # P1
        parts = name.split(",")
        for k in range(len(m)):
            assert m[k] == parts[k].strip()             # P2
    else:
        assert len(m) <= 1                              # P3
        expect_one = (len(name) > 0 or type_ne or desc_ne)
        assert (len(m) == 1) == expect_one              # P4 / P5
        if len(m) == 1:
            assert m[0] == name                         # P6

def main():
    # F2P discriminator: "x1, x2" -> ["x1","x2"] (expand) / ["x1, x2"] (verbatim)
    assert model_emitted("x1, x2", True, False, True) == ["x1", "x2"]
    assert model_emitted("x1, x2", False, False, True) == ["x1, x2"]
    boundary = ["", ",", ",,", "x1, x2", "x1,x2", "x1, x2, x3", " x ", "  ",
                " , ", "a ,b, c ", "x,", ",y", " a , b , c ", "*args, **kwargs",
                "\\*args, \\*\\*kwargs", "x1, x2, optional", "no_comma",
                "  spaced  name  ", "\tx1,\ty2\n"]
    flags = [(m, t, d) for m in (True, False) for t in (True, False)
             for d in (True, False)]
    for s in boundary:
        check_num_commas(s); check_split_len(s); check_trim(s)
        for (m, t, d) in flags:
            check_composed(s, m, t, d)
    rng = random.Random(8056)
    alpha = list("ab x1y2,*\\_") + [" ", ",", "\t", "\n", ""]
    for _ in range(30000):
        s = "".join(rng.choice(alpha) for _ in range(rng.randint(0, 16)))
        check_num_commas(s); check_split_len(s); check_trim(s)
        check_composed(s, rng.choice((True, False)),
                       rng.choice((True, False)), rng.choice((True, False)))
    print("AX-SOUND OK: real str.count/str.split/str.strip satisfy the three "
          "axioms; composed model == gold on %d boundary + 30000 fuzz x flags"
          % len(boundary))
    sys.exit(0)

main()
'''

# Containment probe: the model passes EXACTLY one kind of value to all three
# axioms — ToSeq(name), the SAME PSeq[int] of Unicode code points, the abstraction
# of an arbitrary `_name: str` (and, for split_on_comma's runs fed to trim, the
# runs str.split(',') produces). Every such value is an arbitrary string, which is
# in-domain for str.count/str.split/str.strip (total on all str). There is no
# typed restriction (no int-vs-float gap): the axioms' Requires is `PSeq[int]`
# with no further constraint, and the caller can reach any such PSeq, all covered.
# We demonstrate domain-totality on the full reachable shape (incl. degenerate
# runs split produces) so no caller-reachable input falls outside the axiom domain.
_PROBE_CONTAINMENT = r'''
import random, sys

# The three axioms' Requires domain is: an arbitrary code-point sequence (str).
# num_commas / split_on_comma are total on str; trim (str.strip) is total on str.
# The model reaches the axioms only via:
#   num_commas(ToSeq(name))        -- name is an arbitrary consumed-field name str
#   split_on_comma(ToSeq(name))    -- same arbitrary name
#   trim(split_on_comma(name)[k])  -- a RUN that str.split(',') produced
# So the caller-reachable inputs are: (a) any name string, (b) any run of a
# str.split(',') over a name string. Both are plain strings => in every axiom's
# domain. We confirm str.count/str.split/str.strip accept every such value with
# no exception (domain containment, not just soundness).
def main():
    rng = random.Random(80560)
    alpha = list("ab x1y2,*\\_") + [" ", ",", "\t", "\n", ""]
    fixed = ["", ",", ",,", "x1, x2", " a , b , c ", "*args, **kwargs",
             "\tx1,\ty2\n", "  ", "no_comma"]
    samples = list(fixed)
    for _ in range(20000):
        samples.append("".join(rng.choice(alpha)
                               for _ in range(rng.randint(0, 16))))
    checked_names = 0
    checked_runs = 0
    for name in samples:
        # (a) name reaches num_commas + split_on_comma: must be in-domain (total)
        _ = name.count(",")          # num_commas domain
        runs = name.split(",")       # split_on_comma domain
        checked_names += 1
        # (b) each run reaches trim: must be in-domain (total) too
        for run in runs:
            _ = run.strip()          # trim domain
            checked_runs += 1
    # No exception raised on any reachable input => every caller-reachable input
    # lies inside the axiom Requires domain (str.count/split/strip total on str).
    print("AX-CONTAIN OK: %d names + %d split-runs all in-domain for "
          "count/split/strip; no caller-reachable input outside the axiom domain"
          % (checked_names, checked_runs))
    sys.exit(0)

main()
'''


AXIOM_TESTS = [
    {
        "id": "ax-soundness-stdlib",
        "axiom": "num_commas,split_on_comma,trim",
        "kind": "axiom-soundness",
        "expect": "holds",
        "apply_gold": True,
        "probe": _PROBE_SOUNDNESS,
        "rationale": "Re-runs the G-AX real-callee check in the instance image: the "
                     "REAL str.count(',')/str.split(',')/str.strip() satisfy each "
                     "axiom's Ensures (count>=0 & ''->0; split len == count+1; strip "
                     "interior/idempotent), and the composed model == the gold "
                     "_consume_fields per-field body on 19 boundary + 30000 fuzz "
                     "inputs across all (multiple,type,desc) flags, incl. the F2P "
                     "discriminator. Any disagreement => AXIOM-UNSOUND. The callees "
                     "are CPython built-ins (the exact ops the gold patch calls), so "
                     "no library import is needed.",
    },
    {
        "id": "ax-containment-caller-domain",
        "axiom": "num_commas,split_on_comma,trim",
        "kind": "axiom-containment",
        "expect": "covered",
        "apply_gold": True,
        "probe": _PROBE_CONTAINMENT,
        "rationale": "The model reaches the axioms only with (a) ToSeq(name) for an "
                     "arbitrary consumed-field name and (b) the runs str.split(',') "
                     "produces (fed to trim). Both are plain code-point sequences, and "
                     "count/split/strip are TOTAL on str — every caller-reachable "
                     "input lies inside each axiom's Requires domain (PSeq[int] with no "
                     "further constraint). There is no int-vs-float style restriction "
                     "to escape. A caller-reachable input outside the domain would be "
                     "AXIOM-TOO-WEAK-FOR-CALLER; the probe finds none.",
    },
]
