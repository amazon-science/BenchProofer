# properties.py — PBT falsification battery for pytest-dev__pytest-7571.
#
# NOT a Nagini module: a manifest the runner (swebench_nagini.pbt) parses. Each
# SPEC_TESTS case is a full model.py variant built by region-surgery (only the
# text BETWEEN a function's # impl-start / # impl-end markers is edited; the
# frozen spec — axioms / pure / pre / post regions — is never touched, which
# GUARANTEES same_spec). Each is checked by Nagini verify + markers.same_spec.
#
# ---------------------------------------------------------------------------
# Defended surface (reasoned, not mechanical):
#
# The spec models the pytest #7569 fix: a capture sink ("handler") has an
# integer acceptance threshold (sink_level). set_level must RECORD the threshold
# as it was BEFORE the change (saved_level = Old(sink_level)) and move the sink
# to `level`; teardown_restore must RETURN the sink to the recorded threshold
# when one was recorded, and leave it untouched when nothing was recorded. The
# end-to-end driver pins the cross-test guarantee: raise to `level`, teardown,
# observe back at `ambient`.
#
# Load-bearing postcondition clauses:
#   set_level:        sink_level == level
#                     saved_level is not None
#                     saved_level == Old(sink_level)            <-- the recorded value
#   teardown_restore: Implies(Old(saved_level) is not None,
#                             sink_level == Old(saved_level))    <-- the restore
#                     Implies(Old(saved_level) is None,
#                             sink_level == Old(sink_level))     <-- no-op when nothing saved
#   driver:           Result() == ambient                       <-- composed round trip
#
# Read-only inputs / frame-mutation: NONE. set_level/teardown_restore take
# full-permission Acc(self.sink_level)/Acc(self.saved_level) precisely BECAUSE
# they legitimately mutate those fields; there is no Acc(x,1/2) read-only param,
# and the driver's `level`/`ambient` are pass-by-value ints (no permission, no
# aliasing). So the #1 frame-mutation weakness class does not apply here; see
# 'assessment'. We instead lean on partial-domain attacks against the recorded
# value and the restore, plus structurally-different positive controls.
#
# Ungrounded-oracle echo: NONE. Every postcondition clause is grounded in the
# inputs (Old(sink_level), the `level` arg, the saved/None sentinel) and fully
# unfolds; there is no @Pure answer-key to echo. So no wrong-echo case exists;
# we provide honest cheapest-impl positive controls instead.
# ---------------------------------------------------------------------------
from pathlib import Path

INSTANCE = "pytest-dev__pytest-7571"
FLOAT_ENCODING = None  # meta.json float_encoding is null

_BASE = (Path(__file__).parent / "model.py").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError("drift: %r" % (old,))
    if src.count(old) != 1:
        raise AssertionError("not unique: %r" % (old,))
    return src.replace(old, new, 1)


# --- the exact impl-region bodies of the four functions (verbatim from model.py) ---
_INIT = ("        self.saved_level = None  # type: Optional[int]\n"
         "        self.sink_level = sink_level  # type: int")

_SET = ("    self.saved_level = self.sink_level\n"
        "    self.sink_level = level")

_TEARDOWN = ("    if self.saved_level is not None:\n"
             "        self.sink_level = self.saved_level")

_DRIVER = ("    controller = CaptureController(ambient)\n"
           "    set_level(controller, level)\n"
           "    teardown_restore(controller)\n"
           "    return controller.sink_level")


SPEC_TESTS = [

    # ----------------------------------------------------------------------
    # POSITIVE CONTROLS (soundness): structurally-different but CORRECT impls
    # must verify. If a faithful correct impl cannot satisfy the postcondition,
    # the spec is SPEC-TOO-STRONG. These keep the gold semantics exactly and
    # change only the executable SHAPE (local-variable reshape / branch reorder)
    # — never a loop-direction flip against a recursive helper (none exists here)
    # — so the gold proof obligations remain dischargeable.
    # ----------------------------------------------------------------------
    {
        "id": "pos-setlevel-localreshape",
        "kind": "soundness",
        "expect": "verify",
        "module": _swap(
            _BASE, _SET,
            # bind the old threshold to a typed local FIRST, then record & set:
            # exactly the gold semantics, different statement shape.
            "    prev = self.sink_level  # type: int\n"
            "    self.saved_level = prev\n"
            "    self.sink_level = level",
        ),
        "rationale": (
            "set_level with the pre-change read bound to a typed local before "
            "recording is the same record-then-set semantics in a different "
            "shape; it pins saved_level==Old(sink_level) and sink_level==level "
            "identically, so it MUST verify (else SPEC-TOO-STRONG)."),
    },
    {
        "id": "pos-teardown-branch-reorder",
        "kind": "soundness",
        "expect": "verify",
        "module": _swap(
            _BASE, _TEARDOWN,
            # branch reorder: handle the "nothing recorded" arm explicitly and
            # restore in the else. Same observable behaviour as the gold guard.
            "    if self.saved_level is None:\n"
            "        pass\n"
            "    else:\n"
            "        self.sink_level = self.saved_level",
        ),
        "rationale": (
            "teardown_restore as an if-None/else reorder restores exactly when "
            "a value was recorded and leaves the sink untouched otherwise — the "
            "gold behaviour with reordered branches; it MUST verify (else "
            "SPEC-TOO-STRONG)."),
    },

    # ----------------------------------------------------------------------
    # ADMISSIBILITY: the precondition must accept a normal, F2P-shaped input.
    # The driver composes __init__ -> set_level -> teardown_restore on the exact
    # F2P numbers (ambient=0, raised to 41). If the call sites' Requires cannot
    # be established for this legitimate lifecycle, PRECOND-TOO-STRONG.
    # ----------------------------------------------------------------------
    {
        "id": "admiss-f2p-lifecycle",
        "kind": "admissibility",
        "expect": "verify",
        "module": _swap(
            _BASE, _DRIVER,
            "    controller = CaptureController(ambient)\n"
            "    set_level(controller, level)\n"
            "    teardown_restore(controller)\n"
            "    # admissibility witness on the exact F2P shape (ambient->level->ambient)\n"
            "    Assert(controller.sink_level == ambient)\n"
            "    return controller.sink_level",
        ),
        "rationale": (
            "a positive-control driver that asserts the post-teardown sink is "
            "back at ambient demonstrates the preconditions of __init__/"
            "set_level/teardown_restore admit a normal F2P-shaped lifecycle "
            "(else PRECOND-TOO-STRONG). The Assert is dischargeable from the "
            "composed contracts, so it MUST verify."),
    },

    # ----------------------------------------------------------------------
    # UNIQUENESS / partial-domain (SPEC-TOO-WEAK probes): rivals that share the
    # frozen spec, differ only in impl, and are WRONG on a sub-domain of the
    # tested inputs. Each MUST be rejected by the load-bearing postcondition.
    # ----------------------------------------------------------------------
    {
        "id": "weak-setlevel-record-zero-skip",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(
            _BASE, _SET,
            # Record the pre-change threshold ONLY when it is non-zero; for a
            # zero ambient (the F2P case) record nothing (None). Correct on every
            # nonzero ambient, WRONG exactly on ambient==0.
            "    if self.sink_level != 0:\n"
            "        self.saved_level = self.sink_level\n"
            "    else:\n"
            "        self.saved_level = None\n"
            "    self.sink_level = level",
        ),
        "refinement": (
            "the faithful real patch — `if self.handler.level != 0: "
            "self._initial_handler_level = self.handler.level` — would NOT "
            "record the ambient 0 in F2P test1 (caplog.handler.level==0 then "
            "set_level(41)); _finalize then restores nothing and test2's "
            "`assert caplog.handler.level == 0` fails. So it does NOT resolve."),
        "rationale": (
            "rejected by set_level's postcondition `self.saved_level is not "
            "None` (and `saved_level == Old(sink_level)`): when Old(sink_level) "
            "is 0 the rival sets saved_level=None, violating the record clause."),
    },
    {
        "id": "weak-setlevel-record-new-level",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(
            _BASE, _SET,
            # Record the NEW requested level instead of the pre-change one.
            "    self.sink_level = level\n"
            "    self.saved_level = self.sink_level",
        ),
        "refinement": (
            "the faithful real patch — recording `self._initial_handler_level = "
            "level` (after `self.handler.setLevel(level)`) — saves 41 not the "
            "ambient 0; _finalize would restore the handler to 41 and test2's "
            "`assert caplog.handler.level == 0` fails. So it does NOT resolve."),
        "rationale": (
            "rejected by set_level's postcondition `self.saved_level == "
            "Old(self.sink_level)`: the rival records `level`, which equals "
            "Old(sink_level) only when level==ambient — false for the F2P 0->41."),
    },
    {
        "id": "weak-setlevel-norecord-prepatch",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(
            _BASE, _SET,
            # The pre-patch shape: move the sink but never record the restore
            # point (saved_level stays at its __init__ None).
            "    self.sink_level = level",
        ),
        "refinement": (
            "this is the pre-patch set_level (no `self._initial_handler_level = "
            "self.handler.level` line); _finalize finds None and restores "
            "nothing, leaving the handler at 41 — exactly the #7569 bug — so "
            "test2's `caplog.handler.level == 0` fails. Does NOT resolve "
            "(matches model_prepatch.py / G-DIFF)."),
        "rationale": (
            "rejected by set_level's postcondition `self.saved_level is not "
            "None`: leaving saved_level at the __init__ None violates it."),
    },
    {
        "id": "weak-teardown-noop-prepatch",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(
            _BASE, _TEARDOWN,
            # The pre-patch teardown: restore nothing (the bug). Use a vacuous
            # statement so the impl region stays a valid body.
            "    pass",
        ),
        "refinement": (
            "this is the pre-patch _finalize (no `if self._initial_handler_level "
            "is not None: self.handler.setLevel(...)`); the handler stays at the "
            "raised 41 after test1, so test2's `assert caplog.handler.level == "
            "0` fails — the #7569 bug. Does NOT resolve (model_prepatch.py)."),
        "rationale": (
            "rejected by teardown_restore's postcondition `Implies(Old("
            "saved_level) is not None, sink_level == Old(saved_level))`: a "
            "recorded value is not restored, so sink_level stays at the raised "
            "level != Old(saved_level)."),
    },
    {
        "id": "weak-teardown-restore-to-zero",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(
            _BASE, _TEARDOWN,
            # Restore to 0 whenever something was recorded (instead of to the
            # recorded value). Correct only when the ambient happened to be 0
            # (the F2P test1 case!) but WRONG for any nonzero ambient (test3 in
            # the F2P file uses ambient 0 too, but P2P / fuzz exercise nonzero).
            "    if self.saved_level is not None:\n"
            "        self.sink_level = 0",
        ),
        "refinement": (
            "the faithful real patch — `if self._initial_handler_level is not "
            "None: self.handler.setLevel(0)` — restores the handler to NOTSET(0) "
            "rather than the recorded ambient. The G-AX fuzz drives 2000 "
            "(ambient, level) pairs with nonzero ambient where teardown must "
            "land back at `ambient`, not 0; a nonzero-ambient test would observe "
            "the handler stuck at 0. Does NOT resolve in general."),
        "rationale": (
            "rejected by teardown_restore's postcondition `Implies(Old("
            "saved_level) is not None, sink_level == Old(saved_level))`: the "
            "rival pins sink_level=0, which equals Old(saved_level) only when "
            "the recorded value was 0 — false in general."),
    },
    {
        "id": "weak-teardown-always-restore",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(
            _BASE, _TEARDOWN,
            # Drop the guard: always assign sink_level = saved_level. When
            # nothing was recorded (saved_level is None) this is a type error
            # for an int field — and more importantly violates the no-op clause.
            "    Assert(self.saved_level is not None)\n"
            "    self.sink_level = self.saved_level",
        ),
        "refinement": (
            "the faithful real patch — dropping the `if self._initial_handler_"
            "level is not None` guard and unconditionally calling "
            "`self.handler.setLevel(self._initial_handler_level)` — passes None "
            "to setLevel when set_level never ran in a test, raising in "
            "_finalize (TypeError/_checkLevel) and breaking teardown for every "
            "test that does NOT call set_level (the P2P fixtures). Does NOT "
            "resolve."),
        "rationale": (
            "rejected by teardown_restore's postcondition `Implies(Old("
            "saved_level) is None, sink_level == Old(sink_level))` together with "
            "the field being a plain int: the unguarded restore cannot hold when "
            "saved_level is None (the asserted precondition `saved_level is not "
            "None` is not provable), so verification fails."),
    },
]


# ---------------------------------------------------------------------------
# AXIOM_TESTS: this bundle consumes NO @ContractOnly axiom (meta.axioms == []).
# The two deep-model references (logging.Handler.level field read/write, and the
# real LogCaptureFixture set_level/_finalize round trip) are A-REFERENCE, not
# A-consumed: the proof does not unfold any axiom Ensures; the field semantics
# are validated out-of-band by axiom_check.py (G-AX). There is no consumed-axiom
# soundness or containment obligation to probe at the PBT layer, so AXIOM_TESTS
# is empty. (G-AX already covers the A-reference: 12 boundary + 20000 fuzz
# thresholds for the integer field, and the F2P 0->41->0 case + 2000 fuzzed
# (ambient, level) pairs against the real post-patch callee in-container.)
# ---------------------------------------------------------------------------
AXIOM_TESTS = []
