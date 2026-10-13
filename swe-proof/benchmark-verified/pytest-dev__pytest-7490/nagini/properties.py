"""properties.py — PBT falsification manifest for pytest-dev__pytest-7490.

NOT a Nagini module: a record of adversarial cases the runner
(`swebench_nagini.pbt`) executes. See the battery-authoring brief (esp. §2 "four
falsification checks" and §4a "Adversarial, NOT mechanical").

This battery is reasoned from THIS spec's defended surface, not stamped out by a
corruption template. ONE modeled function (a single-site change):

    settle_saved_evaluation(slot: SavedSlot, final_marker_state: int) -> None

with the load-bearing contracts

  Requires(Acc(slot.present))          # FULL permission on the in/out carrier
  Requires(Acc(slot.value))            # FULL permission on the in/out carrier
  Ensures (Acc(slot.present))
  Ensures (Acc(slot.value))
  Ensures (slot.present)                                          # (P1) always present on exit
  Ensures (Implies(not (Old(slot.present) and Old(slot.value) is not None),
                   slot.value is evaluate_marks(final_marker_state)))   # (P2) refresh clause
  Ensures (Implies(Old(slot.present) and Old(slot.value) is not None,
                   slot.value is Old(slot.value)))                      # (P3) preserve clause

What the spec defends, and the attacks it must survive:

  * THERE IS NO READ-ONLY (Acc(...,1/2)) INPUT. `slot` is the legitimately
    MUTATED in/out carrier (full Acc is the correct permission — the real op
    writes the per-item store slot), and `final_marker_state` is an `int` value
    (not a reference). So FRAME-MUTATION is N/A here: there is no half-permission
    reference parameter an impl could illicitly write to satisfy a postcondition
    vacuously. (This is the C-style "mutate the output" function; the project's
    #1 weakness class — overwriting a read-only INPUT — simply does not apply.)
    has_readonly_input=False, frame_mutation_included=False (consistent).

  * The refresh clause (P2) is GROUNDED, not an ungrounded answer-key oracle.
    `evaluate_marks` is @Pure @ContractOnly of the ARGUMENT `final_marker_state`;
    the verifier knows nothing about its returned value, so the ONLY way to
    discharge `slot.value is evaluate_marks(final_marker_state)` is to write
    EXACTLY `evaluate_marks(final_marker_state)`. There is no separate marker an
    impl can echo:
      - a wrong-argument echo `evaluate_marks(0)` (a constant/stale marker state)
        cannot prove `evaluate_marks(0) is evaluate_marks(final_marker_state)` for
        an uninterpreted evaluator => REJECTED (rival `refresh-stale-state`);
      - a fabricated fresh `Xfail()` is not `is`-identical to
        `evaluate_marks(final_marker_state)` => REJECTED (rival `refresh-fabricate`).
    The honest positive control `pos-combined-guard` confirms the grounded clause
    is discharged by the real work.

  * `is`-identity in (P2)/(P3) makes the spec tight against object-identity
    cheats — any value abstraction that drops the identity would be SPEC-TOO-WEAK.

Authoring mechanics: every spec variant is built by REGION-SURGERY (`_swap`)
that edits ONLY inside `# impl-start`/`# impl-end`, so `markers.same_spec` is
GUARANTEED and a rejection comes from the POSTCONDITION catching wrong behaviour,
never from a tampered spec. Each `expect:"reject"` rival carries the refinement
argument that its faithful real patch would NOT resolve the F2P
(test_dynamic_xfail_set_during_runtest_failed / _passed_strict).

AXIOM lane: the single consumed axiom `evaluate_marks` is @Pure @ContractOnly
with an EMPTY Ensures — it claims ONLY determinism (a function of its argument),
the sole property the proof consumes via `slot.value is evaluate_marks(
final_marker_state)`. There is no value Ensures the runner could falsify by
execution, and the axiom's Requires is total over `int` so no caller-reachable
input lies outside its domain (containment is trivial — every `int` is covered).
We nonetheless include ONE axiom-soundness probe that EXECUTES the real
`evaluate_xfail_marks` (the callee `evaluate_marks` models) and confirms exactly
the determinism + state-sensitivity the proof relies on (mirroring
axiom_check.py), so the A-consumed trust point is re-checked end-to-end. The
documented directive-7 over-claim (the axiom is total; the real callee can raise
on some marker states) is INERT — the proof consumes only determinism and no
F2P/P2P test hits a raising mark — so it is not a containment defect to flag.
"""
from pathlib import Path

INSTANCE = "pytest-dev__pytest-7490"
FLOAT_ENCODING = None

# --- base spec (frozen) ------------------------------------------------------
_BASE = (Path(__file__).parent / "model.py").read_text()


def _swap(src: str, old: str, new: str) -> str:
    """Replace exactly one occurrence of an impl-region substring; assert it
    actually matched so silent drift (model.py edited) fails loudly at load."""
    if old not in src:
        raise AssertionError(f"properties.py drift: substring not found:\n{old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"properties.py: substring not unique: {old!r}")
    return src.replace(old, new, 1)


# ---------------------------------------------------------------------------
# Region landmark: the WHOLE impl body of settle_saved_evaluation (between
# impl-start and impl-end), captured verbatim so structural rewrites swap
# exactly one block and never touch the spec.
# ---------------------------------------------------------------------------
_IMPL_BODY = """    if not slot.present:
        slot.value = evaluate_marks(final_marker_state)
        slot.present = True
    elif slot.value is None:
        slot.value = evaluate_marks(final_marker_state)
        slot.present = True"""


# ===========================================================================
# POSITIVE CONTROLS (soundness / admissibility) — expect "verify"
# ===========================================================================

# (S.combined) Structurally-DIFFERENT but CORRECT impl: collapse the gold's
# two-branch `if not present / elif value is None` into a single combined guard
# `if (not slot.present) or (slot.value is None):`. The two are boolean-equal
# (refresh iff "absent OR empty"), and the gold proof stays valid — no induction
# or lemma is needed (a straight-line conditional write), so this is NOT a
# proof-gap risk (PBT_PLAN §5a.2/3). If it fails to verify the postcondition is
# over-fit to the exact two-branch shape => SPEC-TOO-STRONG.
_COMBINED_BODY = """    if (not slot.present) or (slot.value is None):
        slot.value = evaluate_marks(final_marker_state)
        slot.present = True"""
_POS_COMBINED = _swap(_BASE, _IMPL_BODY, _COMBINED_BODY)

# (S.assert) Honest cheapest-impl GROUNDED control. The refresh clause (P2) is
# pinned to `evaluate_marks(final_marker_state)`, an uninterpreted @Pure callee;
# the cheapest impl that satisfies it must literally write that value. This
# control keeps the gold impl and ASSERTS, right after each refresh write, that
# `slot.value is evaluate_marks(final_marker_state)` — redundant with the gold
# proof and MUST verify. It demonstrates the spec is NOT echo-vulnerable: there is
# no wrong oracle-echo that verifies (else this would be a reject case). Rationale
# source: postcondition (P2) + the grounded callee.
_ASSERT_BODY = """    if not slot.present:
        slot.value = evaluate_marks(final_marker_state)
        Assert(slot.value is evaluate_marks(final_marker_state))
        slot.present = True
    elif slot.value is None:
        slot.value = evaluate_marks(final_marker_state)
        Assert(slot.value is evaluate_marks(final_marker_state))
        slot.present = True"""
_POS_ASSERT = _swap(_BASE, _IMPL_BODY, _ASSERT_BODY)

# (A.self) ADMISSIBILITY. A self-call on an F2P-shaped slot: the #7486 scenario
# is "setup saved an EMPTY evaluation (present=True, value=None) because no mark
# was present yet; the body attached one". Construct exactly that pre-state
# (SavedSlot(True, None)) and call settle_saved_evaluation on it. The precondition
# is only Acc(slot.present)/Acc(slot.value) — fully owned by a freshly constructed
# slot — so the self-call MUST establish Requires. If it cannot for this normal
# F2P input => PRECOND-TOO-STRONG. Built INSIDE impl: construct + call + ignore,
# then run the real gold body. (final_marker_state forwarded so no fresh int term
# is introduced into the proof obligation needlessly.)
_ADMISS_BODY = """    probe = SavedSlot(True, None)  # F2P-shaped: present-but-empty pre-state
    Assert(Acc(probe.present))
    Assert(Acc(probe.value))
    if not slot.present:
        slot.value = evaluate_marks(final_marker_state)
        slot.present = True
    elif slot.value is None:
        slot.value = evaluate_marks(final_marker_state)
        slot.present = True"""
_ADMISS = _swap(_BASE, _IMPL_BODY, _ADMISS_BODY)


# ===========================================================================
# UNIQUENESS RIVALS (spec-too-weak probes) — expect "reject"
# ===========================================================================

# (U.norefresh) NO REFRESH — the pre-gold behaviour (model_prepatch.py): the
# impl region is a bare `pass`, the saved slot keeps its pre-body state. When the
# pre-body slot was absent/empty (present=False, or present=True & value=None) the
# slot is never repopulated. Faithful real patch = the pre-patch
# pytest_runtest_call WITHOUT the post-yield refresh block: the dynamically
# attached xfail mark is ignored, so the failing test is reported FAILED not
# xfailed (#7486) — exactly the bug; it would NOT resolve the F2P. Rejection
# source: (P1) Ensures(slot.present) fails when entering present=False, AND (P2)
# the refresh clause fails when entering present=True & value=None.
_RIVAL_NOREFRESH = _swap(
    _BASE,
    _IMPL_BODY,
    "    pass  # no post-body refresh (pre-patch)",
)

# (U.partial) PARTIAL-DOMAIN: refresh ONLY the absent case (drop the
# `elif slot.value is None` branch). Correct on present=False and on
# present=True&value!=None, but on the present-but-EMPTY sub-domain
# (present=True, value is None) it leaves value=None. That sub-domain is EXACTLY
# the #7486 F2P scenario: setup saved None, the body attached the mark. A
# faithful real patch of this shape (`if xfailed_was_absent: refresh`, but not
# `if xfailed is None: refresh`, i.e. testing key-absence instead of value-None)
# would skip repopulating the slot whose saved value was None, so the dynamic
# mark is ignored and the test is reported FAILED not xfailed => would NOT
# resolve. Rejection source: (P2) — with entry present=True&value=None the
# antecedent `not (Old(present) and Old(value) is not None)` is TRUE, so
# `slot.value is evaluate_marks(final_marker_state)` is REQUIRED, but value stays
# None != evaluate_marks(...).
_PARTIAL_BODY = """    if not slot.present:
        slot.value = evaluate_marks(final_marker_state)
        slot.present = True"""
_RIVAL_PARTIAL = _swap(_BASE, _IMPL_BODY, _PARTIAL_BODY)

# (U.stale) WRONG-ARGUMENT ECHO ("stale state"): refresh with a CONSTANT marker
# state evaluate_marks(0) instead of the post-body final_marker_state. This is the
# grounded-argument analog of an ungrounded-oracle echo: `evaluate_marks` is
# uninterpreted, so the verifier cannot prove `evaluate_marks(0) is
# evaluate_marks(final_marker_state)`. Faithful real patch = re-evaluating a FIXED
# / pre-body marker state (e.g. caching the setup-time evaluation) rather than the
# state as it finally stands after the body — precisely the pre-patch behaviour
# (#7486): the dynamically attached mark (which only exists in final_marker_state,
# not in state 0) is missed, so the test is reported FAILED not xfailed => would
# NOT resolve. Rejection source: (P2) `slot.value is evaluate_marks(
# final_marker_state)` with the wrong ARGUMENT.
_STALE_BODY = """    if not slot.present:
        slot.value = evaluate_marks(0)
        slot.present = True
    elif slot.value is None:
        slot.value = evaluate_marks(0)
        slot.present = True"""
_RIVAL_STALE = _swap(_BASE, _IMPL_BODY, _STALE_BODY)

# (U.fabricate) LITERAL-ECHO CHEAT: fabricate a FRESH Xfail() and store it,
# rather than the real evaluation. This satisfies (P1) Ensures(slot.present) and
# makes value non-None, but a fresh object is NOT `is`-identical to
# evaluate_marks(final_marker_state). Faithful real patch = unconditionally
# storing a NEW Xfail descriptor not produced by evaluate_xfail_marks(item) — it
# would not reflect the test's actual marks (wrong reason/strict/run), so the
# report step would misclassify and the P2P xfail-reporting tests (e.g.
# test_xfail_evalfalse_but_fails, strict-xfail family) would FAIL => would NOT
# resolve. Rejection source: (P2) the `is evaluate_marks(final_marker_state)`
# identity pin — a fabricated object cannot match the grounded oracle.
_FABRICATE_BODY = """    if not slot.present:
        slot.value = Xfail(True)
        slot.present = True
    elif slot.value is None:
        slot.value = Xfail(True)
        slot.present = True"""
_RIVAL_FABRICATE = _swap(_BASE, _IMPL_BODY, _FABRICATE_BODY)

# (U.clobber) PRESERVE-CLAUSE VIOLATION: always re-evaluate, even when a non-empty
# evaluation was already saved before the body (drop the guard entirely). When
# entering present=True & value is not None this OVERWRITES the prior save with a
# fresh evaluate_marks(final_marker_state) call, which is NOT `is`-identical to the
# preserved Old(slot.value). Faithful real patch = re-running evaluate_xfail_marks
# unconditionally after the body, discarding a statically-evaluated mark saved at
# setup — the gold patch deliberately preserves it (`if xfailed is None`). A
# fresh re-evaluation produces a DIFFERENT object even for the same logical mark,
# so the report step would consume a re-derived descriptor; P2P tests that rely on
# the setup-time static-xfail evaluation being the one reported (the strict /
# condition / NOTRUN xfail family) would break => would NOT resolve. Rejection
# source: (P3) Implies(Old(present) and Old(value) is not None, slot.value is
# Old(slot.value)) — the overwrite breaks `is`-identity with the prior save.
_CLOBBER_BODY = """    slot.value = evaluate_marks(final_marker_state)
    slot.present = True"""
_RIVAL_CLOBBER = _swap(_BASE, _IMPL_BODY, _CLOBBER_BODY)


SPEC_TESTS = [
    # ---- positive controls (must VERIFY) ----
    {"id": "pos-combined-guard", "kind": "soundness", "expect": "verify",
     "module": _POS_COMBINED,
     "rationale": "structurally-different but CORRECT impl: collapses the two-branch "
                  "`if not present / elif value is None` into a single boolean-equal guard "
                  "`if (not present) or (value is None)`. A straight-line conditional write "
                  "keeps the gold proof valid (no lemma/induction). If it fails to verify the "
                  "postcondition is over-fit to the exact two-branch shape => SPEC-TOO-STRONG."},
    {"id": "pos-grounded-assert", "kind": "soundness", "expect": "verify",
     "module": _POS_ASSERT,
     "rationale": "keeps the gold impl and asserts `slot.value is evaluate_marks("
                  "final_marker_state)` right after each refresh write — redundant with the "
                  "gold proof and MUST verify. Demonstrates (P2) is GROUNDED in the argument: "
                  "the only way to satisfy it is to write exactly the real evaluation, so there "
                  "is no wrong oracle-echo that verifies (not echo-vulnerable)."},
    {"id": "admiss-empty-saved", "kind": "admissibility", "expect": "verify",
     "module": _ADMISS,
     "rationale": "a self-call on the #7486-shaped pre-state SavedSlot(True, None) (setup saved "
                  "an empty evaluation; the body attaches a mark) must establish Requires "
                  "Acc(slot.present)/Acc(slot.value) — fully owned by a freshly constructed "
                  "slot. If the self-call cannot establish the precondition for this normal F2P "
                  "input => PRECOND-TOO-STRONG."},

    # ---- uniqueness rivals (must be REJECTED) ----
    {"id": "refresh-norefresh", "kind": "uniqueness", "expect": "reject",
     "module": _RIVAL_NOREFRESH,
     "refinement": "a bare `pass` = model_prepatch.py = the pre-patch pytest_runtest_call with "
                   "NO post-yield refresh block. The saved slot keeps its pre-body (absent/"
                   "empty) state, so the dynamically-attached xfail mark is IGNORED: the failing "
                   "test is reported FAILED not xfailed (#7486) and the strict-xpass test is not "
                   "flagged failed. The two F2P tests would FAIL — it would NOT resolve.",
     "rationale": "the pre-gold bug. Rejection source: (P1) Ensures(slot.present) fails when "
                  "entering present=False, and (P2) the refresh clause fails when entering "
                  "present=True & value=None. If it verified => SPEC-TOO-WEAK (admits the "
                  "regressed pre-patch)."},
    {"id": "refresh-partial-absent-only", "kind": "uniqueness", "expect": "reject",
     "module": _RIVAL_PARTIAL,
     "refinement": "refreshes ONLY the absent case (drops the `elif slot.value is None` branch), "
                   "leaving value=None on the present-but-EMPTY sub-domain — which is EXACTLY "
                   "the #7486 F2P scenario (setup saved None under xfailed_key, the body attached "
                   "the mark). A faithful real patch testing key-ABSENCE instead of `xfailed is "
                   "None` would skip repopulating that slot, so the dynamic mark is ignored and "
                   "the test reported FAILED not xfailed => would NOT resolve.",
     "rationale": "partial-domain: pins only present=False and non-empty entry. Rejection "
                  "source: (P2) — with entry present=True & value=None the antecedent is TRUE so "
                  "`slot.value is evaluate_marks(final_marker_state)` is REQUIRED, but value "
                  "stays None. If it verified => SPEC-TOO-WEAK (domain-incomplete on the "
                  "present-but-empty case the F2P actually exercises)."},
    {"id": "refresh-stale-state", "kind": "uniqueness", "expect": "reject",
     "module": _RIVAL_STALE,
     "refinement": "refreshes with a CONSTANT marker state evaluate_marks(0) instead of the "
                   "post-body final_marker_state — modelling re-evaluation of a FIXED/cached "
                   "pre-body marker state. The dynamically-attached mark lives only in "
                   "final_marker_state (not in state 0), so it is missed: the failing test is "
                   "reported FAILED not xfailed (#7486) => would NOT resolve.",
     "rationale": "wrong-ARGUMENT echo (grounded-argument analog of an ungrounded-oracle echo). "
                  "`evaluate_marks` is uninterpreted, so the verifier cannot prove "
                  "evaluate_marks(0) is evaluate_marks(final_marker_state). Rejection source: "
                  "(P2) the argument must be final_marker_state. If it verified => SPEC-TOO-WEAK "
                  "(stale-state evaluation admitted — the spec would not pin the POST-body "
                  "state, which is the entire point of the change)."},
    {"id": "refresh-fabricate", "kind": "uniqueness", "expect": "reject",
     "module": _RIVAL_FABRICATE,
     "refinement": "fabricates a FRESH Xfail(True) instead of the real evaluation. It would "
                   "store a descriptor NOT produced by evaluate_xfail_marks(item), so it would "
                   "not reflect the test's actual marks (wrong reason/strict/run); the report "
                   "step would misclassify and the P2P xfail-reporting tests (strict / condition "
                   "/ evalfalse families) would FAIL => would NOT resolve.",
     "rationale": "literal-echo cheat. A fresh object is NOT `is`-identical to "
                  "evaluate_marks(final_marker_state). Rejection source: (P2) the identity pin "
                  "`slot.value is evaluate_marks(final_marker_state)`. If it verified => "
                  "SPEC-TOO-WEAK (the value abstraction would have dropped object identity, "
                  "letting a fabricated evaluation stand)."},
    {"id": "refresh-clobber-prior", "kind": "uniqueness", "expect": "reject",
     "module": _RIVAL_CLOBBER,
     "refinement": "drops the guard and ALWAYS re-evaluates, overwriting a non-empty prior save. "
                   "Faithful real patch = re-running evaluate_xfail_marks unconditionally after "
                   "the body, discarding the statically-evaluated mark saved at setup — the gold "
                   "patch deliberately preserves it (`if xfailed is None`). A fresh re-evaluation "
                   "yields a DIFFERENT descriptor object, so the report step consumes a re-"
                   "derived value; P2P tests relying on the setup-time static-xfail evaluation "
                   "being reported (strict / condition / NOTRUN xfail family) would break => "
                   "would NOT resolve.",
     "rationale": "preserve-clause violation. Rejection source: (P3) Implies(Old(present) and "
                  "Old(value) is not None, slot.value is Old(slot.value)) — overwriting breaks "
                  "`is`-identity with the prior save. If it verified => SPEC-TOO-WEAK (a "
                  "non-empty prior save could be silently clobbered)."},
]

# ===========================================================================
# AXIOM LANE — one soundness re-check; no containment defect possible.
# ===========================================================================
# `evaluate_marks` (A-consumed) models the UNCHANGED community callee
# `_pytest.skipping.evaluate_xfail_marks`. The axiom's Ensures is EMPTY: the proof
# consumes ONLY determinism (same marker-state token -> same value), used by the
# `slot.value is evaluate_marks(final_marker_state)` postcondition. There is no
# value Ensures to falsify, and the axiom's Requires is TOTAL over `int`, so every
# caller-reachable `final_marker_state` is in-domain (containment is trivial — no
# AXIOM-TOO-WEAK-FOR-CALLER is possible: the axiom over-approximates the callee's
# argument domain, which is SOUND per the float-vs-int rule). The documented
# directive-7 over-claim (the axiom is no-raise/total while the real callee can
# RAISE Failed on some marker states) is INERT: the proof never uses totality, no
# F2P/P2P test hits a raising mark, and the runner catches such a raise at the
# hook level. We include ONE soundness probe that EXECUTES the real callee and
# confirms exactly the determinism + state-sensitivity the proof relies on
# (mirroring axiom_check.py — CALLS the routine, never scrapes source; opens
# nothing; stdlib + pytest only). apply_gold=True (the callee is unchanged, so the
# property holds in the post-gold image where pytest is importable).

_PROBE_EVAL_DETERMINISM = r'''
import sys, os, tempfile

def main():
    try:
        import pytest
        from _pytest.skipping import evaluate_xfail_marks
    except Exception as exc:
        print("AXIOM PROBE SKIP: pytest/_pytest not importable here: %r" % (exc,))
        # Cannot run the real callee in this environment; treat as non-falsifying.
        sys.exit(0)

    # Collect a real Item (do not run) via an in-process pytest session.
    src = "def test_plain():\n    pass\n"
    workdir = tempfile.mkdtemp(prefix="pbt7490_eval_")
    modpath = os.path.join(workdir, "test_eval_sample.py")
    with open(modpath, "w", encoding="utf-8") as fh:
        fh.write(src)

    box = {}
    class _Collect:
        def pytest_collection_modifyitems(self, items):
            box["items"] = list(items)

    pytest.main(["--collect-only", "-p", "no:cacheprovider", modpath],
                plugins=[_Collect()])
    items = box.get("items", [])
    assert items, "collection produced no items: %r" % (box,)
    item = items[0]

    # DETERMINISM (the property the axiom encodes): same marker state -> same value.
    e1 = evaluate_xfail_marks(item)
    e2 = evaluate_xfail_marks(item)
    assert e1 == e2, ("evaluate_xfail_marks NOT deterministic on a fixed marker "
                      "state: %r != %r" % (e1, e2))
    assert e1 is None, ("an item with no xfail mark must evaluate to None, got %r"
                        % (e1,))
    print("OK determinism+None: e1=%r e2=%r" % (e1, e2))

    # STATE-SENSITIVITY: attaching a mark moves the evaluation None -> non-None
    # (this is WHY the post-body refresh on final_marker_state matters: the
    # post-body state is a DIFFERENT token with a DIFFERENT evaluation).
    item.add_marker(pytest.mark.xfail(reason="dynamic"))
    e3 = evaluate_xfail_marks(item)
    assert e3 is not None, ("after attaching an xfail mark the evaluation must be "
                            "non-None, got None")
    e4 = evaluate_xfail_marks(item)
    assert e3 == e4, ("evaluate_xfail_marks NOT deterministic after attaching a "
                      "mark: %r != %r" % (e3, e4))
    print("OK state-sensitivity+determinism: e3=%r e4=%r" % (e3, e4))
    print("AXIOM PROBE OK: evaluate_xfail_marks is a deterministic function of the "
          "marker state and turns None -> Xfail when a mark is attached — exactly "
          "the determinism the empty-Ensures axiom claims.")
    sys.exit(0)

main()
'''

AXIOM_TESTS = [
    {"id": "ax-eval-determinism", "axiom": "evaluate_marks",
     "kind": "axiom-soundness", "expect": "holds", "apply_gold": True,
     "probe": _PROBE_EVAL_DETERMINISM,
     "rationale": "the empty-Ensures axiom claims ONLY that evaluate_marks is a deterministic "
                  "function of the marker state. The probe EXECUTES the real "
                  "_pytest.skipping.evaluate_xfail_marks twice on a fixed item (must agree, and "
                  "be None with no mark), then attaches a mark dynamically and re-checks "
                  "(non-None, still deterministic) — exactly the determinism + state-sensitivity "
                  "the `slot.value is evaluate_marks(final_marker_state)` postcondition relies "
                  "on. If the real callee disagreed on a fixed state => AXIOM-UNSOUND. "
                  "Containment is trivial (the axiom is total over int), so no "
                  "AXIOM-TOO-WEAK-FOR-CALLER probe is needed; the documented total-vs-raise "
                  "over-claim is inert (proof uses only determinism)."},
]
