# properties.py — PBT manifest for pydata__xarray-6599. NOT a Nagini module; a
# record of adversarially-reasoned falsification cases the runner
# (swebench_nagini.pbt) executes and stamps with RESULT. Spec cases are full
# model.py variants that share the FROZEN spec byte-for-byte (region-surgery:
# only text strictly inside an `# impl-start` / `# impl-end` region is edited)
# and swap the implementation; checked by Nagini verify + markers.same_spec.
# Axiom cases are real-callee probes run in the instance Docker image.
#
# ---------------------------------------------------------------------------
# Defended surface (reasoned from model.py, refinement.md, mapping.md, the gold
# patch and the F2P test test_polyval[timedelta-False]):
#
#   coerce_values_to_float(kind, values, reference) -> List[int] coerces a
#   variable's magnitudes to float, dispatched on the value category `kind`:
#     * kind == TIME_POINT (datetime "M"): numeric via the instant-relative
#       measurement = the UNCHANGED callee, modeled by the @ContractOnly axiom
#       `elapsed_since` (per-element subtraction of the reference instant). The
#       axiom is DEFINED ONLY for kind == TIME_POINT (Requires) and only on
#       well_defined_magnitudes (no NaT sentinel -2**63).
#     * kind == TIME_SPAN (timedelta "m"): numeric via the DIRECT magnitude read
#       = the NEW branch the patch adds (x.astype(float)), modeled deeply by the
#       @Pure `magnitude_read` == the identity on magnitudes.
#     * kind == OTHER: already-numeric, returned unchanged.
#
#   The single READ-ONLY input is `values`: Requires(Acc(list_pred(values),1/2))
#   (and the matching Ensures preserves it). => the FRAME-MUTATION probe is
#   MANDATORY (PBT_PLAN directive 5).
#
#   Load-bearing postcondition clauses (where each rival dies):
#     - TIME_POINT: ToSeq(Result()) == elapsed_since(kind, ToSeq(values), reference)
#       (consumed axiom) + well_defined_magnitudes(ToSeq(values)) preserved.
#     - TIME_SPAN:  ToSeq(Result()) == magnitude_read(ToSeq(values))   AND
#                   ToSeq(Result()) == ToSeq(values)   (identity; GROUNDED).
#     - OTHER:      ToSeq(Result()) == ToSeq(values)   (identity; GROUNDED).
#
#   The DECISIVE behavioural fact (G-DIFF, the bug): a duration must NOT be
#   routed through the timestamp measurement. `elapsed_since` carries
#   Requires(kind == TIME_POINT); routing a TIME_SPAN input into it (the
#   pre-patch single guard "mM") fails that precondition — mirroring the real
#   numpy UFuncTypeError on timedelta - datetime64. That is the partial-domain
#   pressure point, reproduced below.
#
# Ungrounded-oracle echo: N/A as a WRONG echo. The only @ContractOnly oracle is
# `elapsed_since`, and the TIME_POINT postcondition IS pinned to it — echoing it
# is precisely the gold's correct computation, not a wrong answer-key echo. The
# TIME_SPAN/OTHER oracles (magnitude_read / identity) are fully grounded in
# `values`. So there is no wrong echo to build; instead we supply honest
# positive controls (below) and pin the grounded identities with reject cases.
#
# Region-surgery discipline: every spec variant is built by _swap on the frozen
# model.py, editing ONLY text strictly inside the # impl-start / # impl-end
# region (the per-branch loop invariants live inside that region, so same_spec
# stays True even when an invariant local is touched). The frozen spec view
# (axioms / pure / pre / post regions) is NEVER altered.
from pathlib import Path

INSTANCE = "pydata__xarray-6599"
FLOAT_ENCODING = None  # meta.json float_encoding is null (precision-independent int carrier)

_BASE = (Path(__file__).parent / "model.py").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# ---------------------------------------------------------------------------
# Region anchors — all strictly INSIDE the impl region (between # impl-start and
# # impl-end). Editing them keeps the frozen spec intact (same_spec == True).
# ---------------------------------------------------------------------------

# The TIME_SPAN (duration) branch body: the NEW branch the patch adds. Its loop
# appends each magnitude directly (the identity == magnitude_read). 12-space
# indent (the line is inside the `while j < len(values):` loop body).
_SPAN_APPEND = "            out.append(values[j])\n"

# The TIME_POINT (timestamp) branch's per-element append of the measured value.
_POINT_APPEND = "            result.append(measured[i])\n"

# The OTHER (passthrough) branch's per-element append.
_OTHER_APPEND = "            passthrough.append(values[m])\n"

# The whole TIME_SPAN branch head (guard + comment) — for replacing the branch.
_SPAN_BRANCH_HEAD = (
    "    elif kind == TIME_SPAN:\n"
    "        # read each duration's magnitude directly (the new branch): the float\n"
    "        # magnitude equals the input magnitude in the base resolution\n"
)


# ===========================================================================
# SPEC LANE
# ===========================================================================

# === POSITIVE CONTROL #1 (soundness) =======================================
# TIME_SPAN branch: bind the magnitude to a typed local before appending. A
# local-variable reshape that keeps the SAME forward-append shape and EVERY
# loop invariant / framing Assert (ToSeq(out) == ToSeq(values).take(j)) intact,
# so the gold proof obligations are untouched (no induction trap — directive
# #2/#3). Behaviourally identical. MUST verify; else SPEC-TOO-STRONG.
_POS_SPAN_LOCAL = _swap(
    _BASE, _SPAN_APPEND,
    "            v = values[j]  # type: int\n"
    "            out.append(v)\n",
)

# === POSITIVE CONTROL #2 (soundness) =======================================
# TIME_POINT branch: bind the measured element to a typed local before
# appending. Keeps the measurement call, the `measured == elapsed_since(...)`
# invariant, the `ToSeq(result) == measured.take(i)` invariant and both framing
# Asserts verbatim — only the executable append is reshaped. MUST verify.
_POS_POINT_LOCAL = _swap(
    _BASE, _POINT_APPEND,
    "            mv = measured[i]  # type: int\n"
    "            result.append(mv)\n",
)

# === ADMISSIBILITY (precondition admits a normal F2P-shaped duration) ======
# Inside coerce_values_to_float's OWN impl region we prepend a self-call on the
# F2P-shaped TIME_SPAN literal [1000,2000,3000] (the timedelta magnitudes the
# F2P test uses), then fall through to the gold body. The call site must (a)
# establish the Requires for this legitimate duration input (kind==TIME_SPAN,
# so the TIME_POINT-only well_defined_magnitudes guard is vacuously satisfied)
# — else PRECOND-TOO-STRONG — and (b) the postcondition then guarantees
# ToSeq(out) == ToSeq(probe) == the input magnitudes, which the asserts confirm.
# coerce_values_to_float is a normal (non-@Pure) function, so a self-call needs
# no termination measure; only the callee precondition is discharged. MUST verify.
_ADMISS = _swap(
    _BASE,
    "    if kind == TIME_POINT:\n",
    "    probe = [1000, 2000, 3000]  # type: List[int]\n"
    "    Assert(len(probe) == 3)\n"
    "    out_probe = coerce_values_to_float(TIME_SPAN, probe, reference)  # type: List[int]\n"
    "    # the F2P duration input must coerce to its own magnitudes (identity).\n"
    "    Assert(ToSeq(out_probe) == ToSeq(probe))\n"
    "    if kind == TIME_POINT:\n",
)

# === FRAME-MUTATION (uniqueness; MANDATORY — read-only `values`) ===========
# A rival that WRITES to the read-only input `values` inside the TIME_SPAN loop.
# With only Acc(list_pred(values),1/2) the __setitem__ needs the FULL predicate,
# so it must be rejected for INSUFFICIENT PERMISSION. Gold invariants/asserts
# kept verbatim so the rejection is attributable to the write, not a proof gap.
# expect="reject".
_FRAME_MUT = _swap(
    _BASE, _SPAN_APPEND,
    "            out.append(values[j])\n"
    "            values[j] = values[j]\n",
)

# === FRAME-MUTATION supporting case: write `values` in the OTHER branch =====
_FRAME_MUT_OTHER = _swap(
    _BASE, _OTHER_APPEND,
    "            passthrough.append(values[m])\n"
    "            values[m] = values[m]\n",
)

# === PARTIAL-DOMAIN / THE BUG (uniqueness): route duration through the =======
# === timestamp measurement (the pre-patch single "mM" guard) ===============
# Replace the TIME_SPAN branch so it computes its result via elapsed_since (the
# instant-relative measurement) instead of the direct magnitude read. This is
# EXACTLY model_prepatch.py's defect. elapsed_since carries Requires(kind ==
# TIME_POINT); called here with kind == TIME_SPAN, that precondition "might not
# hold" => verification fails on precisely that clause. expect="reject".
_SPAN_VIA_MEASUREMENT = _swap(
    _BASE,
    _SPAN_BRANCH_HEAD +
    "        out = []  # type: List[int]\n"
    "        j = 0\n"
    "        while j < len(values):\n"
    "            # invariants-start\n"
    "            Invariant(Acc(list_pred(values), 1 / 2))\n"
    "            Invariant(Acc(list_pred(out)))\n"
    "            Invariant(0 <= j and j <= len(values))\n"
    "            Invariant(ToSeq(out) == ToSeq(values).take(j))\n"
    "            # invariants-end\n"
    "            out.append(values[j])\n"
    "            j = j + 1\n",
    _SPAN_BRANCH_HEAD +
    "        out = elapsed_since(kind, ToSeq(values), reference)\n"
    "        result_span = []  # type: List[int]\n"
    "        j = 0\n"
    "        while j < len(values):\n"
    "            # invariants-start\n"
    "            Invariant(Acc(list_pred(values), 1 / 2))\n"
    "            Invariant(Acc(list_pred(result_span)))\n"
    "            Invariant(0 <= j and j <= len(values))\n"
    "            Invariant(len(out) == len(values))\n"
    "            Invariant(ToSeq(result_span) == out.take(j))\n"
    "            # invariants-end\n"
    "            result_span.append(out[j])\n"
    "            j = j + 1\n",
)
# Also fix the dangling return/asserts of the old branch to use the new local.
_SPAN_VIA_MEASUREMENT = _swap(
    _SPAN_VIA_MEASUREMENT,
    "        Assert(ToSeq(out) == ToSeq(values).take(len(values)))\n"
    "        Assert(ToSeq(values).take(len(values)) == ToSeq(values))\n"
    "        return out\n",
    "        return result_span\n",
)

# === PARTIAL-DOMAIN (uniqueness): duration returns reference-subtracted ======
# === magnitudes instead of the identity ====================================
# A rival that subtracts `reference` from each duration magnitude (as if a span
# had a reference instant). For reference != 0 this diverges from the required
# identity. Must be rejected by ToSeq(Result()) == magnitude_read(ToSeq(values))
# == ToSeq(values). expect="reject".
_SPAN_SUBTRACT_REF = _swap(
    _BASE, _SPAN_APPEND,
    "            out.append(values[j] - reference)\n",
)

# === PARTIAL-DOMAIN (uniqueness): corrupt only the FIRST duration element ===
# Correct on every duration index except j == 0, which is forced to a constant.
# The loop invariant ToSeq(out) == ToSeq(values).take(j) fails at the first
# step => reject. Targets the input that fails first. expect="reject".
_SPAN_FIRST_WRONG = _swap(
    _BASE, _SPAN_APPEND,
    "            if j == 0:\n"
    "                out.append(0)\n"
    "            else:\n"
    "                out.append(values[j])\n",
)

# === SUPPORTING near-miss (uniqueness): OTHER branch returns a constant ======
# The cheapest wrong passthrough: append a constant 0 instead of values[m].
# Wrong on any non-zero numeric input; rejected by ToSeq(Result()) ==
# ToSeq(values). A supporting mechanical case carrying a real refinement.
_OTHER_CONST = _swap(
    _BASE, _OTHER_APPEND,
    "            passthrough.append(0)\n",
)

# === SUPPORTING near-miss (uniqueness): duration returns a constant ==========
# Append a constant 1 in the TIME_SPAN branch. Wrong on the F2P input
# [1000,2000,3000]; rejected by the magnitude_read / identity postcondition.
_SPAN_CONST = _swap(
    _BASE, _SPAN_APPEND,
    "            out.append(1)\n",
)


SPEC_TESTS = [
    {
        "id": "pos-span-local-reshape",
        "kind": "soundness",
        "expect": "verify",
        "module": _POS_SPAN_LOCAL,
        "rationale": "structurally-different CORRECT impl of the duration branch "
                     "(bind the magnitude to a typed local before append); keeps "
                     "the forward-append shape + every loop invariant + framing "
                     "Assert. Must verify against ToSeq(Result())==magnitude_read"
                     "(==identity); else SPEC-TOO-STRONG.",
    },
    {
        "id": "pos-point-local-reshape",
        "kind": "soundness",
        "expect": "verify",
        "module": _POS_POINT_LOCAL,
        "rationale": "structurally-different CORRECT impl of the timestamp branch "
                     "(bind measured[i] to a typed local before append); keeps the "
                     "measurement call and the measured==elapsed_since(...) / "
                     "ToSeq(result)==measured.take(i) invariants verbatim. A "
                     "faithful correct impl must verify; else SPEC-TOO-STRONG.",
    },
    {
        "id": "admiss-f2p-timedelta",
        "kind": "admissibility",
        "expect": "verify",
        "module": _ADMISS,
        "rationale": "a positive-control self-call on the F2P duration input "
                     "[1000,2000,3000] with kind==TIME_SPAN. The Requires must "
                     "admit a normal duration (the TIME_POINT-only "
                     "well_defined_magnitudes guard is vacuous for TIME_SPAN) and "
                     "the grounded postcondition must yield the input magnitudes "
                     "(Assert ToSeq(out_probe)==ToSeq(probe)); else PRECOND-TOO-STRONG.",
    },
    {
        "id": "frame-mutate-readonly-values-span",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _FRAME_MUT,
        "refinement": "a faithful real patch that wrote back into the variable's "
                      "shared underlying array (x.data) while coercing would "
                      "corrupt the DataArray the caller still holds (_ensure_numeric "
                      "operates on the user's data); the F2P asserts "
                      "assert_allclose(expected, actual) on the ORIGINAL variable, "
                      "so a mutated input would not produce the gold result and "
                      "would NOT resolve test_polyval[timedelta-False].",
        "rationale": "`values` is Requires(Acc(list_pred(values),1/2)) — read-only. "
                     "The write `values[j]=...` (__setitem__) needs the FULL "
                     "list_pred, so it must be rejected for INSUFFICIENT PERMISSION "
                     "(permission system), not a postcondition mismatch. If it "
                     "verified, the read-only frame is unguarded (SPEC-TOO-WEAK).",
    },
    {
        "id": "frame-mutate-readonly-values-other",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _FRAME_MUT_OTHER,
        "refinement": "the same in-place write in the passthrough branch would "
                      "mutate the caller's already-numeric array; the P2P / F2P "
                      "tests read the original values, so the result diverges from "
                      "gold and would NOT resolve.",
        "rationale": "rejected for INSUFFICIENT PERMISSION on `values` (held at "
                     "1/2) in the OTHER branch. Supporting frame-integrity case.",
    },
    {
        "id": "weak-duration-via-measurement",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _SPAN_VIA_MEASUREMENT,
        "refinement": "this IS the pre-patch bug (the single guard "
                      "'if x.dtype.kind in \"mM\"' routing durations into "
                      "datetime_to_numeric). In reality timedelta64 - datetime64 "
                      "raises numpy.UFuncTypeError, so polyval would error on the "
                      "timedelta input and test_polyval[timedelta-False] would NOT "
                      "resolve (it would raise, not produce [1000.,2000.,3000.]).",
        "rationale": "the duration branch calls elapsed_since(kind, ...) with "
                     "kind==TIME_SPAN, but elapsed_since carries "
                     "Requires(kind == TIME_POINT) — verification fails on exactly "
                     "that 'kind == TIME_POINT might not hold' clause (the "
                     "discriminating fact, mirrored by model_prepatch.py / G-DIFF). "
                     "If it verified, the spec would not sense the type-"
                     "applicability bug (SPEC-TOO-WEAK).",
    },
    {
        "id": "weak-duration-subtract-reference",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _SPAN_SUBTRACT_REF,
        "refinement": "subtracting a reference instant from a duration (treating a "
                      "span as if it had an absolute origin) is the very category "
                      "error the patch removes; for a non-zero reference the "
                      "coerced magnitudes are shifted, so polyval(0 + 1*x) would "
                      "return shifted values and the assert_allclose F2P fails.",
        "rationale": "rejected by ToSeq(Result()) == magnitude_read(ToSeq(values)) "
                     "== ToSeq(values): out[j]==values[j]-reference is not provably "
                     "equal to values[j] (for reference != 0). The grounded identity "
                     "postcondition pins the duration read. If it verified, the "
                     "duration conversion is unpinned (SPEC-TOO-WEAK).",
    },
    {
        "id": "weak-duration-first-element-wrong",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _SPAN_FIRST_WRONG,
        "refinement": "a real patch correct on all but the first duration element "
                      "still mis-coerces values[0] (here to 0); polyval observes "
                      "the whole array, so the F2P assert_allclose([1000.,2000.,"
                      "3000.]) fails on the first element — would NOT resolve.",
        "rationale": "rejected by the loop invariant ToSeq(out)==ToSeq(values)."
                     "take(j), which fails on the first iteration (out[0]==0 != "
                     "values[0]), hence the postcondition identity fails. "
                     "Partial-domain (first-element) divergence.",
    },
    {
        "id": "weak-other-constant",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _OTHER_CONST,
        "refinement": "constant-filling the already-numeric passthrough drops the "
                      "real values; the P2P/F2P inputs that pass through the OTHER "
                      "branch (already-float coefficients/values) would be zeroed, "
                      "so polyval returns the wrong result and the tests fail.",
        "rationale": "rejected by Ensures(Implies(kind==OTHER, ToSeq(Result())=="
                     "ToSeq(values))): appending 0 violates the identity. "
                     "Supporting near-miss with a real refinement.",
    },
    {
        "id": "weak-duration-constant",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _SPAN_CONST,
        "refinement": "returning a constant for every duration magnitude collapses "
                      "[1000,2000,3000] to [1,1,1]; polyval(0 + 1*x) would then "
                      "return [1.,1.,1.] not [1000.,2000.,3000.], so "
                      "test_polyval[timedelta-False] fails to resolve.",
        "rationale": "rejected by ToSeq(Result()) == magnitude_read(ToSeq(values)) "
                     "== ToSeq(values): a constant is not provably the input "
                     "magnitudes. Supporting near-miss.",
    },
]


# ===========================================================================
# AXIOM LANE
# ===========================================================================
#
# Two kind-A deep models:
#   * `elapsed_since`   — A-consumed @ContractOnly axiom; the proof uses its
#                         Ensures (per-element subtraction) AND its
#                         Requires (kind==TIME_POINT, well_defined_magnitudes).
#   * `magnitude_read`  — A-reference deep model (== timedelta astype(float)),
#                         validated equal to the real op out-of-band.
# The persisted axiom_check.py already runs BOTH real callees on boundary +
# 20000 fuzz inputs (datetime_to_numeric per-element subtraction on the NaT-free
# domain; precondition honesty = raises on timedelta; the NaT-sentinel exclusion
# necessity; and timedelta astype(float)==raw ns magnitudes). We embed its
# source (read on the HOST at load time — the runner mounts ONLY the probe at
# /work; axiom_check.py is NOT in-container) and drive main() as the soundness
# probe. utf-8-safe (pure runtime; no disk reads of bundle files).

_AXIOM_CHECK_SRC = (Path(__file__).parent / "axiom_check.py").read_text(encoding="utf-8")

# --- axiom-soundness: run the REAL callees via the gold-grounded axiom_check.py
_AX_SOUND_PROBE = _AXIOM_CHECK_SRC + """

# ---- PBT axiom-soundness driver (appended) --------------------------------
import sys as _sys
print("PBT axiom-soundness: running real datetime_to_numeric (A-consumed "
      "elapsed_since) + real timedelta64.astype(float) (A-reference "
      "magnitude_read) soundness obligations on boundary + 20000 fuzz inputs")
_rc = main()
_sys.exit(0 if _rc == 0 else 1)
"""

# --- axiom-containment: enumerate EXACTLY the callee inputs the MODEL can reach
# and assert each lies in elapsed_since's Requires domain (kind==TIME_POINT AND
# well_defined_magnitudes). The model calls elapsed_since ONLY in the TIME_POINT
# branch (and in the postcondition Ensures Implies(kind==TIME_POINT, ...)). At
# every such site kind==TIME_POINT holds, and the caller precondition supplies
# Implies(kind==TIME_POINT, well_defined_magnitudes(ToSeq(values))). So both
# Requires atoms are met at every reachable call. We prove this statically over
# the model source: every elapsed_since call passes `kind`, and every executable
# call site is guarded by `kind == TIME_POINT`. (stdlib-only, utf-8-safe; runs
# in-container but reads nothing from disk — model source is embedded at load.)
_MODEL_SRC = (Path(__file__).parent / "model.py").read_text(encoding="utf-8")

_AX_COVER_PROBE = (
    "import sys, ast\n"
    "SRC = " + repr(_MODEL_SRC) + "\n"
    "tree = ast.parse(SRC)\n"
    "# locate the modeled function and the @ContractOnly axiom def\n"
    "funcs = {n.name: n for n in ast.walk(tree) if isinstance(n, ast.FunctionDef)}\n"
    "if 'coerce_values_to_float' not in funcs:\n"
    "    print('modeled function not found'); sys.exit(1)\n"
    "caller = funcs['coerce_values_to_float']\n"
    "# 1) collect EXECUTABLE elapsed_since call sites inside the impl region.\n"
    "#    The impl region is delimited by the `# impl-start` / `# impl-end` markers.\n"
    "lines = SRC.splitlines()\n"
    "impl_lo = next(i for i, L in enumerate(lines) if '# impl-start' in L)\n"
    "impl_hi = next(i for i, L in enumerate(lines) if '# impl-end' in L)\n"
    "calls = []  # (lineno, arg0_src)\n"
    "for sub in ast.walk(caller):\n"
    "    if isinstance(sub, ast.Call) and getattr(sub.func, 'id', None) == 'elapsed_since':\n"
    "        calls.append((sub.lineno, ast.dump(sub.args[0]) if sub.args else None))\n"
    "exec_calls = [c for c in calls if impl_lo + 1 <= c[0] <= impl_hi + 1]\n"
    "print('elapsed_since call sites (all):', [c[0] for c in calls])\n"
    "print('elapsed_since EXECUTABLE call sites (impl region):', [c[0] for c in exec_calls])\n"
    "if not exec_calls:\n"
    "    print('no executable elapsed_since call in impl region'); sys.exit(1)\n"
    "# 2) every executable call passes `kind` as the first arg (the tag the\n"
    "#    Requires(kind==TIME_POINT) constrains).\n"
    "kind_arg = ast.dump(ast.Name(id='kind', ctx=ast.Load()))\n"
    "bad_arg = [c for c in exec_calls if c[1] != kind_arg]\n"
    "if bad_arg:\n"
    "    print('an elapsed_since call passes a non-`kind` first arg:', bad_arg); sys.exit(1)\n"
    "# 3) the impl-region call site lives strictly INSIDE an `if kind == TIME_POINT:`\n"
    "#    guard. Verify the TIME_POINT guard precedes the elapsed_since call and the\n"
    "#    TIME_SPAN/else branches contain NO elapsed_since call.\n"
    "impl_src = '\\n'.join(lines[impl_lo: impl_hi + 1])\n"
    "if 'if kind == TIME_POINT:' not in impl_src:\n"
    "    print('TIME_POINT guard missing from impl'); sys.exit(1)\n"
    "# crude branch slicing on the impl text: the elapsed_since execution must occur\n"
    "# AFTER the TIME_POINT guard and BEFORE the `elif kind == TIME_SPAN:` head.\n"
    "guard_at = impl_src.index('if kind == TIME_POINT:')\n"
    "span_at = impl_src.index('elif kind == TIME_SPAN:')\n"
    "first_call_at = impl_src.index('elapsed_since(')\n"
    "if not (guard_at < first_call_at < span_at):\n"
    "    print('elapsed_since is not confined to the TIME_POINT branch'); sys.exit(1)\n"
    "after_span = impl_src[span_at:]\n"
    "if 'elapsed_since(' in after_span:\n"
    "    print('elapsed_since reachable from the TIME_SPAN/OTHER branch — a duration\\n'\n"
    "          'could reach the timestamp measurement: AXIOM-TOO-WEAK-FOR-CALLER'); sys.exit(1)\n"
    "# 4) the caller precondition supplies the second Requires atom\n"
    "#    well_defined_magnitudes for exactly the TIME_POINT case.\n"
    "pre_src = SRC\n"
    "need = 'Requires(Implies(kind == TIME_POINT, well_defined_magnitudes(ToSeq(values))))'\n"
    "if need not in pre_src:\n"
    "    print('caller does not establish well_defined_magnitudes for TIME_POINT'); sys.exit(1)\n"
    "print('AXIOM-CONTAINMENT OK: elapsed_since is called only inside the\\n'\n"
    "      'kind==TIME_POINT branch (and the matching Implies postcondition),\\n'\n"
    "      'always with the `kind` tag; the caller precondition pins\\n'\n"
    "      'well_defined_magnitudes for TIME_POINT. Both axiom Requires atoms\\n'\n"
    "      '(kind==TIME_POINT, well_defined_magnitudes) hold at every reachable\\n'\n"
    "      'call. No TIME_SPAN/OTHER (duration/numeric) input reaches the\\n'\n"
    "      'timestamp measurement, so every caller-reachable callee input is\\n'\n"
    "      'inside the axiom domain.')\n"
    "sys.exit(0)\n"
)

AXIOM_TESTS = [
    {
        "id": "ax-sound-elapsed_since-and-magnitude_read",
        "axiom": "elapsed_since",
        "kind": "axiom-soundness",
        "expect": "holds",
        "apply_gold": True,
        "probe": _AX_SOUND_PROBE,
        "rationale": "the proof consumes elapsed_since's Ensures (per-element "
                     "subtraction with reference 0) on its NaT-free domain AND its "
                     "Requires honesty (the real datetime_to_numeric RAISES on a "
                     "timedelta input — the type-applicability fact the bug "
                     "violates). It also relies on magnitude_read == real timedelta "
                     "astype(float). The gold-grounded axiom_check.py runs both "
                     "real callees on boundary + 20000 fuzz inputs (incl. int64 "
                     "extremes and the NaT sentinel -2**63, where the sentinel-"
                     "exclusion is shown NECESSARY). Any violation => AXIOM-UNSOUND.",
    },
    {
        "id": "ax-cover-elapsed_since",
        "axiom": "elapsed_since",
        "kind": "axiom-containment",
        "expect": "covered",
        "apply_gold": True,
        "probe": _AX_COVER_PROBE,
        "rationale": "elapsed_since's Requires is (kind==TIME_POINT AND "
                     "well_defined_magnitudes). The model calls it ONLY inside the "
                     "kind==TIME_POINT branch (never from the TIME_SPAN/OTHER "
                     "branch), always with the `kind` tag, and the caller "
                     "precondition pins well_defined_magnitudes for exactly the "
                     "TIME_POINT case. Every caller-reachable callee input is "
                     "inside the axiom domain; a duration/numeric input reaching "
                     "the measurement would be AXIOM-TOO-WEAK-FOR-CALLER. (Covering "
                     "MORE than the caller reaches — e.g. a general reference — is "
                     "sound, not a defect.)",
    },
]
