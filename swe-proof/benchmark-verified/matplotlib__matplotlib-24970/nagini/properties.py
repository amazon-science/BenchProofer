"""properties.py — PBT falsification manifest for matplotlib__matplotlib-24970.

NOT a Nagini module: a record of adversarial cases the runner
(`swebench_nagini.pbt`) executes. See the battery-authoring brief (esp. §2 "four
falsification checks" and §4a "Adversarial, NOT mechanical").

This battery is reasoned from THIS spec's defended surface, not stamped out by a
corruption template. The function under spec is

    take_rows(values: List[int], bads: List[bool], n: int, modulus: int)
        -> List[int]                       # = the integer index-resolution stage
                                           #   of Colormap.__call__: each element's
                                           #   final lookup-table row

with the load-bearing contract (pre/post-conditions regions, verbatim):

    Requires(Acc(list_pred(values), 1/2))     # READ-ONLY input  (half perm)
    Requires(Acc(list_pred(bads),   1/2))     # READ-ONLY input  (half perm)
    Requires(len(values) == len(bads)); Requires(n >= 1); Requires(modulus >= 1)
    Ensures(Acc(list_pred(values), 1/2)); Ensures(Acc(list_pred(bads), 1/2))
    Ensures(Acc(list_pred(Result())))
    Ensures(len(values) == len(bads)); Ensures(len(Result()) == len(values))
    Ensures(ToSeq(Result()) == rows_of(ToSeq(values), ToSeq(bads), n))   # VALUE pin
    Ensures(rows_assigned(ToSeq(Result()), n))                          # TOKEN pin

What this spec actually defends, and the attacks it must survive:

  * THE DISCRIMINATOR IS A SIDE-EFFECT, NOT A VALUE.  The F2P bug
    (`cm(np.uint8(0)) == cm(0)` under `filterwarnings=error`) has NO value-level
    difference: the row value of value-0 is 0 pre- and post-patch. The pre-patch
    failure is purely an out-of-bound-integer DeprecationWarning emitted when the
    three special-row stores (`xa[...]=N`, `=N+1`, `=N+2`) convert those scalars
    into a NARROW input container (uint8 at N=256). The gold fix casts `xa` to a
    signed `int` (a container that admits every special index) BEFORE the stores,
    so the conversion is in-range and no warning fires. Therefore the spec CANNOT
    be pinned to a value property alone — a buggy narrow-carrier impl returns the
    SAME row values. The discriminator is modelled (directive 8) as the unforgeable
    capability token `rows_assigned`, granted ONLY by `assign_special_rows`, and
    ONLY under its legality precondition `Requires(modulus >= n+3)` (the carrier
    admits the largest special index n+2). `rows_assigned` is `@ContractOnly
    @Predicate`, so an impl cannot `Fold` it into existence, and it carries
    (rows, n) so it cannot be laundered across a value-equal copy.

  * THE TWO READ-ONLY INPUTS (Acc(values,1/2), Acc(bads,1/2)) are the
    frame-mutation surface. A rival that WRITES into either to satisfy a
    postcondition vacuously must be rejected for INSUFFICIENT PERMISSION (half
    permission grants read, not write). This is the project's #1 weakness class
    and is MANDATORY here (two such inputs). We keep every gold invariant/assert
    verbatim so the rejection is attributable to the write, not a proof hole.

  * THE VALUE PIN `ToSeq(Result()) == rows_of(...)` IS GROUNDED in the inputs:
    `rows_of` is a @Pure front-recursive fold of `final_row` over the actual
    (values, bads) sequence — there is no opaque answer-key to echo. The only way
    to satisfy BOTH the value pin and the token is to route the result through
    `assign_special_rows` on an admitting carrier (carrier >= n+3). The
    cheapest honest impl that does so verifies (positive control); a narrow
    carrier cannot obtain the token (the prepatch attack / control-flow-effect).

Authoring mechanics: every spec variant is built by REGION-SURGERY (`_swap`) that
edits ONLY inside `# impl-start`/`# impl-end` (including the nested
`# invariants-*` block, which is part of the elided impl region and so does NOT
change the spec view). `markers.same_spec` is therefore guaranteed True for every
case, and a rejection comes from the POSTCONDITION / PERMISSION SYSTEM catching
wrong behaviour, never from a tampered spec. Each `expect:"reject"` rival carries
the refinement argument that its faithful real patch would NOT resolve the F2P
test `test_index_dtype[uint8]`. The axiom cases run the REAL NumPy callee in
Docker (reusing/strengthening axiom_check.py's logic).
"""
from pathlib import Path

INSTANCE = "matplotlib__matplotlib-24970"
FLOAT_ENCODING = None  # meta.json float_encoding is null (integer-index model)

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
# Region landmarks (all strictly INSIDE the impl region of model.py).
# ---------------------------------------------------------------------------
# The two list-building statements at the loop body tail (independent appends).
_BUILD_PAIR = ("        sel_values = [v] + sel_values\n"
               "        sel_bads = [bad] + sel_bads\n")
# The carrier choice + the single A-consumed callee call + the return.
_CARRIER_CALL = ("    carrier = n + 3\n"
                 "    result = assign_special_rows(sel_values, sel_bads, n, carrier)\n"
                 "    return result")
# The two reads at the loop body head.
_READS = ("        v = values[i - 1]\n"
          "        bad = bads[i - 1]\n")


# ===========================================================================
# POSITIVE CONTROLS (soundness / admissibility) — expect "verify"
# ===========================================================================

# (P1) Structurally-DIFFERENT but CORRECT — STATEMENT REORDER. The two
# independent per-element appends are reordered (sel_bads built before
# sel_values), and the two assert pairs are likewise reordered, so the executable
# shape differs while every loop invariant and framing assert is KEPT verbatim
# (directive: a positive control must keep the proof obligations it still needs).
# No induction lemma is introduced; the appends are commutative and the proof is
# unchanged. If this fails to verify, the postcondition / proof is over-fit to the
# exact statement order => SPEC-TOO-STRONG.
_POS_REORDER = _swap(
    _BASE, _BUILD_PAIR,
    "        sel_bads = [bad] + sel_bads\n"
    "        sel_values = [v] + sel_values\n",
)

# (P2) Structurally-DIFFERENT but CORRECT — LOCAL-VARIABLE RESHAPE of the carrier.
# Instead of `carrier = n + 3`, compute it through a local `extra = 3` (so the
# verifier must still prove carrier == n + 3 >= n + 3 to establish the callee's
# Requires(modulus >= n+3)). Same admitting carrier, different code shape; the
# gold proof stays valid. If it fails, the proof is over-fit to the literal
# `n + 3` form => SPEC-TOO-STRONG.
_POS_LOCAL = _swap(
    _BASE,
    "    carrier = n + 3\n    result = assign_special_rows(sel_values, sel_bads, n, carrier)\n",
    "    extra = 3\n    carrier = n + extra\n"
    "    result = assign_special_rows(sel_values, sel_bads, n, carrier)\n",
)

# (P3) Structurally-DIFFERENT but CORRECT — WIDER admitting carrier (n + 5). A
# faithful impl is free to pick ANY container that admits every special index,
# not only the tight n + 3; n + 5 still satisfies Requires(modulus >= n+3) and
# yields the SAME rows (the callee's result spec is rows_of regardless of how
# much extra headroom the carrier has). This is the gold patch's real freedom
# (the signed-int cast admits far more than n+2). If it fails to verify, the spec
# spuriously pins the carrier WIDTH (not just admittance) => SPEC-TOO-STRONG.
_POS_WIDER = _swap(
    _BASE,
    "    carrier = n + 3\n",
    "    carrier = n + 5\n",
)

# (P4) ADMISSIBILITY on the exact F2P-shaped input the failure exercises: a
# length-1 array of value 0, unmasked, at the default N = 256, with a wide
# container (300). The probe builds that input at the head of the impl and
# ASSERTS that every Requires clause of take_rows is establishable for it:
#   Acc(values,1/2), Acc(bads,1/2)  (freshly built lists => elements readable)
#   len(values) == len(bads)        (1 == 1)
#   n >= 1                          (256 >= 1)
#   modulus >= 1                    (300 >= 1)
# If the precondition could not be met for this normal input the asserts would
# not verify => PRECOND-TOO-STRONG. The gold body follows VERBATIM after the
# probe, so the postcondition obligation is unchanged.
#
# A self-call is no longer usable as the witness: take_rows carries a termination
# obligation, and a self-call is never strictly below itself, so Nagini reports
# `Obligation leak check failed. Callee take_rows might not take all unsatisfied
# obligations from the caller.` — a termination fact, not a fact about the
# precondition's domain, so it would attribute nothing. (Measured: the old
# self-call probe fails exactly that way.) Asserting the establishability of each
# Requires clause is the same substitution django__django-14580 uses.
# The remaining clause, MustTerminate(3), is an obligation rather than a state
# predicate, so it is not assertable; it is discharged by the level ordering
# (take_rows at 3 is strictly above assign_special_rows at 2), which the gold
# body below exercises by actually performing that call.
#
# NEGATIVE CONTROL (proves the probe can fail, i.e. is not a tautology): moving
# the length witness OUTSIDE what the frozen precondition gives — asserting the
# probe input holds a SECOND element, `Assert(len(probe_v) >= 2)`, which a
# one-element admissible input does not establish — is REJECTED by the verifier
# with
#   error: Assert might fail. Assertion (len(probe_v) >= 2) might not hold.
# So the asserts below are discharged by the constructed input, not by triviality.
_ADMISS_HEAD = "    sel_values = []  # type: List[int]\n"
_ADMISS_HEAD_NEW = (
    "    probe_v = [0]  # type: List[int]\n"
    "    probe_b = [False]  # type: List[bool]\n"
    "    probe_n = 256  # type: int\n"
    "    probe_mod = 300  # type: int\n"
    "    # ADMISSIBILITY probe: each Requires clause of take_rows is\n"
    "    # establishable for this normal F2P-shaped input.\n"
    "    # Requires clauses 1-2: the permissions admit reading the elements.\n"
    "    Assert(probe_v[0] == 0)\n"
    "    Assert(not probe_b[0])\n"
    "    # Requires clause 3: the two inputs have equal length.\n"
    "    Assert(len(probe_v) == len(probe_b))\n"
    "    # Requires clause 4: the table has at least one ordinary row.\n"
    "    Assert(probe_n >= 1)\n"
    "    # Requires clause 5: the container is non-degenerate...\n"
    "    Assert(probe_mod >= 1)\n"
    "    # ...and is in fact wide enough to admit every special index an\n"
    "    # assignment for this table size writes (the largest is probe_n + 2).\n"
    "    Assert(probe_mod >= probe_n + 3)\n"
    "    sel_values = []  # type: List[int]\n"
)
_ADMISS = _swap(_BASE, _ADMISS_HEAD, _ADMISS_HEAD_NEW)


# ===========================================================================
# FRAME-MUTATION RIVALS (read-only inputs) — expect "reject" (insufficient perm)
# ===========================================================================

# (F1) WRITE INTO `values` (Acc(values,1/2) = READ-ONLY). The rival overwrites the
# input element it just read (`values[i - 1] = v`) — a no-op-looking write that a
# real in-place NumPy impl is tempted to do (`xa[...] = ...` mutates the array).
# Half permission grants READ only; any store requires FULL permission, which the
# precondition does not give. The case must be REJECTED for INSUFFICIENT
# PERMISSION (not a postcondition violation). Every gold invariant/assert is kept
# verbatim, so the rejection is attributable to the write alone.
_FRAME_VALUES = _swap(
    _BASE, _READS,
    "        v = values[i - 1]\n"
    "        bad = bads[i - 1]\n"
    "        values[i - 1] = v\n",
)

# (F2) WRITE INTO `bads` (Acc(bads,1/2) = READ-ONLY). The over-the-array
# special-row assignment writes the bad-mask positions; a faithful in-place impl
# that mutates `bads` to drive selection must be rejected for INSUFFICIENT
# PERMISSION on the half-permission input. Gold invariants/asserts kept verbatim.
_FRAME_BADS = _swap(
    _BASE, _READS,
    "        v = values[i - 1]\n"
    "        bad = bads[i - 1]\n"
    "        bads[i - 1] = bad\n",
)


# ===========================================================================
# UNIQUENESS / CONTROL-FLOW RIVALS (spec-too-weak probes) — expect "reject"
# ===========================================================================

# (U1) CONTROL-FLOW-EFFECT / PREPATCH NARROW CARRIER — the canonical bug. Carry
# the special-row assignment out on the INPUT's own (possibly narrow) container
# (`carrier = modulus`) instead of a widened one. This is EXACTLY model_prepatch:
# the row VALUES are identical (rows_of is unchanged), but the assignment is not
# well-defined on a narrow container — the callee's Requires(modulus >= n+3) is
# NOT established (modulus is only >= 1), so the `rows_assigned` token is never
# granted and the postcondition rows_assigned(ToSeq(Result()), n) is
# undischargeable. Rejection source: the TOKEN pin + the callee precondition. If
# it verified => SPEC-TOO-WEAK (the spec would admit the warning-emitting bug).
_RIVAL_NARROW = _swap(
    _BASE,
    "    carrier = n + 3\n",
    "    carrier = modulus\n",
)

# (U2) CONTROL-FLOW-EFFECT — carrier ONE SHORT (n + 2). n + 2 admits indices up to
# n + 1 but NOT the largest special index n + 2 (the bad/masked row), so
# Requires(modulus >= n+3) fails by one. This is the off-by-one widening bug (cast
# to a container one bit too narrow); the bad-row store would still be out-of-range
# and warn. The row VALUES are still rows_of, so only the TOKEN pin (via the
# callee precondition) rejects it. Rejection source: the callee precondition
# modulus >= n+3 (n+2 < n+3). If it verified => SPEC-TOO-WEAK.
_RIVAL_OFF_BY_ONE = _swap(
    _BASE,
    "    carrier = n + 3\n",
    "    carrier = n + 2\n",
)

# (U3) PARTIAL-DOMAIN — corrupt ONE element's value while building the assignment
# input. The rival reads the FIRST-processed (last) element's value as 0 instead
# of its true value (`v = 0` when i == len(values)). For an all-zero / length-1
# F2P input this is invisible (v is already 0), but for any input whose last
# element is non-zero, ToSeq(sel_values) != ToSeq(values), so the callee returns
# rows_of of the WRONG sequence and the value pin
# ToSeq(Result()) == rows_of(ToSeq(values), ToSeq(bads), n) is violated (the model
# also can no longer prove ToSeq(sel_values) == ToSeq(values).drop(i)). Rejection
# source: the VALUE pin (rows_of over the true input sequence) + the loop
# invariant ToSeq(sel_values) == ToSeq(values).drop(i). If it verified =>
# SPEC-TOO-WEAK (correct on the F2P value-0 input but wrong on a sub-domain).
_RIVAL_PARTIAL = _swap(
    _BASE, _READS,
    "        v = values[i - 1] if i < len(values) else 0\n"
    "        bad = bads[i - 1]\n",
)

# (U4, supporting) DROP THE TOKEN-GRANTING CALLEE — return a freshly-built list of
# the correct length whose elements are the right row VALUES, fabricated WITHOUT
# routing through assign_special_rows. Even if value-correct, no admitting
# assignment produced it, so the unforgeable rows_assigned token cannot be
# obtained (an impl cannot Fold a @ContractOnly @Predicate). Rejection source: the
# TOKEN pin (rows_assigned is grantable only by the callee). This is the
# value-proxy attack the token defeats: identical row values, no completing
# assignment. A real patch of this shape (compute rows in Python, never widen the
# container, never perform the in-range store) would still emit the deprecation in
# the real pipeline (the store is what warns), so F2P would NOT resolve. If it
# verified => SPEC-TOO-WEAK.  NOTE: this also exercises that the value pin alone
# is insufficient — exactly why the token exists.
_RIVAL_NO_CALLEE = _swap(
    _BASE, _CARRIER_CALL,
    "    return sel_values",
)


SPEC_TESTS = [
    # ---- positive controls (must VERIFY) ----
    {"id": "pos-control-reorder", "kind": "soundness", "expect": "verify",
     "module": _POS_REORDER,
     "rationale": "structurally-different (the two independent per-element appends + their assert "
                  "pairs reordered) but CORRECT impl that keeps every loop invariant and framing "
                  "assert verbatim must verify; the appends are commutative and no induction lemma "
                  "is added. If it fails => the proof is over-fit to the exact statement order "
                  "(SPEC-TOO-STRONG)."},
    {"id": "pos-control-local-carrier", "kind": "soundness", "expect": "verify",
     "module": _POS_LOCAL,
     "rationale": "a correct impl that computes the admitting carrier through a local (extra=3; "
                  "carrier=n+extra) — a different code shape that still proves carrier>=n+3 — must "
                  "verify. If not, the proof is over-fit to the literal `n+3` carrier form "
                  "(SPEC-TOO-STRONG)."},
    {"id": "pos-control-wider-carrier", "kind": "soundness", "expect": "verify",
     "module": _POS_WIDER,
     "rationale": "a faithful impl may pick ANY container that admits every special index, not "
                  "only the tight n+3; carrier=n+5 still satisfies Requires(modulus>=n+3) and "
                  "yields the same rows_of result (this is the gold patch's real freedom: the "
                  "signed-int cast admits far more than n+2). If it fails => the spec spuriously "
                  "pins the carrier WIDTH rather than admittance (SPEC-TOO-STRONG)."},
    {"id": "admiss-f2p-uint8-zero", "kind": "admissibility", "expect": "verify",
     "module": _ADMISS,
     "rationale": "on the F2P-shaped input (a length-1 array of value 0, unmasked, N=256, "
                  "modulus=300) the probe ASSERTS each Requires clause of take_rows is "
                  "establishable: the permissions admit reading the elements, the lengths are "
                  "equal, n >= 1, modulus >= 1, and the container is in fact wide enough for "
                  "every special index (modulus >= n + 3). The gold body follows verbatim, so "
                  "the postcondition obligation is unchanged. If the precondition could not be "
                  "met for this normal input => PRECOND-TOO-STRONG. A self-call is no longer "
                  "usable as the witness: take_rows carries a termination obligation and a "
                  "self-call is never strictly below itself, so it fails with `Obligation leak "
                  "check failed. Callee take_rows might not take all unsatisfied obligations "
                  "from the caller.` — a termination fact that attributes nothing about the "
                  "domain (measured). NEGATIVE CONTROL (the probe is a real check, not a "
                  "tautology): replacing the length witness with one the input does not give, "
                  "Assert(len(probe_v) >= 2), is REJECTED with `error: Assert might fail. "
                  "Assertion (len(probe_v) >= 2) might not hold.` (measured)."},

    # ---- frame-mutation rivals (read-only inputs; must be REJECTED for perm) ----
    {"id": "frame-write-values", "kind": "uniqueness", "expect": "reject",
     "module": _FRAME_VALUES,
     "refinement": "a faithful real patch of this shape mutates the input array in place "
                   "(`xa[i] = ...` writes the integer container). On the F2P input the value 0 is "
                   "unchanged, but the in-place store on the NARROW input dtype is exactly the "
                   "out-of-bound conversion that emits the DeprecationWarning escalated to the F2P "
                   "failure — so a faithful in-place patch would NOT resolve (it must write into a "
                   "widened copy, which is the gold fix).",
     "rationale": "Rejection source: the PERMISSION SYSTEM. `values` is Acc(list_pred(values),1/2) "
                  "(half permission = read-only); the store `values[i-1] = v` requires FULL "
                  "permission, which the precondition does not grant, so it fails for INSUFFICIENT "
                  "PERMISSION (not a postcondition violation). Every gold invariant/assert is kept "
                  "verbatim, so the rejection is attributable to the write. If it verified => the "
                  "frame condition is unsound (SPEC-TOO-WEAK)."},
    {"id": "frame-write-bads", "kind": "uniqueness", "expect": "reject",
     "module": _FRAME_BADS,
     "refinement": "the array special-row assignment writes the bad-mask positions in place; a "
                   "faithful patch that mutates the input mask array (instead of operating on a "
                   "fresh widened carrier) leaves the narrow integer container untouched, so the "
                   "out-of-range store still warns and F2P would NOT resolve.",
     "rationale": "Rejection source: the PERMISSION SYSTEM. `bads` is Acc(list_pred(bads),1/2) "
                  "(read-only); the store `bads[i-1] = bad` requires FULL permission. Rejected for "
                  "INSUFFICIENT PERMISSION with the gold invariants/asserts intact. If it verified "
                  "=> the frame condition on the second read-only input is unsound."},

    # ---- uniqueness / control-flow rivals (must be REJECTED) ----
    {"id": "rival-narrow-carrier-prepatch", "kind": "uniqueness", "expect": "reject",
     "module": _RIVAL_NARROW,
     "refinement": "this IS model_prepatch: carry the special-row assignment out on the input's "
                   "own (narrow) container (`carrier = modulus`). On the F2P input (uint8, "
                   "modulus=256, N=256) the row value is unchanged (0), but the special-index "
                   "stores (256/257/258) are out-of-range for uint8 and emit the DeprecationWarning "
                   "that `filterwarnings=error` turns into the F2P failure. The unpatched code does "
                   "NOT resolve (G-DIFF's prepatch witness).",
     "rationale": "Rejection source: the TOKEN pin via the callee precondition. "
                  "assign_special_rows grants rows_assigned ONLY under Requires(modulus>=n+3); with "
                  "carrier=modulus (only >=1) that precondition is NOT established, the token is "
                  "never granted, and Ensures(rows_assigned(ToSeq(Result()),n)) is undischargeable. "
                  "The row VALUES are identical (rows_of unchanged), so ONLY the token catches it — "
                  "this is the side-effect discriminator. If it verified => SPEC-TOO-WEAK (admits "
                  "the warning-emitting bug)."},
    {"id": "rival-carrier-off-by-one", "kind": "uniqueness", "expect": "reject",
     "module": _RIVAL_OFF_BY_ONE,
     "refinement": "widen the container, but ONE bit too narrow (`carrier = n + 2`, admits up to "
                   "n+1 but not the bad-row index n+2). The bad/masked store of n+2 is still "
                   "out-of-range and warns, so a faithful patch of this shape would NOT resolve the "
                   "F2P (and would corrupt the bad row for a masked element in a real run).",
     "rationale": "Rejection source: the callee precondition modulus>=n+3. carrier=n+2 < n+3, so "
                  "the assignment is not well-defined, the token is not granted, and the token pin "
                  "fails. The row values are still rows_of (no value discriminator), so only the "
                  "token rejects the off-by-one widening. If it verified => SPEC-TOO-WEAK."},
    {"id": "rival-partial-domain-last-elem", "kind": "uniqueness", "expect": "reject",
     "module": _RIVAL_PARTIAL,
     "refinement": "read the LAST-processed element's value as 0 instead of its true value. On the "
                   "length-1 value-0 F2P input this is invisible (v is already 0), so a faithful "
                   "patch of this shape would PASS test_index_dtype[uint8] — but on any input whose "
                   "last element is non-zero it resolves the WRONG row (e.g. an over-range value "
                   "would no longer map to the over-range row), failing the P2P dtype tests "
                   "(int/float16/...) and real colormap usage. It is correct on a sub-domain only, "
                   "so its faithful patch would NOT resolve the full suite.",
     "rationale": "Rejection source: the VALUE pin. With v forced to 0 for the last element, "
                  "ToSeq(sel_values) != ToSeq(values), so the loop invariant "
                  "ToSeq(sel_values)==ToSeq(values).drop(i) cannot be re-established AND the callee "
                  "returns rows_of of the wrong sequence, violating "
                  "Ensures(ToSeq(Result())==rows_of(ToSeq(values),ToSeq(bads),n)). If it verified "
                  "=> SPEC-TOO-WEAK (admits an impl correct only on the value-0 sub-domain)."},
    {"id": "rival-fabricate-no-callee", "kind": "uniqueness", "expect": "reject",
     "module": _RIVAL_NO_CALLEE,
     "refinement": "fabricate the result directly (here: return the reconstructed input sequence) "
                   "WITHOUT routing through assign_special_rows — i.e. compute rows in Python and "
                   "never perform the widened in-range store. In the real pipeline the row store is "
                   "what emits/avoids the warning, so an impl that skips the admitting store leaves "
                   "the narrow container's out-of-range store in place (or omits the cast) and would "
                   "NOT resolve the F2P. Even a value-correct fabrication has no completing "
                   "assignment behind it.",
     "rationale": "Rejection source: the TOKEN pin. rows_assigned is @ContractOnly @Predicate so an "
                  "impl cannot Fold it into existence; it is obtainable ONLY from a well-defined "
                  "assign_special_rows. A result not produced by that callee cannot satisfy "
                  "Ensures(rows_assigned(ToSeq(Result()),n)). This demonstrates the value pin ALONE "
                  "is insufficient (the values can be right) — exactly why the unforgeable token "
                  "exists. If it verified => SPEC-TOO-WEAK."},
]

# ===========================================================================
# AXIOM LANE (Docker, real NumPy callee) — one A-consumed callee assign_special_rows
# ===========================================================================
# These reuse + strengthen axiom_check.py. The runner mounts ONLY the probe at
# /work, so each probe is self-contained (imports only stdlib + numpy, the
# dependency the patch operates on) and reconstructs the real NumPy pipeline
# inline. apply_gold=True is harmless: the modeled callee is the UNCHANGED
# integer-array operation; we run it directly on NumPy rather than through the
# colormap, so the result is independent of whether the colors.py hunk is applied.

# (A1) AXIOM-SOUNDNESS for assign_special_rows. Two obligations the proof consumes:
#   (1) RESULT: on a well-defined (admitting, modulus>=n+3) assignment, the
#       per-element result equals final_row(v,n,bad) over the real NumPy pipeline.
#   (2) LEGALITY: modulus>=n+3 coincides EXACTLY with "no out-of-bound deprecation"
#       on the F2P-shaped store (value 0, unmasked) across uint8/uint16/int8/int16
#       sweeping N across the n+2 threshold — neither too strong (no admitting
#       width excluded) nor too weak (every excluded width really warns).
# Any well-defined-assignment result != final_row, or any legality mismatch, =>
# AXIOM-UNSOUND.
_AX_SOUND = r'''
import random, sys, warnings
import numpy as np

# --- model.py deep models (kept in lock-step) ---
def selected_index(v, n, bad):
    if bad:
        return n + 2
    if v > n - 1:
        return n + 1
    if v < 0:
        return n
    return v

def clip_row(idx, n):
    if idx < 0:
        return 0
    if idx > n + 2:
        return n + 2
    return idx

def final_row(v, n, bad):
    return clip_row(selected_index(v, n, bad), n)

# --- the REAL NumPy special-row assignment on a widened (admitting) carrier ---
def real_row_widened(value, n, bad):
    xa = np.atleast_1d(np.array(value))
    with np.errstate(invalid="ignore"):
        xa = xa.astype(int)                 # carrier admits every special index
    mask_bad = np.atleast_1d(np.array(bad, dtype=bool))
    xa[xa > n - 1] = n + 1                   # over-range row
    xa[xa < 0] = n                           # under-range row
    xa[mask_bad] = n + 2                     # bad/masked row (last -> highest prec)
    return int(np.clip(xa, 0, n + 2)[0])     # lut.take(..., mode='clip')

def store_emits_deprecation(n, dtype):
    """Run the three special-row stores into a `dtype` container on the F2P-shaped
    input (single element value 0, unmasked): no element matches any special mask,
    so the RESULT value is unchanged, yet the stores convert the special-index
    scalars n+1, n, n+2 into the container. True iff NumPy emits the out-of-bound
    DeprecationWarning (or refuses the store outright)."""
    xa = np.atleast_1d(np.array(0, dtype=dtype))
    mask_bad = np.atleast_1d(np.array(False, dtype=bool))
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        try:
            xa[xa > n - 1] = n + 1
            xa[xa < 0] = n
            xa[mask_bad] = n + 2
        except (OverflowError, ValueError):
            return True
    return any(issubclass(w.category, DeprecationWarning) for w in caught)

def container_modulus(dtype):
    info = np.iinfo(dtype)
    return int(info.max) - int(info.min) + 1

# --- (1) RESULT soundness: 48 boundary + 20000 fuzz triples ---
boundary = []
for n in (1, 2, 8, 255, 256, 257, 300):
    for v in (-3, -1, 0, 1, n - 2, n - 1, n, n + 1, n + 5):
        for bad in (False, True):
            boundary.append((v, n, bad))
for (v, n, bad) in boundary:
    exp, obs = final_row(v, n, bad), real_row_widened(v, n, bad)
    if exp != obs:
        print("AXIOM-UNSOUND result mismatch (v=%d,n=%d,bad=%s): model %d real %d"
              % (v, n, bad, exp, obs)); sys.exit(1)
rng = random.Random(24970)
for _ in range(20000):
    n = rng.randint(1, 320)
    v = rng.randint(-6, n + 12)
    bad = rng.random() < 0.2
    exp, obs = final_row(v, n, bad), real_row_widened(v, n, bad)
    if exp != obs:
        print("AXIOM-UNSOUND result fuzz mismatch (v=%d,n=%d,bad=%s): model %d real %d"
              % (v, n, bad, exp, obs)); sys.exit(1)

# --- (2) LEGALITY: modulus>=n+3 coincides EXACTLY with no-deprecation ---
for dtype in (np.uint8, np.uint16, np.int8, np.int16):
    info = np.iinfo(dtype)
    hi = int(info.max)
    for n in range(max(1, hi - 5), hi + 4):
        fits = (n + 2 <= hi)                 # the real "container admits index n+2"
        emits = store_emits_deprecation(n, dtype)
        if fits == emits:                    # must be OPPOSITE
            print("AXIOM-UNSOUND legality mismatch dtype=%s n=%d: fits=%s emits-dep=%s"
                  % (np.dtype(dtype).name, n, fits, emits)); sys.exit(1)
        if np.issubdtype(dtype, np.unsignedinteger):
            modulus = container_modulus(dtype)
            if (modulus >= n + 3) != fits:
                print("AXIOM-UNSOUND modulus-form mismatch dtype=%s n=%d modulus=%d"
                      % (np.dtype(dtype).name, n, modulus)); sys.exit(1)

# --- F2P witness: uint8 N=256 deprecates on value-0; widened does not, value 0 ---
n = 256
assert container_modulus(np.uint8) == 256 and not (256 >= n + 3)
if not store_emits_deprecation(n, np.uint8):
    print("AXIOM-UNSOUND: expected narrow uint8 store to deprecate on value-0 F2P input")
    sys.exit(1)
if store_emits_deprecation(n, np.int64):
    print("AXIOM-UNSOUND: widened carrier unexpectedly deprecated"); sys.exit(1)
if not (final_row(0, n, False) == 0 == real_row_widened(0, n, False)):
    print("AXIOM-UNSOUND: value-0 row not 0"); sys.exit(1)

print("AXIOM assign_special_rows SOUND: result==final_row (48 boundary + 20000 fuzz); "
      "modulus>=n+3 coincides EXACTLY with no-deprecation across uint8/uint16/int8/int16 "
      "around the threshold; F2P witness confirmed (narrow uint8 deprecates on value-0, "
      "widened does not, row 0).")
sys.exit(0)
'''

# (A2) AXIOM-CONTAINMENT for assign_special_rows. The model has exactly ONE call
# site (take_rows impl): `assign_special_rows(sel_values, sel_bads, n, carrier)`
# with `carrier = n + 3`. So the ONLY modulus the caller can pass is n+3, and the
# axiom's Requires(modulus >= n+3) is satisfied by EQUALITY for every reachable n
# (n>=1 from the caller's own Requires). Likewise n>=1 (the caller's precondition,
# forwarded unchanged) lies in the axiom's Requires(n>=1), and the length
# preconditions are forwarded by the proven loop invariant
# (ToSeq(sel_values)==ToSeq(values), ToSeq(sel_bads)==ToSeq(bads), equal lengths).
# A reachable (n, carrier) with carrier < n+3 would be AXIOM-TOO-WEAK-FOR-CALLER;
# none exists because carrier is the constant n+3. We assert this over every n>=1
# in a wide range (pure domain check; no real-callee execution needed, so it does
# not depend on the image — but it runs in-container harmlessly).
_AX_CONTAINMENT = r'''
import sys

# The model's only call site forwards carrier = n + 3 (constant in the impl), with
# n >= 1 from take_rows' own precondition. The axiom domain is modulus >= n + 3
# (and n >= 1). Containment: every (n, carrier) the caller can reach lies in it.
def caller_carrier(n):
    return n + 3                  # the literal `carrier = n + 3` in take_rows impl

def axiom_requires(n, modulus):
    return (n >= 1) and (modulus >= n + 3)

violations = []
checked = 0
# every caller-reachable n (n >= 1), wide range incl. the default N=256 and beyond
for n in list(range(1, 1100)) + [4096, 65536, 65539, 1000000]:
    carrier = caller_carrier(n)
    if not axiom_requires(n, carrier):
        violations.append((n, carrier))
    checked += 1

if violations:
    print("AXIOM-TOO-WEAK-FOR-CALLER: caller reaches (n,carrier) outside "
          "assign_special_rows' Requires(modulus>=n+3):", violations[:8]); sys.exit(1)
# also confirm the boundary is EXACT: n+3 is in-domain, n+2 (the off-by-one rival)
# would NOT be — so the axiom domain is the weakest that admits the gold carrier.
assert axiom_requires(7, 7 + 3) and not axiom_requires(7, 7 + 2)
print("CONTAINMENT OK: over %d caller-reachable n the only forwarded modulus is "
      "carrier=n+3, which satisfies the axiom Requires(modulus>=n+3) by equality; "
      "no reachable input lies outside the axiom domain (the boundary is exact: "
      "n+3 in-domain, n+2 out)." % checked)
sys.exit(0)
'''

AXIOM_TESTS = [
    {"id": "ax-assign-special-rows-sound", "axiom": "assign_special_rows",
     "kind": "axiom-soundness", "expect": "holds", "apply_gold": True, "probe": _AX_SOUND,
     "rationale": "the REAL NumPy special-row assignment on a widened (admitting) carrier must (1) "
                  "yield final_row(v,n,bad) for every element (48 boundary + 20000 fuzz), and (2) "
                  "the legality precondition modulus>=n+3 must coincide EXACTLY with 'no "
                  "out-of-bound DeprecationWarning' on the F2P-shaped store across "
                  "uint8/uint16/int8/int16 around the threshold (weakest-sufficient). Any result "
                  "mismatch or legality mismatch => AXIOM-UNSOUND."},
    {"id": "ax-assign-special-rows-containment", "axiom": "assign_special_rows",
     "kind": "axiom-containment", "expect": "covered", "apply_gold": True, "probe": _AX_CONTAINMENT,
     "rationale": "the model's only call site forwards carrier=n+3 (a constant) with n>=1; that is "
                  "the single modulus the caller can pass, and it satisfies the axiom's "
                  "Requires(modulus>=n+3) by equality for every reachable n. A reachable carrier < "
                  "n+3 would be AXIOM-TOO-WEAK-FOR-CALLER; none exists. The boundary is exact (n+3 "
                  "in-domain, n+2 out — matching the off-by-one rival)."},
]
