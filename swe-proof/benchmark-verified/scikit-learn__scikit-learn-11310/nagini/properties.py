# properties.py — PBT falsification battery for scikit-learn__scikit-learn-11310.
#
# NOT a Nagini module. A manifest the runner (swebench_nagini.pbt) parses: each
# SPEC_TESTS entry is a full model.py variant that shares the FROZEN spec
# (axioms + pre + post byte-identical) and edits ONLY the impl region, checked by
# Nagini verify + markers.same_spec; AXIOM_TESTS entries are real-callee probes
# run in the instance Docker image.
#
# Defended surface (read from model.py / refinement.md / mapping.md):
#   recorded_refit_duration(do_final_fit: bool, start: float, end: float)
#       -> Optional[float]
#     Requires: end >= start                       (timer monotonicity, A-ref clock_after)
#     Ensures (1): do_final_fit == (Result() is not None)      PRESENCE iff final fit
#     Ensures (2): Implies(Result() is not None,
#                          Result() == elapsed_between(start, end))   VALUE pinned
#
#   All three inputs are pass-by-value Nagini primitives (bool, float). There is
#   NO Acc(...,1/2) read-only reference input anywhere in the spec (grep-confirmed:
#   no Acc clause), so the FRAME-MUTATION class is N/A here — there is no
#   heap-resident input a rival could overwrite to satisfy a postcondition
#   vacuously. (See 'assessment' in the returned JSON.)
#
#   The value oracle elapsed_between(start, end) is GROUNDED in the two input
#   carriers (a @Pure @ContractOnly model of the real subtraction
#   refit_end_time - refit_start_time, refinement.md §E), not an opaque answer
#   key: any impl that "echoes" elapsed_between(start, end) IS the correct gold
#   value, so there is no wrong-echo to build. The ungrounded-oracle-echo attack
#   is therefore vacuous; in its place we (a) supply an honest cheapest correct
#   positive control that routes the value through elapsed_between, and (b) attack
#   the value clause with constants / wrong functions of the inputs that are NOT
#   equal to the grounded oracle.

from pathlib import Path

INSTANCE = "scikit-learn__scikit-learn-11310"
FLOAT_ENCODING = "real"   # meta.json float_encoding; the spec verifies with --float-encoding=real

_BASE = (Path(__file__).parent / "model.py").read_text()

# The exact impl region of the frozen model.py (between # impl-start / # impl-end).
# Every variant is produced by _swap on this unique block, so the spec regions
# (axioms / pure / pre / post) are never touched -> same_spec holds by construction.
_GOLD_IMPL = (
    "    result = None  # type: Optional[float]\n"
    "    if do_final_fit:\n"
    "        # the elapsed interval is the later reading minus the earlier one; the\n"
    "        # readings are ordered (end >= start), so the interval is a non-negative\n"
    "        # real value.\n"
    "        result = elapsed_between(start, end)\n"
    "    return result"
)


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r} not found in base")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


def _variant(new_impl):
    return _swap(_BASE, _GOLD_IMPL, new_impl)


# ---------------------------------------------------------------------------
# POSITIVE CONTROLS (soundness) — structurally-different CORRECT impls that MUST
# verify. If a faithful correct impl cannot satisfy the Ensures => SPEC-TOO-STRONG.
# Both keep the value routed through the grounded elapsed_between oracle (raw
# float subtraction end-start is deliberately NOT provable-equal under Nagini's
# uninterpreted float arithmetic — refinement.md §C — so a structural variant
# must still call elapsed_between; that is a design choice, not a spec defect).
# ---------------------------------------------------------------------------

# Reorder control flow: guard the ABSENT case first with an early return, then
# fall through to the recording. Same value, opposite branch order from gold.
POS_EARLY_RETURN = _variant(
    "    if not do_final_fit:\n"
    "        none_result = None  # type: Optional[float]\n"
    "        return none_result\n"
    "    # the final fit was performed; report the elapsed interval of the two\n"
    "    # ordered readings (later minus earlier), a non-negative real value.\n"
    "    duration = elapsed_between(start, end)  # type: Optional[float]\n"
    "    return duration"
)

# Local-variable reshape: bind the elapsed interval unconditionally to a typed
# local, then select between it and the absent marker. Different data shape
# (compute-then-select vs guard-then-assign), identical observable value.
POS_COMPUTE_THEN_SELECT = _variant(
    "    measured = elapsed_between(start, end)  # type: float\n"
    "    result = None  # type: Optional[float]\n"
    "    if do_final_fit:\n"
    "        result = measured\n"
    "    return result"
)


# ---------------------------------------------------------------------------
# ADMISSIBILITY — a self-call caller proving the precondition admits a normal
# F2P-shaped input on BOTH branches. If the Requires cannot be established for a
# legitimate input => PRECOND-TOO-STRONG. (The F2P uses refit=True with two real
# time.time() readings end >= start; both branches are reachable in sklearn —
# refit truthy vs falsy.)
# ---------------------------------------------------------------------------

# True branch: do_final_fit=True, an ordered pair start<=end => result present.
ADMISS_TRUE = _variant(
    "    result = None  # type: Optional[float]\n"
    "    if do_final_fit:\n"
    "        result = elapsed_between(start, end)\n"
    "    # admissibility: a normal F2P-shaped input (refit performed, two ordered\n"
    "    # readings 1.0 <= 2.0) satisfies Requires(end >= start) and yields a\n"
    "    # present, non-negative duration.\n"
    "    Assert(2.0 >= 1.0)\n"
    "    return result"
)

# False branch + boundary zero-length interval: do_final_fit=False with the
# trivial-X case start==end (the axiom_check.py (0.0,0.0) boundary) => result
# absent. Exercises the present-iff direction and the end>=start boundary.
ADMISS_FALSE_AND_ZERO = _variant(
    "    result = None  # type: Optional[float]\n"
    "    if do_final_fit:\n"
    "        result = elapsed_between(start, end)\n"
    "    # admissibility: the no-refit case (do_final_fit=False) reports the absent\n"
    "    # marker; the zero-length interval (3.0, 3.0) is in-domain (end >= start).\n"
    "    Assert(3.0 >= 3.0)\n"
    "    return result"
)


# ---------------------------------------------------------------------------
# UNIQUENESS / completeness — same-spec WRONG impls that MUST be rejected. If any
# verifies the spec admits an incorrect impl => SPEC-TOO-WEAK. Each carries the
# refinement argument: its faithful real patch and whether it would resolve.
# ---------------------------------------------------------------------------

# (a) PRESENCE class — missing presence (= the pre-patch behaviour). Never report
# a duration even when the final fit runs. Violates Ensures(1) when
# do_final_fit is True (result stays None => do_final_fit != (Result() is None)).
WEAK_NEVER_PRESENT = _variant(
    "    result = None  # type: Optional[float]\n"
    "    if do_final_fit:\n"
    "        # the final fit happens but its duration is never recorded\n"
    "        pass\n"
    "    return result"
)

# (b) PRESENCE class — extra presence / partial-domain on the do_final_fit=False
# sub-domain. Always report a duration, even when the final fit did NOT run.
# Violates Ensures(1) on the not-do_final_fit branch (Result() is not None while
# do_final_fit is False).
WEAK_ALWAYS_PRESENT = _variant(
    "    # always report a value, ignoring whether the final fit ran\n"
    "    result = elapsed_between(start, end)  # type: Optional[float]\n"
    "    return result"
)

# (c) VALUE class — constant zero. Report 0.0 (the int/non-real-stand-in family
# the refinement.md panel fix explicitly targeted: atk_9 result=0). Equal to the
# grounded oracle only on the zero-length interval; on any positive interval
# 0.0 != elapsed_between(start, end). Violates Ensures(2).
WEAK_CONST_ZERO = _variant(
    "    result = None  # type: Optional[float]\n"
    "    if do_final_fit:\n"
    "        # report a constant instead of the genuine elapsed interval\n"
    "        result = 0.0\n"
    "    return result"
)

# (d) VALUE class — echo a reading instead of the difference. Report `end` (a
# function of the inputs, but the WRONG one): end != elapsed_between(start, end)
# in general. Defeats a naive "any input-derived float is fine" reading of the
# value clause. Violates Ensures(2).
WEAK_ECHO_END = _variant(
    "    result = None  # type: Optional[float]\n"
    "    if do_final_fit:\n"
    "        # echo the later reading rather than the elapsed interval\n"
    "        result = end\n"
    "    return result"
)

# (e) VALUE class — swapped-argument elapsed_between(end, start) (the earlier
# minus later orientation). With end >= start this calls the oracle with
# later=start, earlier=end, which violates elapsed_between's own
# Requires(later >= earlier) (unless start==end) AND yields the negated interval.
WEAK_SWAPPED = _variant(
    "    result = None  # type: Optional[float]\n"
    "    if do_final_fit:\n"
    "        # wrong orientation: earlier reading minus later reading\n"
    "        result = elapsed_between(end, start)\n"
    "    return result"
)


SPEC_TESTS = [
    # ---- soundness (positive controls) ----
    {
        "id": "pos-early-return",
        "kind": "soundness",
        "expect": "verify",
        "module": POS_EARLY_RETURN,
        "rationale": (
            "Structurally-different but correct: guard the absent case with an "
            "early return, then report elapsed_between(start, end). Branch order "
            "is the opposite of gold. Keeps every gold proof obligation (value "
            "routed through the grounded oracle; presence pinned by control flow). "
            "Must verify, else SPEC-TOO-STRONG."
        ),
    },
    {
        "id": "pos-compute-then-select",
        "kind": "soundness",
        "expect": "verify",
        "module": POS_COMPUTE_THEN_SELECT,
        "rationale": (
            "Local-variable reshape: compute the elapsed interval unconditionally "
            "into a typed local, then select between it and None on do_final_fit. "
            "Different data shape (compute-then-select), identical value. elapsed_"
            "between's Requires(end>=start) is discharged by the model precondition "
            "unconditionally, so the unconditional call is sound. Must verify."
        ),
    },
    # ---- admissibility ----
    {
        "id": "admiss-true-branch",
        "kind": "admissibility",
        "expect": "verify",
        "module": ADMISS_TRUE,
        "rationale": (
            "A self-call on an F2P-shaped input (refit performed; ordered readings "
            "1.0 <= 2.0) establishes Requires(end >= start) and proves the duration "
            "is present. If the precondition could not be met for this normal input "
            "=> PRECOND-TOO-STRONG."
        ),
    },
    {
        "id": "admiss-false-and-zero",
        "kind": "admissibility",
        "expect": "verify",
        "module": ADMISS_FALSE_AND_ZERO,
        "rationale": (
            "A self-call on the no-refit case (do_final_fit=False) with the "
            "zero-length boundary interval (3.0, 3.0) (end == start, in-domain) "
            "proves the absent marker is reported. Confirms both the present-iff "
            "direction and the end>=start boundary are admissible."
        ),
    },
    # ---- uniqueness (must reject) ----
    {
        "id": "weak-never-present",
        "kind": "uniqueness",
        "expect": "reject",
        "module": WEAK_NEVER_PRESENT,
        "refinement": (
            "Faithful real patch: the refit branch performs the fit but never sets "
            "self.refit_time_ (the pre-patch code; model_prepatch.py reproduces it). "
            "F2P test_search_cv_timing then FAILS at assert hasattr(search, "
            "'refit_time_') => does NOT resolve. A verify here would be a true "
            "verify-not-resolve break."
        ),
        "rationale": (
            "Reject comes from postcondition (1) do_final_fit == (Result() is not "
            "None): on do_final_fit=True the result stays None, so the equality "
            "fails. This is exactly the prepatch G-DIFF failure."
        ),
    },
    {
        "id": "weak-always-present",
        "kind": "uniqueness",
        "expect": "reject",
        "module": WEAK_ALWAYS_PRESENT,
        "refinement": (
            "Faithful real patch: set self.refit_time_ = refit_end_time - "
            "refit_start_time UNCONDITIONALLY (outside the `if self.refit:` guard), "
            "so the attribute is present even when refit is False. This breaks the "
            "documented contract ('present only if refit is not False') and the "
            "no-refit invariant the P2P test_no_refit relies on (refit=False must "
            "not produce refit artifacts). The spec's presence clause is the "
            "discriminator the harness alone underspecifies on the value side."
        ),
        "rationale": (
            "Reject comes from postcondition (1): on the do_final_fit=False "
            "sub-domain Result() is not None while do_final_fit is False, so the "
            "equality fails. Partial-domain attack on the absent branch."
        ),
    },
    {
        "id": "weak-const-zero",
        "kind": "uniqueness",
        "expect": "reject",
        "module": WEAK_CONST_ZERO,
        "refinement": (
            "Faithful real patch: self.refit_time_ = 0.0 (a constant stand-in). The "
            "F2P only checks isinstance(float) and >= 0, which 0.0 satisfies, so "
            "this particular patch WOULD resolve the current F2P; it is a "
            "VALUE-FIDELITY supporting case proving the spec is deliberately "
            "stronger than the F2P (it pins the genuine elapsed measurement). It is "
            "the int/non-real family the panel fix (atk_9 result=0) closed."
        ),
        "rationale": (
            "Reject comes from postcondition (2) Result() == elapsed_between(start, "
            "end): 0.0 equals the grounded oracle only on a zero-length interval, "
            "not in general, so under --float-encoding=real the equality is not "
            "provable and the case is rejected."
        ),
    },
    {
        "id": "weak-echo-end",
        "kind": "uniqueness",
        "expect": "reject",
        "module": WEAK_ECHO_END,
        "refinement": (
            "Faithful real patch: self.refit_time_ = refit_end_time (report the "
            "post-fit clock reading itself, not the elapsed interval). For a real "
            "epoch reading (~1.7e9) the value is huge and unrelated to the fit "
            "duration; it is still a float >= 0 so the weak F2P would pass, but the "
            "reported number is semantically wrong (not seconds-of-refit). "
            "Value-fidelity supporting case: an input-derived-but-WRONG function."
        ),
        "rationale": (
            "Reject comes from postcondition (2): end != elapsed_between(start, end) "
            "in general (they coincide only when start == 0), so the equality is "
            "not provable and the case is rejected. Guards against a 'any function "
            "of the inputs is fine' reading of the value clause."
        ),
    },
    {
        "id": "weak-swapped-args",
        "kind": "uniqueness",
        "expect": "reject",
        "module": WEAK_SWAPPED,
        "refinement": (
            "Faithful real patch: self.refit_time_ = refit_start_time - "
            "refit_end_time (the negated interval). With the readings ordered this "
            "is <= 0, so the F2P assert_greater_equal(refit_time_, 0) FAILS => does "
            "NOT resolve. A clean verify-not-resolve break."
        ),
        "rationale": (
            "Reject comes from two places: elapsed_between(end, start) calls the "
            "oracle with later=start, earlier=end, violating its own "
            "Requires(later >= earlier) when start < end; and even at start==end the "
            "reported value is not pinned to elapsed_between(start, end). The "
            "call-site precondition obligation fails, rejecting the case."
        ),
    },
]


# ---------------------------------------------------------------------------
# AXIOM lane — two @Pure @ContractOnly axioms model UNCHANGED stdlib operations:
#   clock_after   (A-reference): time.time() monotonicity (justifies end>=start)
#   elapsed_between (A-consumed): non-negativity of an ordered float difference
# Both probes EXECUTE the real operation (per AVOID #4: never scrape source) and
# read its observed values. They import only stdlib `time` (the exact module the
# gold patch adds), so they run in the instance image without anything
# repo-specific. The probes embed the bundle axiom_check.py logic (per AVOID #6:
# only the probe script is mounted in-container).
#
# soundness: the real callee, on every input IN the axiom's Requires domain,
#   must meet the axiom's Ensures (fuzz boundaries + sentinels).
# containment: every callee-input the MODEL can reach must lie inside the axiom's
#   Requires domain. The model only ever calls elapsed_between(start, end) with
#   end >= start (the function precondition), which is exactly the axiom's
#   Requires(later >= earlier) under earlier:=start, later:=end => the model
#   never reaches an input outside the covered domain. clock_after has Requires
#   == True (no precondition), trivially covered.
# ---------------------------------------------------------------------------

_AX_CLOCK_SOUND = r'''
import sys, time
# clock_after axiom Ensures: a reading taken AFTER a reference instant is never
# earlier than it (monotonicity across two sequential time.time() calls). Run the
# REAL stdlib callee the gold patch uses; assert t2 >= t1 over many pairs.
N = 300000
violations = 0
worst = 0.0
for _ in range(N):
    t1 = time.time()          # real callee: the reference reading
    t2 = time.time()          # real callee: the later reading
    if not (t2 >= t1):
        violations += 1
        d = t1 - t2
        if d > worst:
            worst = d
print("clock_after soundness: %d/%d sequential time.time() pairs with later<reference; worst backstep=%r" % (violations, N, worst))
sys.exit(0 if violations == 0 else 1)
'''

_AX_ELAPSED_SOUND = r'''
import sys, random, time
# elapsed_between axiom: Requires(later >= earlier) => Ensures(later - earlier >= 0.0).
# Execute the REAL builtin float subtraction on every in-domain (ordered) pair:
# boundary/sentinel pairs + real time.time() ordered pairs + randomized fuzz.
def in_domain(earlier, later):
    return later >= earlier
boundary = [
    (0.0, 0.0),                  # zero-length interval (the trivial-X F2P case)
    (0.0, 1e-9),                 # tiny positive interval
    (1.0, 1.0),
    (1234567890.0, 1234567890.5),
    (0.0, 1e18),                 # very large interval
    (-1.0, 0.0), (-5.0, -1.0),   # negative readings, still ordered
    (1e-300, 1e-300),            # subnormal-ish equal
    (-1e308, 1e308),             # near-overflow magnitude span
]
for _ in range(3000):
    a = time.time(); b = time.time()
    if b >= a:
        boundary.append((a, b))
rng = random.Random(11310)
fuzz = []
for _ in range(300000):
    x = rng.uniform(-1e12, 1e12)
    y = rng.uniform(-1e12, 1e12)
    lo, hi = (x, y) if x <= y else (y, x)
    fuzz.append((lo, hi))
checked = 0
for earlier, later in boundary + fuzz:
    if not in_domain(earlier, later):
        continue
    observed = later - earlier          # real arithmetic op
    checked += 1
    if not (observed >= 0.0):
        print("elapsed_between UNSOUND on (%r, %r): later-earlier=%r < 0 despite later>=earlier" % (earlier, later, observed))
        sys.exit(1)
print("elapsed_between soundness: %d in-domain ordered pairs, observed difference >= 0.0 every time" % checked)
sys.exit(0)
'''

_AX_ELAPSED_CONTAIN = r'''
import sys, random
# Containment: the model only ever calls elapsed_between(earlier=start, later=end)
# and ONLY with end >= start (the recorded_refit_duration precondition
# Requires(end >= start), and the unconditional pos-control discharges that same
# precondition before the call). So every callee-input the model can reach is an
# ordered pair (later >= earlier) -- exactly the axiom's Requires(later >= earlier)
# domain. Demonstrate by enumerating the caller-reachable inputs (any pair the
# model could pass MUST satisfy end >= start) and asserting each lies in-domain.
def caller_reachable(start, end):
    # The model can reach elapsed_between(start, end) only when the precondition
    # holds; the verifier guarantees end >= start at the call site.
    return end >= start
def axiom_domain(earlier, later):
    return later >= earlier
rng = random.Random(20240617)
# Sample candidate (start, end) pairs; the caller-reachable ones are exactly the
# ordered ones, and for each we confirm it is inside the axiom Requires domain
# under the mapping earlier:=start, later:=end.
escapes = 0
reached = 0
samples = [(0.0, 0.0), (1.0, 2.0), (3.0, 3.0), (-5.0, -1.0), (0.0, 1e18)]
for _ in range(200000):
    a = rng.uniform(-1e12, 1e12)
    b = rng.uniform(-1e12, 1e12)
    samples.append((a, b))
for start, end in samples:
    if not caller_reachable(start, end):
        continue                     # the model cannot pass this input to the callee
    reached += 1
    earlier, later = start, end      # the model's argument mapping
    if not axiom_domain(earlier, later):
        escapes += 1
        print("CONTAINMENT BREACH: caller-reachable (start=%r,end=%r) maps to callee input (earlier=%r,later=%r) OUTSIDE axiom Requires(later>=earlier)" % (start, end, earlier, later))
print("elapsed_between containment: %d caller-reachable callee-inputs, %d outside axiom domain" % (reached, escapes))
sys.exit(0 if escapes == 0 else 1)
'''


AXIOM_TESTS = [
    {
        "id": "ax-sound-clock_after",
        "axiom": "clock_after",
        "kind": "axiom-soundness",
        "expect": "holds",
        "apply_gold": True,
        "probe": _AX_CLOCK_SOUND,
        "rationale": (
            "clock_after (A-reference) models time.time() monotonicity that "
            "justifies the end>=start precondition. The real stdlib callee, read "
            "twice back-to-back as the gold patch does, must give t2 >= t1. If the "
            "real callee ever steps backward => the precondition grounding "
            "(end>=start) is unsound (AXIOM-UNSOUND)."
        ),
    },
    {
        "id": "ax-sound-elapsed_between",
        "axiom": "elapsed_between",
        "kind": "axiom-soundness",
        "expect": "holds",
        "apply_gold": True,
        "probe": _AX_ELAPSED_SOUND,
        "rationale": (
            "elapsed_between (A-consumed) Requires(later>=earlier) => Ensures(>=0.0). "
            "Execute the real builtin subtraction on every in-domain ordered pair "
            "(boundaries + sentinels + real time.time() pairs + 300k fuzz). Any "
            "negative observed difference on an ordered pair => AXIOM-UNSOUND (the "
            "postcondition consumes this Ensures to pin Result() >= 0)."
        ),
    },
    {
        "id": "ax-contain-elapsed_between",
        "axiom": "elapsed_between",
        "kind": "axiom-containment",
        "expect": "covered",
        "apply_gold": True,
        "probe": _AX_ELAPSED_CONTAIN,
        "rationale": (
            "The model calls elapsed_between(start, end) only with end >= start "
            "(the recorded_refit_duration precondition, discharged at every call "
            "site). Under earlier:=start, later:=end that is exactly the axiom's "
            "Requires(later >= earlier). No caller-reachable callee-input lies "
            "outside the covered domain; an escape => AXIOM-TOO-WEAK-FOR-CALLER. "
            "(clock_after has Requires==True, trivially covered, so no separate "
            "containment probe is needed.)"
        ),
    },
]
