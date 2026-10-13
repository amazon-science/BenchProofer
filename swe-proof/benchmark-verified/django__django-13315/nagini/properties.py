# properties.py — PBT falsification battery for django__django-13315.
#
# NOT a Nagini module. A manifest the runner (swebench_nagini.pbt) parses: each
# SPEC_TESTS entry is a full model.py variant that shares the FROZEN spec
# (axioms/pure/pre/post-conditions regions untouched) and swaps ONLY text inside
# the # impl-start/# impl-end region; the runner checks each with Nagini verify +
# markers.same_spec. The whole impl region (the loop's Invariant(...) lines
# included) is elided by spec_view, so editing inside it preserves same_spec.
#
# Defended surface (read from model.py + refinement.md + mapping.md + instance.json):
#   offered_options(matches: List[int]) -> List[int]
#     the MODELED CHANGED function (apply_limit_choices_to_to_formfield: narrow a
#     formfield's queryset by limit_choices_to across a relational join, offering
#     each matching row EXACTLY ONCE — the gold patch's Exists()-wrapping).
#     `matches` (the raw join-match stream, a row id once per satisfying join
#     path) is READ-ONLY: Requires AND Ensures Acc(list_pred(matches), 1/2).
#     Load-bearing postcondition:
#         ToSeq(Result()) == dedup(ToSeq(matches))
#     i.e. the offered options are EXACTLY the duplicate-free image of the raw
#     matching stream: membership preserved (a row is offered iff it matched at
#     least once) AND no row offered twice. Returning the raw stream verbatim
#     (the pre-patch bug) violates this whenever a row matched along >1 join path.
#
#   dedup(s) / occurs(v, s)  — @Pure helpers in the `pure` region.
#     dedup is the front-recursive duplicate-free fold; occurs is membership.
#     dedup is FULLY GROUNDED in ToSeq(matches) (spelled out as a function of the
#     input) — it is NOT an opaque answer-key oracle, so there is no WRONG echo of
#     it that verifies. The "echo" `return materialize(dedup(ToSeq(matches)))`
#     would be CORRECT (it IS the spec). See 'assessment' for the
#     ungrounded-oracle disposition; we ship an honest cheapest-impl positive
#     control instead of a wrong-echo reject.
#
# F2P: test_limit_choices_to_no_duplicates — two characters (marley, threepwood)
#      each matched along several join paths; the form field's queryset must
#      offer each EXACTLY ONCE (assertCountEqual == multiset/membership equality,
#      carried by pks). The raw stream e.g. [tw, mar, mar, tw, mar, tw] must
#      collapse to {mar, tw}.
#
# No @ContractOnly axiom is consumed (axioms region empty; meta.json axioms==[]).
# The changed collection op is modelled DEEPLY (dedup), an A-reference validated
# == the real Exists()-distinct semantics by axiom_check.py (G-AX) — see
# AXIOM_TESTS (a DB-free collection fact, runs in-container post-gold).

from pathlib import Path

INSTANCE = "django__django-13315"
FLOAT_ENCODING = None  # meta.json float_encoding == null


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


_BASE = (Path(__file__).parent / "model.py").read_text()


# ---------------------------------------------------------------------------
# Frozen impl-region anchors (verbatim from model.py). Only bytes BETWEEN
# # impl-start / # impl-end are edited, so spec_view (and same_spec) is preserved.
# ---------------------------------------------------------------------------

# The keep/drop decision (the duplicate-elimination core) — verbatim:
_DECISION = """        if occurs(v, ToSeq(matches).drop(i)):
            pass
        else:
            result = [v] + result"""

# The full loop body from the `v = ...` read to the decrement, verbatim — used
# where a variant must keep all gold invariants/asserts but reshape the body.
_BODY = """        v = matches[i - 1]
        # Keep this row only if it does not recur later in the stream, so a row
        # matched along several join paths is offered exactly once.
        if occurs(v, ToSeq(matches).drop(i)):
            pass
        else:
            result = [v] + result
        i = i - 1
    return result"""

# The final `return result` (with its trailing decrement context) for the
# admissibility append point.
_RETURN = """        i = i - 1
    return result"""


# === POSITIVE CONTROL #1 (soundness) — branch REORDER =====================
# Structurally-different but CORRECT: test the KEEP condition (not occurs(...))
# FIRST and prepend in the if-branch; the recurs-later case falls through to
# `pass`. Same executable meaning, same backward scan, every gold Invariant /
# Assert kept VERBATIM (so the loop-invariant proof and the front-recursive
# dedup matching are intact — directive-2 / directive-3 safe; no induction
# lemma, no loop-direction flip). If this cannot verify => SPEC-TOO-STRONG.
_POS_REORDER = """        if not occurs(v, ToSeq(matches).drop(i)):
            result = [v] + result
        else:
            pass"""
POS_REORDER = _swap(_BASE, _DECISION, _POS_REORDER)


# === POSITIVE CONTROL #2 (soundness) — local-variable RESHAPE =============
# Hoist the membership test into a typed boolean local, then branch on it. No
# change to the scan direction or the prepend; every gold Invariant/Assert kept
# verbatim. A correct value-equivalent reshape that must verify (else
# SPEC-TOO-STRONG). Directive-3 safe (no fold/append-forward, no lemma).
_POS_RESHAPE = """        recurs = occurs(v, ToSeq(matches).drop(i))  # type: bool
        if recurs:
            pass
        else:
            result = [v] + result"""
POS_RESHAPE = _swap(_BASE, _DECISION, _POS_RESHAPE)


# === ADMISSIBILITY ========================================================
# A positive-control CALLER appended as an impl-only helper INSIDE the impl
# region (after the gold `return result`, before # impl-end) — the proven
# django-12708 / django-13012 pattern: the frozen spec is untouched and every
# gold obligation of offered_options is preserved verbatim. The helper builds a
# concrete F2P-shaped raw matching stream (two rows each matched along several
# join paths, the regression shape [102, 101, 101, 102, 101, 102]) with FULL
# list_pred, hands HALF to offered_options (its Requires is Acc(.,1/2)), and
# asserts the result is owned + equals the duplicate-free image. If the Requires
# cannot be met for a legitimate F2P-shaped input => PRECOND-TOO-STRONG.
_ADMISS = """        i = i - 1
    return result


def _admiss_caller() -> None:
    # impl-only helper: build an F2P-shaped raw matching stream and call the
    # modeled function. A fresh list grants full list_pred, from which the
    # Acc(.,1/2) the Requires demands is split off — exactly a normal input.
    stream = [102, 101, 101, 102, 101, 102]  # type: List[int]
    got = offered_options(stream)
    # the precondition admitted a normal input; the result is owned + is the
    # exact duplicate-free image of the stream (each matching row offered once).
    Assert(Acc(list_pred(got)))
    Assert(ToSeq(got) == dedup(ToSeq(stream)))"""
ADMISS = _swap(_BASE, _RETURN, _ADMISS)


# === FRAME-MUTATION (MANDATORY: read-only Acc(matches, 1/2) input) =========
# matches is held at HALF permission (read-only: Requires AND Ensures
# Acc(list_pred(matches), 1/2)). A rival that WRITES to matches — overwriting an
# element to collapse the stream by mutation instead of building a fresh list —
# must fail for INSUFFICIENT PERMISSION (a write needs full permission; only 1/2
# is held). Every gold Invariant/Assert and the keep/drop decision are kept
# VERBATIM, and the write is inserted before the read so the rejection is
# attributable to the illegal mutation, not a value mismatch. A byte-fuzzer
# never thinks to mutate the input — this is the project's #1 weakness class.
_FRAME = """        matches[i - 1] = 0  # FRAME-MUTATION: write to a read-only (1/2) input
        v = matches[i - 1]"""
FRAME_WRITE = _swap(_BASE, "        v = matches[i - 1]", _FRAME)


# === UNIQUENESS / REJECT rivals ===========================================

# --- The PRE-PATCH bug: expose the raw matching stream VERBATIM (no dedup).
# Always prepend the row (drop the recurs-later guard), so result == the input
# stream including every duplicate. This is exactly model_prepatch.py / the
# pre-patch complex_filter(limit_choices_to) raw stream.
# refinement: this is the LITERAL pre-patch behaviour — formfield.queryset
# .complex_filter(limit_choices_to) adds the join to the SELECT and emits one row
# per satisfying join path (no DISTINCT). On the F2P, marley/threepwood each
# matched along several join paths, so the field would offer them MULTIPLE times;
# test_limit_choices_to_no_duplicates uses assertCountEqual against
# [marley, threepwood] (each exactly once) and would FAIL — it does NOT resolve
# (it IS the duplicates bug the patch fixes).
# rejection source: postcondition ToSeq(Result()) == dedup(ToSeq(matches)).
# Whenever matches has a repeat, ToSeq(matches) != dedup(ToSeq(matches)) (lengths
# differ), so returning the raw stream fails the equality.
_KEEP_ALL = """        if occurs(v, ToSeq(matches).drop(i)):
            result = [v] + result
        else:
            result = [v] + result"""
KEEP_ALL = _swap(_BASE, _DECISION, _KEEP_ALL)


# --- Inverted guard: keep a row iff it DOES recur later (drop its last
# occurrence). Membership-violating: a row appearing exactly once is DROPPED, and
# a duplicated row is kept once (at an earlier position). Set image is wrong.
# refinement: a faithful real patch that offered a row iff it had a DUPLICATE
# join path (and dropped singly-matched rows) would DROP genuinely-matching rows
# that matched along exactly one path — the F2P expects BOTH marley and
# threepwood offered (each matched), but rows matched along a single path would
# vanish; test_limit_choices_to_no_duplicates asserts both present and would FAIL
# — it does NOT resolve.
# rejection source: postcondition ToSeq(Result()) == dedup(ToSeq(matches)).
# dedup KEEPS the last occurrence of every distinct value (membership preserved);
# the inverted guard keeps the EARLIER occurrence of duplicated values and DROPS
# singletons, so set(result) != set(matches) and the sequence equality fails.
_INVERT = """        if occurs(v, ToSeq(matches).drop(i)):
            result = [v] + result
        else:
            pass"""
INVERT_GUARD = _swap(_BASE, _DECISION, _INVERT)


# --- Partial-domain: dedup correctly EXCEPT always keep the FIRST stream
# element (i == 1, the last loop step). On inputs where matches[0] recurs later,
# this re-introduces a duplicate of that row; correct on every input whose first
# element is distinct.
# refinement: a faithful real patch that special-cased the first row (offering it
# unconditionally even when a later join path already accounts for it) would
# re-introduce a duplicate of that row in the offered options on exactly the F2P
# shape (the regression stream begins with a row that recurs later); the field
# would offer that character twice and test_limit_choices_to_no_duplicates
# (assertCountEqual against each-once) would FAIL — it does NOT resolve.
# rejection source: postcondition ToSeq(Result()) == dedup(ToSeq(matches)). At
# i == 1 dedup drops matches[0] when it recurs in drop(1); the rival keeps it, so
# the result carries a duplicate dedup does not — the sequence equality fails.
_PARTIAL = """        if i > 1 and occurs(v, ToSeq(matches).drop(i)):
            pass
        else:
            result = [v] + result"""
PARTIAL_FIRST = _swap(_BASE, _DECISION, _PARTIAL)


SPEC_TESTS = [
    {
        "id": "pos-reorder",
        "kind": "soundness",
        "expect": "verify",
        "module": POS_REORDER,
        "rationale": "structurally-different CORRECT impl: the keep condition "
        "(not occurs(...)) is tested FIRST with the prepend in the if-branch and "
        "the recurs-later case falls through to `pass`. Same backward scan, same "
        "value, every gold Invariant/Assert kept verbatim (directive-2/3 safe; no "
        "loop-direction flip, no induction lemma). Must verify, else SPEC-TOO-STRONG.",
    },
    {
        "id": "pos-reshape",
        "kind": "soundness",
        "expect": "verify",
        "module": POS_RESHAPE,
        "rationale": "structurally-different CORRECT impl: hoist the membership "
        "test into a typed boolean local `recurs` and branch on it. No change to "
        "scan direction or the prepend; every gold Invariant/Assert kept verbatim. "
        "Must verify, else SPEC-TOO-STRONG.",
    },
    {
        "id": "admiss-stream",
        "kind": "admissibility",
        "expect": "verify",
        "module": ADMISS,
        "rationale": "positive-control caller builds an F2P-shaped raw matching "
        "stream [102,101,101,102,101,102] (two rows each matched along several "
        "join paths — the regression shape) with full list_pred and calls "
        "offered_options on it; a fresh list yields the Acc(.,1/2) the Requires "
        "demands, so the call site must verify — else PRECOND-TOO-STRONG. The "
        "trailing Asserts confirm the result is owned and equals the duplicate-free "
        "image (the precondition admitted a normal input).",
    },
    {
        "id": "frame-write-matches",
        "kind": "uniqueness",
        "expect": "reject",
        "module": FRAME_WRITE,
        "refinement": "a faithful real patch that mutated the source matching "
        "stream in place (rather than building a fresh narrowed queryset — Django "
        "querysets are immutable; filter() returns a NEW clone) is not even "
        "expressible against the real API, and any in-place collapse that destroyed "
        "the caller's queryset would corrupt shared state the form relies on; the "
        "F2P reads the field's queryset rows and would not see a correct distinct "
        "set — it would NOT resolve.",
        "rationale": "MANDATORY frame-mutation probe. matches is held at "
        "Acc(list_pred(matches), 1/2) (read-only, required AND ensured); the rival "
        "WRITES matches[i-1] = 0, which requires FULL permission. Rejection comes "
        "from the PERMISSION SYSTEM (insufficient permission to assign an element "
        "of matches), NOT a value mismatch — every gold Invariant/Assert and the "
        "keep/drop decision are kept verbatim and the write is placed before the "
        "read, so the rejection is attributable to the illegal mutation.",
    },
    {
        "id": "keep-all-raw-stream",
        "kind": "uniqueness",
        "expect": "reject",
        "module": KEEP_ALL,
        "refinement": "this is the LITERAL pre-patch behaviour — "
        "formfield.queryset.complex_filter(limit_choices_to) adds the join to the "
        "SELECT and emits one row per satisfying join path (no DISTINCT), i.e. the "
        "raw stream verbatim. On the F2P marley/threepwood each matched along "
        "several join paths, so the field would offer them MULTIPLE times; "
        "test_limit_choices_to_no_duplicates uses assertCountEqual against "
        "[marley, threepwood] (each once) and would FAIL — it does NOT resolve (it "
        "IS the duplicates bug the patch fixes; this is G-DIFF / model_prepatch).",
        "rationale": "rejected by the postcondition ToSeq(Result()) == "
        "dedup(ToSeq(matches)). Whenever matches carries a repeat, "
        "ToSeq(matches) != dedup(ToSeq(matches)) (lengths differ), so returning the "
        "raw stream fails the structural sequence equality. The decisive "
        "duplicate-elimination discriminator.",
    },
    {
        "id": "invert-guard-drop-singletons",
        "kind": "uniqueness",
        "expect": "reject",
        "module": INVERT_GUARD,
        "refinement": "a faithful real patch that offered a row only if it had a "
        "DUPLICATE join path (keeping recurring rows, dropping singly-matched ones) "
        "would DROP genuinely-matching rows that matched along exactly one path. "
        "The F2P expects BOTH marley and threepwood offered (each matched at least "
        "once); rows matched along a single path would vanish; "
        "test_limit_choices_to_no_duplicates asserts both present and would FAIL — "
        "it does NOT resolve.",
        "rationale": "rejected by the postcondition ToSeq(Result()) == "
        "dedup(ToSeq(matches)). dedup keeps the LAST occurrence of every distinct "
        "value (membership preserved); the inverted guard keeps the EARLIER "
        "occurrence of duplicated values and DROPS singletons, so set(result) != "
        "set(matches) and the sequence equality fails (membership violated).",
    },
    {
        "id": "partial-keep-first",
        "kind": "uniqueness",
        "expect": "reject",
        "module": PARTIAL_FIRST,
        "refinement": "a faithful real patch that special-cased the first matching "
        "row (offering it unconditionally even when a later join path already "
        "accounts for it) would re-introduce a duplicate of that row on exactly the "
        "F2P shape (the regression stream begins with a row that recurs later). The "
        "field would offer that character twice and test_limit_choices_to_no_"
        "duplicates (assertCountEqual against each-once) would FAIL — NOT resolve.",
        "rationale": "partial-domain: correct on every input whose first element is "
        "distinct, WRONG when matches[0] recurs later. Rejected by the postcondition "
        "ToSeq(Result()) == dedup(ToSeq(matches)): at i == 1 dedup drops matches[0] "
        "when it recurs in drop(1), but the rival keeps it, so the result carries a "
        "duplicate dedup does not — the structural sequence equality fails.",
    },
]


# === AXIOM LANE ===========================================================
# No @ContractOnly axiom is consumed (model.py axioms region is empty; meta.json
# axioms == []). The changed collection op (collapse the duplicate join-match
# stream to a distinct set) is modelled DEEPLY — the front-recursive fold `dedup`
# (with membership helper `occurs`) IS the duplicate elimination, an A-REFERENCE
# validated == the real Exists()-distinct semantics in-container by axiom_check.py
# (G-AX). PBT re-runs that exact host-validated oracle as a soundness + caller-
# domain containment probe (DB-free: the contrast "raw join-match stream" vs "its
# distinct image" is a pure collection fact, so no DB/settings/SQL is needed).
# The probe embeds axiom_check.py's source (read on the HOST at load time — the
# runner mounts ONLY the probe at /work, so model.py/axiom_check.py are NOT
# in-container) and runs it post-gold (apply_gold=True: the deep model describes
# the post-patch Exists()-distinct behaviour). Exit 0 iff every obligation holds.

_AX_SRC = (Path(__file__).parent / "axiom_check.py").read_text()

_PROBE_SOUNDNESS = (
    "# -*- coding: utf-8 -*-\n"
    "# G-AX soundness probe (django__django-13315): run the host-validated\n"
    "# axiom_check.py oracle in-container. It asserts the A-reference deep model\n"
    "# `dedup` EQUALS the real Exists()-distinct semantics (a base row offered iff\n"
    "# some join path matches, AT MOST ONCE — membership-preserving + duplicate-\n"
    "# free) and `occurs` EQUALS real membership, over 10 boundary + 50000 fuzz\n"
    "# match streams plus the explicit regression witness. Exit 0 iff sound.\n\n"
    + _AX_SRC
)

_PROBE_CONTAINMENT = (
    "# -*- coding: utf-8 -*-\n"
    "# G-AX caller-domain containment probe (django__django-13315). The MODEL only\n"
    "# ever feeds `dedup`/`occurs` a raw matching stream: a List[int] of row ids\n"
    "# (one occurrence per satisfying join path). Every such input is a finite\n"
    "# int sequence — exactly the domain dedup_ref/occurs_ref operate over — so\n"
    "# every caller-reachable callee-input lies inside the deep model's domain.\n"
    "# axiom_check.py exercises that whole domain (empty, singleton, all-distinct,\n"
    "# heavy-duplicate, interleaved, and 50000 random small-universe streams that\n"
    "# force collisions), demonstrating no reachable input escapes the covered\n"
    "# domain (no AXIOM-TOO-WEAK-FOR-CALLER). Exit 0 iff every reachable input is\n"
    "# contained.\n\n"
    + _AX_SRC
)


AXIOM_TESTS = [
    {
        "id": "ax-sound-dedup",
        "axiom": "dedup / occurs (A-reference deep model)",
        "kind": "axiom-soundness",
        "expect": "holds",
        "apply_gold": True,
        "probe": _PROBE_SOUNDNESS,
        "rationale": "A-reference soundness: the deep model `dedup` must equal the "
        "REAL Exists()-distinct semantics the gold patch realises (a matching base "
        "row offered AT MOST ONCE: membership-preserving + duplicate-free) and "
        "`occurs` must equal real membership, over boundary + 50000 fuzz streams + "
        "the regression witness. If the deep model disagreed with the real "
        "distinct-matching semantics => unsound (AXIOM-UNSOUND-analogue). Runs "
        "post-gold (apply_gold).",
    },
    {
        "id": "ax-contain-stream-domain",
        "axiom": "dedup / occurs (A-reference deep model)",
        "kind": "axiom-containment",
        "expect": "covered",
        "apply_gold": True,
        "probe": _PROBE_CONTAINMENT,
        "rationale": "caller-domain containment: every callee-input the model can "
        "reach is a raw matching stream (a finite List[int] of row ids, one per "
        "satisfying join path) — exactly the int-sequence domain dedup/occurs "
        "operate over, so no reachable input escapes the covered domain. "
        "axiom_check.py exercises empty/singleton/all-distinct/heavy-duplicate/"
        "interleaved + 50000 collision-forcing random streams, confirming "
        "containment (no AXIOM-TOO-WEAK-FOR-CALLER). Runs post-gold (apply_gold).",
    },
]
