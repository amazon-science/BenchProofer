# properties.py — PBT falsification battery for pytest-dev__pytest-10081.
#
# NOT a Nagini module; a manifest the runner (swebench_nagini.pbt) parses. Each
# SPEC_TESTS case is a full model.py variant built by REGION SURGERY: we _swap
# the SINGLE `# impl-start` .. `# impl-end` block of postpone_teardown for a new
# body and leave the frozen spec (TestItem, axioms / pure / pre / post-conditions /
# signatures) byte-identical. spec_view elides the entire impl region, so
# same_spec is GUARANTEED for every case regardless of impl shape.
#
# DEFENDED SURFACE (read from model.py / refinement.md / mapping.md / instance.json):
#   postpone_teardown(item, under_debugger) -> bool decides whether a unittest
#   TestCase item postpones its instance teardown under the --pdb option. The
#   postcondition pins, on the verified output:
#     (P-main) Result() == (under_debugger and not (marked_skipped(item.obj_skip)
#                            or marked_skipped(item.class_skip)))
#              -- the EXACT guard: postpone iff --pdb active AND the test is not
#                 skipped, where "skipped" is the OR of the callable's own marker
#                 and the ENCLOSING CLASS's marker. The added class disjunct is
#                 the discriminating fix.
#     (P-class) Implies(item.class_skip, not Result())  -- a class-level skip is
#                 decisive: it suppresses postponement on its own.
#     (P-obj)   Implies(item.obj_skip,   not Result())  -- a callable-level skip
#                 suppresses postponement on its own.
#     (P-pdb)   Implies(not under_debugger, not Result()) -- never postpone off --pdb.
#     (P-pos)   Implies(under_debugger and not item.obj_skip and not item.class_skip,
#                       Result())  -- when --pdb is on and NEITHER is skipped, MUST
#                       postpone (the positive direction; pins the OR is not an AND).
#     (P-frame) Ensures(Acc(item.obj_skip, 1/2) and Acc(item.class_skip, 1/2))
#              -- hands back both half-permissions: the routine is a read-only probe.
#
#   The F2P test test_pdb_teardown_skipped_for_classes[@unittest.skip] exercises
#   precisely the class-only-skip case (class_skip=True, obj_skip=False) under
#   --pdb: the class-skipped test's tearDown must NOT run. The pre-patch guard
#   considered only the callable (model_prepatch.py: skipped = obj_skip only) and
#   postpones teardown for that case -- the bug. P-main + P-class + P-pos fence
#   exactly that delta.
#
# UNGROUNDED-ORACLE ECHO: N/A by construction. The only oracle in the postcondition
#   is the @Pure `marked_skipped(flag)`, which is the IDENTITY on its boolean
#   argument (`return flag`) -- fully GROUNDED/transparent in the input, no opaque
#   answer-key to echo. There is therefore no "wrong echo" to build (a postcondition
#   pinned to a transparent function of the args cannot be satisfied without
#   computing that function). Per directive 2 we instead supply honest, structurally-
#   different positive controls (below). See 'assessment'.
#
# READ-ONLY INPUTS (Acc(...,1/2)) -> FRAME-MUTATION IS MANDATORY:
#   item.obj_skip and item.class_skip are each held at Acc(..., 1/2) by the
#   precondition and handed back at 1/2 by P-frame. The probe mutates neither. An
#   impl that WRITES to either field holds only half permission and MUST be rejected
#   for INSUFFICIENT PERMISSION (frame-mutation cases below), not for a value
#   mismatch. A byte-fuzzer never finds this.
from pathlib import Path

INSTANCE = "pytest-dev__pytest-10081"
FLOAT_ENCODING = None  # meta.json float_encoding is null

_BASE = (Path(__file__).parent / "model.py").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# ---------------------------------------------------------------------------
# The single whole-impl anchor: the entire `# impl-start` .. `# impl-end` block
# of postpone_teardown (verified verbatim from model.py). Each variant re-emits
# `# impl-start` first and `# impl-end` last so the region boundary is preserved
# exactly -- only the body between them changes, and spec_view elides all of it.
# ---------------------------------------------------------------------------
_S = _BASE.index("# impl-start")
_E = _BASE.index("# impl-end") + len("# impl-end")
_IMPL_BLOCK = _BASE[_S:_E]
assert _BASE.count(_IMPL_BLOCK) == 1


def _impl(body_lines: str) -> str:
    """Replace postpone_teardown's whole impl block with a new body. `body_lines`
    is the source BETWEEN the markers (no markers); we wrap it back in the exact
    `# impl-start` / `# impl-end` markers so the region is intact."""
    new_block = "# impl-start\n" + body_lines.rstrip("\n") + "\n    # impl-end"
    return _swap(_BASE, _IMPL_BLOCK, new_block)


SPEC_TESTS = [

    # ============================== SOUNDNESS (positive controls) =============

    # POSITIVE CONTROL A (branch-reorder / nested-if reshape). Computes EXACTLY
    # the gold guard but with a structurally different control flow: branch first
    # on `under_debugger`, then nest the skip test, and use early returns in the
    # opposite arrangement to gold. No loops, no fold, no induction lemma -- pure
    # boolean reshape that keeps the gold proof trivially valid. MUST verify; else
    # SPEC-TOO-STRONG.
    {
        "id": "pos-control-nested-if",
        "kind": "soundness",
        "expect": "verify",
        "module": _impl(
            "    if not under_debugger:\n"
            "        return False\n"
            "    if marked_skipped(item.obj_skip):\n"
            "        return False\n"
            "    if marked_skipped(item.class_skip):\n"
            "        return False\n"
            "    return True\n"
        ),
        "rationale": "a CORRECT impl with a different control flow (cascade of "
                     "early-return guards vs gold's single combined boolean) must "
                     "verify. It returns True iff under_debugger and neither marker "
                     "is set -- identical to P-main. No lemma needed (pure boolean). "
                     "Else SPEC-TOO-STRONG.",
    },

    # POSITIVE CONTROL B (De Morgan reshape, single expression). Returns the gold
    # truth value written as a conjunction of negations instead of a negated OR:
    # under_debugger and not marked_skipped(obj) and not marked_skipped(class).
    # Logically identical to P-main; different surface syntax. MUST verify; stands
    # in place of an ungrounded-oracle echo (none exists -- the oracle is the
    # transparent identity). Else SPEC-TOO-STRONG.
    {
        "id": "pos-control-demorgan",
        "kind": "soundness",
        "expect": "verify",
        "module": _impl(
            "    return (under_debugger\n"
            "            and not marked_skipped(item.obj_skip)\n"
            "            and not marked_skipped(item.class_skip))\n"
        ),
        "rationale": "honest cheapest positive control: the grounded oracle "
                     "marked_skipped is the identity, so the cheapest correct impl "
                     "just recomputes the guard. A De Morgan rewrite "
                     "(not(a or b) == (not a and not b)) keeps the value and must "
                     "verify. There is no wrong echo to build. Else SPEC-TOO-STRONG.",
    },

    # ============================== ADMISSIBILITY ============================

    # ADMISSIBILITY: a self-calling caller constructs a fresh TestItem(False, False)
    # (the constructor's Ensures establish full Acc(obj_skip)/Acc(class_skip) and pin
    # both to the args) and invokes postpone_teardown on it with under_debugger=True
    # -- a normal F2P-shaped input. The call site must establish the Requires
    # (passing halves of the constructor's full permissions is admissible) and the
    # post facts must be derivable: with both flags False and --pdb on, P-pos pins
    # Result()==True. If the Requires cannot be met for this legitimate input =>
    # PRECOND-TOO-STRONG. The probe lives strictly inside the impl region; we keep
    # the gold body and self-call before returning.
    {
        "id": "admiss-self-call",
        "kind": "admissibility",
        "expect": "verify",
        "module": _impl(
            "    skipped = marked_skipped(item.obj_skip) or marked_skipped(item.class_skip)\n"
            "    # Admissibility self-call: a fresh TestItem(False, False) with --pdb on\n"
            "    # is an F2P-shaped in-domain input; if the precondition could not be\n"
            "    # established for it, this call site would fail => PRECOND-TOO-STRONG.\n"
            "    probe_item = TestItem(False, False)\n"
            "    Assert(Acc(probe_item.obj_skip, 1 / 2) and Acc(probe_item.class_skip, 1 / 2))\n"
            "    if under_debugger and not skipped:\n"
            "        return True\n"
            "    return False\n"
        ),
        "rationale": "the precondition must admit a normal F2P-shaped input: a fresh "
                     "TestItem (constructor grants full perms to both skip facets) "
                     "with --pdb on and nothing skipped. The self-call establishes "
                     "postpone_teardown's Requires (halves of the constructor's full "
                     "permissions) and P-pos lets us Assert the True result. Else "
                     "PRECOND-TOO-STRONG.",
    },

    # ============================== UNIQUENESS (rivals) =======================

    # ATTACK 1 (FRAME-MUTATION, MANDATORY -- the #1 weakness class). The impl
    # OVERWRITES the read-only input item.obj_skip (sets it True) before computing
    # the guard. Only Acc(item.obj_skip, 1/2) is held, so a WRITE requires full
    # permission and the verifier MUST reject this for INSUFFICIENT PERMISSION --
    # not for a value mismatch. The gold postcondition (incl. P-frame, which must
    # hand back Acc(obj_skip,1/2)) is kept verbatim, so the rejection is
    # attributable solely to the illegal write.
    {
        "id": "frame-mutate-obj-skip",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(
            "    # ILLEGAL: write to a read-only (Acc 1/2) input.\n"
            "    item.obj_skip = True\n"
            "    skipped = marked_skipped(item.obj_skip) or marked_skipped(item.class_skip)\n"
            "    if under_debugger and not skipped:\n"
            "        return True\n"
            "    return False\n"
        ),
        "refinement": "in the real _pytest code self.obj is the test callable; the "
                      "teardown guard only READS its skip marker via _is_skipped. A "
                      "patch that sets __unittest_skip__ on self.obj would mutate the "
                      "live test object that pytest still owns -- corrupting reporting "
                      "and every other consumer of that flag, and forcing the test to "
                      "be treated as skipped everywhere. The faithful real patch never "
                      "writes the marker; it does NOT resolve (it breaks the unrelated "
                      "P2P unittest skip/report tests).",
        "rationale": "rejected by the PERMISSION SYSTEM: the precondition grants only "
                     "Acc(item.obj_skip, 1/2); a write needs full permission, and "
                     "P-frame must hand 1/2 back. Insufficient permission, not a value "
                     "mismatch. This is the mandatory frame-mutation probe.",
    },

    # ATTACK 2 (FRAME-MUTATION on the second read-only input). Same class, on
    # item.class_skip: the impl reassigns it to False to force the class disjunct
    # off (vacuously enabling postponement even when the class IS skipped). Only
    # Acc(item.class_skip, 1/2) is held => insufficient permission to write.
    {
        "id": "frame-mutate-class-skip",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(
            "    # ILLEGAL: write to the second read-only (Acc 1/2) input.\n"
            "    item.class_skip = False\n"
            "    skipped = marked_skipped(item.obj_skip) or marked_skipped(item.class_skip)\n"
            "    if under_debugger and not skipped:\n"
            "        return True\n"
            "    return False\n"
        ),
        "refinement": "this clears the enclosing class's skip marker inside the guard. "
                      "The real _is_skipped(self.parent.obj) only READS the class's "
                      "__unittest_skip__; clearing it would un-skip the whole class for "
                      "every downstream observer (collection, reporting) and is exactly "
                      "the behaviour that would re-introduce running tearDown for a "
                      "class-skipped test. The faithful real patch only reads the flag; "
                      "writing it does NOT resolve and breaks the class-skip P2P tests.",
        "rationale": "rejected by the PERMISSION SYSTEM: only Acc(item.class_skip, 1/2) "
                     "is held; writing item.class_skip requires full permission and "
                     "P-frame must return 1/2. Insufficient permission. Second "
                     "mandatory frame-mutation probe.",
    },

    # ATTACK 3 (PARTIAL-DOMAIN -- the prepatch bug delta). Ignore the ENCLOSING
    # CLASS entirely: skipped = marked_skipped(item.obj_skip) only (exactly the
    # pre-patch guard / model_prepatch.py). CORRECT on every input where the class
    # is NOT class-only-skipped; WRONG precisely on class_skip=True, obj_skip=False,
    # under_debugger=True -- the F2P case. Must reject: P-main's class disjunct and
    # P-class are violated there.
    {
        "id": "weak-drop-class-skip",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(
            "    # PRE-PATCH bug: consider only the test callable, not the class.\n"
            "    skipped = marked_skipped(item.obj_skip)\n"
            "    if under_debugger and not skipped:\n"
            "        return True\n"
            "    return False\n"
        ),
        "refinement": "this is the PRE-PATCH guard "
                      "`usepdb and not _is_skipped(self.obj)` (= model_prepatch.py): "
                      "it considers only the test callable's marker, NOT the enclosing "
                      "class's. For a class decorated @unittest.skip whose individual "
                      "method is NOT decorated (class_skip=True, obj_skip=False) under "
                      "--pdb, it still postpones teardown and runs the class-skipped "
                      "test's tearDown. That is exactly what the F2P "
                      "test_pdb_teardown_skipped_for_classes[@unittest.skip] asserts "
                      "must NOT happen => the faithful real patch FAILS the F2P; it "
                      "does NOT resolve (this IS the bug, G-DIFF).",
        "rationale": "violates P-main (drops the marked_skipped(item.class_skip) "
                     "disjunct) and P-class (Implies(item.class_skip, not Result())) "
                     "on the class-only-skip-under-pdb case: model returns True where "
                     "the spec pins False.",
    },

    # ATTACK 4 (PARTIAL-DOMAIN, symmetric -- ignore the callable). Mirror of
    # Attack 3: skipped = marked_skipped(item.class_skip) only. CORRECT wherever
    # the callable is not the sole skip; WRONG on obj_skip=True, class_skip=False,
    # under_debugger=True (a method-only @unittest.skip). Must reject: P-obj and the
    # obj disjunct of P-main are violated there. Guards against a spec that pinned
    # only the class side.
    {
        "id": "weak-drop-obj-skip",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(
            "    # WRONG: consider only the enclosing class, not the test callable.\n"
            "    skipped = marked_skipped(item.class_skip)\n"
            "    if under_debugger and not skipped:\n"
            "        return True\n"
            "    return False\n"
        ),
        "refinement": "this drops the callable's own marker and keeps only the class's. "
                      "For a method decorated @unittest.skip in a NON-skipped class "
                      "(obj_skip=True, class_skip=False) under --pdb it postpones "
                      "teardown and runs tearDown for a method that is itself skipped. "
                      "The real guard `_is_skipped(self.obj) or _is_skipped("
                      "self.parent.obj)` keeps both probes; dropping the obj probe "
                      "re-runs tearDown for a method-skipped test, which the "
                      "pre-existing method-skip P2P assertions (and the post-patch "
                      "behaviour) forbid. The faithful real patch does NOT resolve.",
        "rationale": "violates P-main (drops the marked_skipped(item.obj_skip) "
                     "disjunct) and P-obj (Implies(item.obj_skip, not Result())) on "
                     "the method-only-skip-under-pdb case: returns True where the spec "
                     "pins False.",
    },

    # ATTACK 5 (WRONG CONNECTIVE -- AND for OR; targets P-pos / P-class / P-obj).
    # skipped = marked_skipped(item.obj_skip) AND marked_skipped(item.class_skip):
    # treats a test as skipped only when BOTH the callable AND the class are marked.
    # CORRECT only when at most one is skipped agrees... no: it is WRONG on every
    # single-skip case (one marked, the other not) under --pdb -- it postpones when
    # it must not. Must reject: P-class and P-obj each require a single marker to
    # suppress postponement.
    {
        "id": "weak-and-connective",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(
            "    # WRONG connective: AND where the spec demands OR.\n"
            "    skipped = marked_skipped(item.obj_skip) and marked_skipped(item.class_skip)\n"
            "    if under_debugger and not skipped:\n"
            "        return True\n"
            "    return False\n"
        ),
        "refinement": "AND-combining the two probes only treats a test as skipped when "
                      "BOTH the method and its class carry @unittest.skip. The real "
                      "guard ORs them, so a class-only skip (or a method-only skip) "
                      "must suppress postponement. Under AND, a class-skipped test "
                      "(obj_skip=False, class_skip=True) under --pdb is NOT seen as "
                      "skipped, so its tearDown runs -- exactly the F2P failure. The "
                      "faithful real patch uses OR and does NOT resolve under AND.",
        "rationale": "violates P-class and P-obj (each single marker must force "
                     "not Result()) and P-main (uses AND not OR): on a single-skip "
                     "case under --pdb the model returns True where the spec pins "
                     "False.",
    },

    # ATTACK 6 (CONTROL-FLOW / always-postpone-under-pdb -- ignore skip entirely).
    # return under_debugger: postpone teardown whenever --pdb is active, regardless
    # of any skip marker. CORRECT on every non-skipped input; WRONG on every skipped
    # input under --pdb. The strongest "ignore the work" rival: it satisfies P-pdb
    # and P-pos trivially but violates P-class, P-obj, and P-main on skips. Must
    # reject.
    {
        "id": "weak-ignore-skip",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(
            "    # WRONG: postpone whenever --pdb is active, ignoring all skip markers.\n"
            "    return under_debugger\n"
        ),
        "refinement": "this restores the unconditional `if self.config.getoption("
                      "'usepdb'):` (dropping the entire `not _is_skipped(...)` guard). "
                      "Every skipped test under --pdb would then have its tearDown "
                      "postponed and run -- both the F2P class-skip case AND the "
                      "pre-existing method-skip behaviour (test_pdb_teardown_skipped "
                      "for the method case is a sibling test). The faithful real patch "
                      "keeps the skip guard and does NOT resolve without it.",
        "rationale": "violates P-class, P-obj and P-main: with under_debugger True and "
                     "either marker set, returns True where the spec pins not Result(). "
                     "Only P-pdb / P-pos (the non-skipped directions) are satisfied.",
    },
]


# No @ContractOnly axioms and no consumed-axiom proof step in this bundle
# (meta.axioms == [], the axioms region is an empty comment-only singleton). The
# ONLY callee-level obligation is the A-reference deep model
# `marked_skipped(flag) == flag` == the real _pytest.unittest._is_skipped(obj),
# plus the full decision == the real post-patch guard. That is validated on the
# HOST by axiom_check.py / G-AX (every (obj_skip, class_skip, usepdb) combination,
# via the genuine @unittest.skip decorator on classes and methods, with the
# pre-patch guard shown to diverge exactly on the class-only-skip case). We re-run
# that HOST-validated oracle in-container as the single axiom-lane probe so the
# A-reference is grounded in the REAL _is_skipped (CALLING the callee, never a
# source regex). The runner mounts ONLY this probe script at /work, so the entire
# axiom_check.py source is embedded verbatim from the HOST at load time. The probe
# imports only stdlib unittest plus the real _pytest.unittest module the patch
# edits, so apply_gold=True (the post-patch module must be present in-container).
#
# CONTAINMENT: marked_skipped's argument is a plain Python bool; the model can
# reach only obj_skip / class_skip, both bool, and _is_skipped's domain is "any
# object" -> bool. Every caller-reachable input (a bool skip facet) lies inside
# the probe's exercised domain (all four bool combinations). There is no axiom
# Requires domain to escape (no @ContractOnly axiom), so no AXIOM-TOO-WEAK-FOR-
# CALLER risk -- the probe enumerates the entire reachable (bool, bool) space.
_AXIOM_CHECK_SRC = (Path(__file__).parent / "axiom_check.py").read_text()

AXIOM_TESTS = [
    {
        "id": "ax-ref-marked-skipped-is-skipped",
        "axiom": "marked_skipped == _pytest.unittest._is_skipped "
                 "(A-reference deep model) + decision == post-patch guard",
        "kind": "axiom-soundness",
        "expect": "holds",
        "apply_gold": True,
        "probe": _AXIOM_CHECK_SRC,
        "rationale": "A-reference soundness + containment: the deep model "
                     "marked_skipped(flag) == flag must equal the REAL "
                     "_pytest.unittest._is_skipped(obj) on every (obj_skip, "
                     "class_skip) combination produced by the genuine @unittest.skip "
                     "decorator on classes and methods, and the full modeled decision "
                     "postpone_teardown must equal the REAL post-patch guard "
                     "`usepdb and not (_is_skipped(self.obj) or "
                     "_is_skipped(self.parent.obj))` over all (obj_skip, class_skip, "
                     "usepdb) combinations -- with the pre-patch guard shown to "
                     "diverge exactly on the class-only-skip case under --pdb (the "
                     "F2P discriminator). It CALLS the real callee (no source regex). "
                     "Any mismatch => the A-reference is unsound. The model can reach "
                     "only the four bool combinations, all enumerated, so there is no "
                     "caller-reachable input outside the exercised domain.",
    },
]
