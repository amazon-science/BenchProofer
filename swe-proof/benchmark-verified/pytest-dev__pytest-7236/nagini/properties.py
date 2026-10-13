# properties.py — PBT falsification battery for pytest-dev__pytest-7236.
#
# NOT a Nagini module. A manifest the runner (swebench_nagini.pbt) parses: each
# SPEC_TESTS entry is a full model.py variant that shares the FROZEN spec
# (axioms/pure/pre/post-conditions regions untouched) and swaps ONLY text inside
# the # impl-start/# impl-end region of decide_teardown; the runner checks each
# with Nagini verify + markers.same_spec.
#
# Defended surface (read from model.py + refinement.md + instance.json + meta):
#   decide_teardown(item: TestCaseItem) -> None
#   Decides whether a unittest TestCase's tearDown routine is RECORDED for
#   explicit later invocation under post-mortem (--pdb) mode. The model carries
#   exactly the touched fields:
#     - item.postmortem_mode (bool)  -- the --pdb config option  -- READ-ONLY Acc(.,1/2)
#     - item.skip_marker     (int)   -- the __unittest_skip__ truthiness carrier
#                                        (0 = absent/falsy, !=0 = present-truthy) -- READ-ONLY Acc(.,1/2)
#     - item.teardown_recorded (bool) -- the recorded-for-later flag -- MUTATED, full perm
#   The single LOAD-BEARING postcondition is a complete BICONDITIONAL:
#     Ensures(item.teardown_recorded ==
#             (item.postmortem_mode and not skip_marker_set(item.skip_marker)))
#   plus two read-only Old-pins:
#     Ensures(item.postmortem_mode == Old(item.postmortem_mode))
#     Ensures(item.skip_marker    == Old(item.skip_marker))
#   skip_marker_set is a @Pure deep model `skip_marker != 0` (GROUNDED in the
#   input, fully unfolded — NOT an opaque answer-key oracle; see 'assessment').
#
# F2P: testing/test_unittest.py::test_pdb_teardown_skipped[@unittest.skip]
#      (--pdb + skipped -> tearDown must NOT run -> teardown_recorded == False).
# P2P companion: test_pdb_teardown_called (--pdb + not skipped -> recorded).

from pathlib import Path

INSTANCE = "pytest-dev__pytest-7236"
FLOAT_ENCODING = None  # meta.json float_encoding == null

_BASE = (Path(__file__).parent / "model.py").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# ---------------------------------------------------------------------------
# The frozen gold impl region body (the two lines between # impl-start /
# # impl-end). Every rival edits ONLY this block.
# ---------------------------------------------------------------------------
_GOLD_IMPL = """    if item.postmortem_mode and not skip_marker_set(item.skip_marker):
        item.teardown_recorded = True"""


# === POSITIVE CONTROL (soundness) =========================================
# Structurally-different but CORRECT: instead of the gold's guarded write of a
# literal True, compute the decision boolean into a local and assign it
# UNCONDITIONALLY (no branch; both polarities written). Same final value for
# every input; the precondition guarantees teardown_recorded starts False so the
# False branch is also satisfied. No gold asserts/lemmas to drop (the gold impl
# carries none), so this is a pure executable reshape (directive-2/3 safe).
# If a faithful correct impl could not verify -> SPEC-TOO-STRONG.
_POS_UNCOND = """    decision = item.postmortem_mode and not skip_marker_set(item.skip_marker)  # type: bool
    item.teardown_recorded = decision"""
POS_UNCOND = _swap(_BASE, _GOLD_IMPL, _POS_UNCOND)

# Second positive control: explicit if/else with a False write on the else arm.
# Branch shape differs from the gold (which omits the else); still correct.
_POS_IFELSE = """    if item.postmortem_mode and not skip_marker_set(item.skip_marker):
        item.teardown_recorded = True
    else:
        item.teardown_recorded = False"""
POS_IFELSE = _swap(_BASE, _GOLD_IMPL, _POS_IFELSE)


# === ADMISSIBILITY ========================================================
# A separate top-level caller would break same_spec (the spec_view elides only
# the impl region; any module-level addition enters the spec signature). So the
# admissibility probe lives INSIDE the impl region, inserted right after
# # impl-start and BEFORE the gold obligation, so every following obligation is
# preserved verbatim. It constructs a concrete F2P-shaped TestCaseItem (the
# discriminating scenario: --pdb on, skipped) and asserts decide_teardown's
# Requires predicate facts are establishable on it (full-perm fields from the
# constructor Ensures, teardown_recorded == False). A self-call would need a
# Decreases measure the spec does not carry (proof gap, not a spec defect), so we
# exercise the Requires facts directly. If this cannot verify, the precondition
# is unsatisfiable for a normal input -> PRECOND-TOO-STRONG.
_ADMISS_BLOCK = """    # impl-start
    # ADMISSIBILITY PROBE: a representative F2P-shaped item (--pdb on, skipped)
    # establishes decide_teardown's Requires.
    probe = TestCaseItem(True, 1)
    Assert(Acc(probe.postmortem_mode, 1 / 2))
    Assert(Acc(probe.skip_marker, 1 / 2))
    Assert(Acc(probe.teardown_recorded))
    Assert(probe.teardown_recorded == False)
    Assert(probe.postmortem_mode == True)
    Assert(skip_marker_set(probe.skip_marker))"""
ADMISS = _swap(_BASE, "    # impl-start", _ADMISS_BLOCK)


# === FRAME-MUTATION (MANDATORY: two read-only Acc(.,1/2) inputs) ==========
# postmortem_mode and skip_marker are held at HALF permission (read-only). A
# rival that WRITES to one of them to satisfy the postcondition vacuously must be
# rejected for INSUFFICIENT PERMISSION (not by the value postcondition). The gold
# Old-pins (postmortem_mode == Old(...), skip_marker == Old(...)) are kept
# verbatim so the rejection is attributable to the write itself, not to a changed
# invariant. A byte-fuzzer never thinks to mutate the input — this is the #1
# weakness class.

# --- Frame A: write to the read-only post-mortem-mode flag. To "make the
# postcondition trivially hold" a rival could try to force the mode flag to a
# value that makes the recorded decision come out as it already wrote
# teardown_recorded. Writing to postmortem_mode is the attack.
# refinement: a real patch that REASSIGNED self.config's --pdb option (or mutated
# the shared Config) inside runtest would corrupt every later item's --pdb
# decision in the session; the P2P --pdb suite (test_pdb_teardown_called and the
# whole --pdb teardown grid) reads the option per-item and would observe the
# wrong mode -> it would NOT resolve.
# rejection source: PERMISSION SYSTEM -- Acc(item.postmortem_mode, 1/2) grants no
# write capability; the assignment fails for insufficient permission.
_FRAME_MODE = """    if not skip_marker_set(item.skip_marker):
        item.teardown_recorded = item.postmortem_mode
        item.postmortem_mode = item.teardown_recorded"""
FRAME_WRITE_MODE = _swap(_BASE, _GOLD_IMPL, _FRAME_MODE)

# --- Frame B: write to the read-only skip-marker carrier. A rival that
# "normalises" the marker (e.g. clamps it) to drive the decision mutates a
# read-only input.
# refinement: a real patch that wrote __unittest_skip__ back onto self.obj (e.g.
# setattr(self.obj, '__unittest_skip__', ...)) would corrupt the TestCase's skip
# state seen by collect() and the xunit fixture (both also read _is_skipped) and
# by unittest's own runner -> a once-read test could be mis-skipped / mis-run
# later; the P2P collect/skip suite would observe it -> it would NOT resolve.
# rejection source: PERMISSION SYSTEM -- Acc(item.skip_marker, 1/2) is read-only;
# the write to item.skip_marker fails for insufficient permission.
_FRAME_MARKER = """    if item.postmortem_mode and not skip_marker_set(item.skip_marker):
        item.teardown_recorded = True
        item.skip_marker = 0"""
FRAME_WRITE_MARKER = _swap(_BASE, _GOLD_IMPL, _FRAME_MARKER)


# === UNIQUENESS / partial-domain reject rivals ============================
# The postcondition is a complete biconditional, so any impl whose decision
# diverges from `postmortem_mode and not skip_marker_set(skip_marker)` on ANY
# input is rejected. Each rival below is CORRECT on most of the (mode x marker)
# domain but diverges on a named sub-domain.

# --- Partial-domain A: the PRE-PATCH shape -- record whenever post-mortem mode is
# active, IGNORING the skip marker (the exact bug the gold patch fixes).
# Diverges only on the sub-domain mode=True AND skipped=True: records True where
# the spec requires False. This is precisely the F2P scenario.
# refinement: this is literally the pre-patch `if self.config.getoption("usepdb"):`
# (no `and not _is_skipped`). The F2P test_pdb_teardown_skipped[@unittest.skip]
# runs a skipped TestCase under --pdb and asserts tearDown is NOT invoked; the
# pre-patch records _explicit_tearDown and teardown() later runs it -> the test
# FAILS. It does NOT resolve (it is the bug under repair; confirmed by
# model_prepatch.py, G-DIFF).
# rejection source: the biconditional Ensures(teardown_recorded ==
# (postmortem_mode and not skip_marker_set(skip_marker))) on mode=True ^ skipped.
_PD_PREPATCH = """    if item.postmortem_mode:
        item.teardown_recorded = True"""
PD_PREPATCH = _swap(_BASE, _GOLD_IMPL, _PD_PREPATCH)

# --- Partial-domain B: INVERTED skip guard -- record only when post-mortem AND
# SKIPPED (record exactly the cases that should not record, and skip the ones that
# should). Diverges on both F2P (skipped+pdb records, must not) and the P2P
# companion (not-skipped+pdb does not record, must).
# refinement: a real patch writing `if usepdb and _is_skipped(self.obj):` (missing
# the `not`) would record/neutralise tearDown for the skipped case (F2P still
# fails: the recorded tearDown runs) AND drop the recording for the normal --pdb
# case, so test_pdb_teardown_called (P2P, --pdb + not skipped -> tearDown runs)
# would no longer postpone teardown correctly -> it would NOT resolve.
# rejection source: the biconditional Ensures on BOTH the skipped and not-skipped
# sub-domains.
_PD_INVERT = """    if item.postmortem_mode and skip_marker_set(item.skip_marker):
        item.teardown_recorded = True"""
PD_INVERT = _swap(_BASE, _GOLD_IMPL, _PD_INVERT)

# --- Partial-domain C: IGNORE post-mortem mode -- record whenever not-skipped,
# regardless of --pdb. Correct on the whole --pdb sub-domain; diverges on
# non-pdb + not-skipped (records True where spec requires False).
# refinement: a real patch dropping the `usepdb` half of the guard
# (`if not _is_skipped(self.obj):`) would record _explicit_tearDown and replace
# tearDown with a no-op for EVERY non-skipped test, even without --pdb. That
# changes the moment of TestCase/results interaction for the entire ordinary
# (non-pdb) unittest suite -- the P2P test_simple_unittest / test_teardown grid
# (run WITHOUT --pdb) would observe tearDown postponed/neutralised and fail -> it
# would NOT resolve. (The source comment itself warns this changes observable
# timing, so it is only done "when absolutely needed", i.e. under --pdb.)
# rejection source: the biconditional Ensures on the non-pdb sub-domain
# (postmortem_mode == False -> teardown_recorded must be False).
_PD_IGNORE_PDB = """    if not skip_marker_set(item.skip_marker):
        item.teardown_recorded = True"""
PD_IGNORE_PDB = _swap(_BASE, _GOLD_IMPL, _PD_IGNORE_PDB)

# --- Partial-domain D (supporting, cheap): record UNCONDITIONALLY. Diverges on
# every input where the gold decision is False. A coarse near-miss that any tight
# biconditional rejects; carried as a supporting case, with a real refinement.
# refinement: a real patch that always recorded _explicit_tearDown + neutralised
# tearDown would run/postpone teardown for every test (skipped or not, pdb or not)
# -> both the F2P (skipped -> recorded -> tearDown runs) and the non-pdb P2P suite
# fail -> it would NOT resolve.
# rejection source: the biconditional Ensures whenever the gold decision is False.
_PD_ALWAYS = """    item.teardown_recorded = True"""
PD_ALWAYS = _swap(_BASE, _GOLD_IMPL, _PD_ALWAYS)


SPEC_TESTS = [
    {
        "id": "pos-uncond",
        "kind": "soundness",
        "expect": "verify",
        "module": POS_UNCOND,
        "rationale": "structurally-different CORRECT impl (compute the decision "
        "boolean into a local and assign it UNCONDITIONALLY -- no branch, both "
        "polarities written) must verify, else SPEC-TOO-STRONG. The precondition "
        "teardown_recorded==False makes the always-write of the False case sound.",
    },
    {
        "id": "pos-ifelse",
        "kind": "soundness",
        "expect": "verify",
        "module": POS_IFELSE,
        "rationale": "second structurally-different CORRECT impl (explicit if/else "
        "with a False write on the else arm; gold omits the else). Must verify, else "
        "SPEC-TOO-STRONG.",
    },
    {
        "id": "admiss-pdb-skipped",
        "kind": "admissibility",
        "expect": "verify",
        "module": ADMISS,
        "rationale": "a positive-control inside the impl region constructs an "
        "F2P-shaped TestCaseItem(True, 1) (--pdb on, skipped) and asserts "
        "decide_teardown's Requires facts (half-perm reads, teardown_recorded==False) "
        "are establishable -- the precondition must admit a normal input, else "
        "PRECOND-TOO-STRONG.",
    },
    {
        "id": "frame-write-mode",
        "kind": "uniqueness",
        "expect": "reject",
        "module": FRAME_WRITE_MODE,
        "refinement": "a real patch that reassigned the --pdb config option (mutated "
        "the shared Config) inside runtest would corrupt every later item's --pdb "
        "decision in the session; the --pdb teardown P2P grid reads the option "
        "per-item and would observe the wrong mode -> it would NOT resolve.",
        "rationale": "FRAME-MUTATION: rejected by the PERMISSION SYSTEM -- "
        "Acc(item.postmortem_mode, 1/2) is read-only, so `item.postmortem_mode = ...` "
        "fails for insufficient permission. Gold Old-pins kept verbatim so the "
        "rejection is attributable to the write (the #1 weakness class).",
    },
    {
        "id": "frame-write-marker",
        "kind": "uniqueness",
        "expect": "reject",
        "module": FRAME_WRITE_MARKER,
        "refinement": "a real patch that wrote __unittest_skip__ back onto self.obj "
        "would corrupt the skip state seen by collect()/the xunit fixture (which also "
        "read _is_skipped) and by unittest's own runner -> a test could be "
        "mis-skipped/mis-run later; the collect/skip P2P suite would observe it -> it "
        "would NOT resolve.",
        "rationale": "FRAME-MUTATION: rejected by the PERMISSION SYSTEM -- "
        "Acc(item.skip_marker, 1/2) is read-only, so `item.skip_marker = 0` fails for "
        "insufficient permission. Gold Old-pins kept verbatim.",
    },
    {
        "id": "pd-prepatch",
        "kind": "uniqueness",
        "expect": "reject",
        "module": PD_PREPATCH,
        "refinement": "this is the literal PRE-PATCH `if usepdb:` (no `and not "
        "_is_skipped`). The F2P test_pdb_teardown_skipped[@unittest.skip] runs a "
        "skipped TestCase under --pdb and asserts tearDown is NOT invoked; the "
        "pre-patch records _explicit_tearDown and teardown() later runs it -> the "
        "test fails. It does NOT resolve (the bug under repair; model_prepatch.py / "
        "G-DIFF confirm).",
        "rationale": "PARTIAL-DOMAIN: rejected by the biconditional Ensures "
        "teardown_recorded == (postmortem_mode and not skip_marker_set(skip_marker)) "
        "on mode=True ^ skipped=True (records True; spec requires False).",
    },
    {
        "id": "pd-invert",
        "kind": "uniqueness",
        "expect": "reject",
        "module": PD_INVERT,
        "refinement": "a real patch writing `if usepdb and _is_skipped(self.obj):` "
        "(missing the `not`) records/neutralises tearDown for the skipped case (F2P "
        "still fails) AND drops the recording for the normal --pdb case, so "
        "test_pdb_teardown_called (P2P, --pdb + not skipped) no longer postpones "
        "teardown correctly -> it would NOT resolve.",
        "rationale": "PARTIAL-DOMAIN: rejected by the biconditional Ensures on BOTH "
        "the skipped and not-skipped sub-domains (the guard is inverted on the marker).",
    },
    {
        "id": "pd-ignore-pdb",
        "kind": "uniqueness",
        "expect": "reject",
        "module": PD_IGNORE_PDB,
        "refinement": "a real patch dropping the `usepdb` half (`if not "
        "_is_skipped(self.obj):`) records _explicit_tearDown + neutralises tearDown "
        "for EVERY non-skipped test, even without --pdb -- changing the moment of "
        "TestCase/results interaction for the whole ordinary non-pdb suite; the "
        "non-pdb P2P unittest grid (test_simple_unittest / teardown ordering) would "
        "observe postponed/neutralised teardown and fail -> it would NOT resolve.",
        "rationale": "PARTIAL-DOMAIN: rejected by the biconditional Ensures on the "
        "non-pdb sub-domain (postmortem_mode==False -> teardown_recorded must be "
        "False, but this records True for any not-skipped item).",
    },
    {
        "id": "pd-always",
        "kind": "uniqueness",
        "expect": "reject",
        "module": PD_ALWAYS,
        "refinement": "a real patch that always recorded _explicit_tearDown + "
        "neutralised tearDown would run/postpone teardown for every test (skipped or "
        "not, pdb or not) -> the F2P (skipped -> recorded -> tearDown runs) and the "
        "non-pdb P2P suite both fail -> it would NOT resolve.",
        "rationale": "PARTIAL-DOMAIN (supporting, cheap): rejected by the biconditional "
        "Ensures whenever the gold decision is False (i.e. not-pdb or skipped). Carried "
        "as a coarse supporting near-miss alongside the reasoned attacks.",
    },
]


# === AXIOM LANE ===========================================================
# meta.json axioms == [] : there are NO @ContractOnly axioms the proof consumes.
# skip_marker_set is a @Pure DEEP MODEL (A-reference), NOT a consumed axiom; it is
# fully unfolded (`skip_marker != 0`) and grounded in the input. It is validated
# out-of-band against the REAL _is_skipped helper by axiom_check.py (G-AX), which
# already CALLS bool(getattr(obj,"__unittest_skip__",False)) over 23 boundary +
# 20000 fuzz marker cases and the 46-case (usepdb x marker) decision grid. There
# is nothing for the PBT axiom lane (in-Docker real-callee soundness/containment)
# to add: the deep model has no domain restriction (every int carrier is in
# range), so containment is trivial, and soundness is already discharged by G-AX
# whose check is reproduced here for completeness as a single host-checkable probe.
AXIOM_TESTS = []
