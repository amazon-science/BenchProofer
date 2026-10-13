"""properties.py — G-PBT falsification battery for pytest-dev__pytest-7521 (velvet).

NOT a Velvet module; a record of adversarial cases the G-PBT gate executes.
Each SPEC case is a full ``Solution.lean`` variant that shares the FROZEN spec
byte-for-byte (region surgery: only text inside the ``-- impl-start`` /
``-- impl-end`` region, or inside the ``prove_correct`` tactic body, is changed —
both of which the consumer spec view elides, so ``markers.same_spec`` holds and
the ``prove_correct readbackStream`` obligation survives with a byte-identical
statement) and swaps in a candidate implementation; it is checked by the real
verifier. ``expect:"verify"`` passes iff (in scope AND verifies);
``expect:"reject"`` passes iff (in scope AND does NOT verify AND its refutation
``witness`` discriminates: the witness must ELABORATE against the rival and FAIL
against the frozen solution).

DEFENDED SURFACE (one contracted method over a single scanned sequence):

  readbackStream (text : List Char) return (out : List Char)
    ensures out = readback text     -- (E1) recovered content is the deep model
    ensures out = text              -- (E2) recovered content is the input VERBATIM

``readback`` is a front-recursive per-code-point fold proven == identity
(``readback_id : readback cs = cs``, ``@[grind]``), so E1 and E2 are NOT
independent — they are logically equivalent (``out = readback text ⟺ out =
text``). The single behavioural constraint is therefore: the recovered sequence
reproduces the input sequence code point for code point — nothing rewritten,
inserted, dropped, or merged. Every reject rival is refuted against BOTH clauses
at once (the extracted tester checks the whole postcondition). The ``axioms``
region is empty; the post-image is GROUNDED in the method's own input (the
identity on the argument, no opaque answer key), so there is no *wrong* echo a
rival can return — the cheapest honest impl is ``return text`` (a positive
control below).

GROUNDED-ORACLE NOTE. Because the post-image is the identity on the input
carrier, the uniqueness lane cannot be "echo a wrong constant" (any constant or
mangled echo fails E2). It is instead the PARTIAL-DOMAIN attack: an impl that
agrees with the identity on a majority sub-domain but diverges on the
discriminating sub-domain — every input bearing a carriage return (U+000D, 13),
which is exactly the F2P sub-domain (``print("test", end="\\r")`` /
``print("test", end="\\r\\n")`` must read back ending in the written newline). A
carriage-return-losing read-back reproduces the input on every CR-free string yet
folds ``\\r`` to ``\\n`` on the failing tests.

The sole INPUT BINDER is ``text : List Char``. The reject witnesses vary it
along the axes the rivals abuse: a carriage return at a LEADING/interior position,
a carriage return at the TRAILING position, and a CR-free input whose LENGTH and
element positions a truncation rival corrupts.

ADVERSARIAL READ of the nagini classes on this carrier:
  * FRAME / PERMISSION-MUTATION — VACUOUS. The sibling carries this as a
    MANDATORY rival (a store into ``written`` held at half permission, rewriting
    a CR away in place so the identity holds vacuously). Lean and Velvet are
    referentially transparent: ``text`` is an immutable value, this bundle
    declares NO ``mut`` binder over any input (only the local accumulator
    ``result`` and index ``i`` are ``mut``), there is no heap and no aliasing —
    so there is no read-only input to overwrite and no permission system to trip.
    Not fabricated (per the porting map: vacuous here).
  * DIVERGENCE / NON-TERMINATION - the class is CLOSED BY THE SEMANTICS here,
    and a diverging rival is REJECTED rather than admitted. This bundle sets
    ``loom.semantics.termination "total"`` AND carries
    ``open TotalCorrectness``, and the ``open`` is the line that actually
    selects the semantics: both namespaces define
    ``WPGen.forWithInvariantLoop``, the later ``open`` wins, and the
    ``PartialCorrectness`` version takes a loop measure and DISCARDS it. So the
    two lines have to move together, and they do here. Under the total scope a
    postcondition is claimed of ALL runs, not only of terminating ones, and the
    verifier emits a descent obligation ``measure b' < measure b`` for every
    loop in the impl (1 loop here, measure ``i``). A rival that loops without a
    measure is refused outright (``Decreasing annotations are required in total
    correctness semantics``), and a rival that supplies a CONSTANT measure to
    dodge that is refused on the measure's own goal (``case «decreasing_1:
    spin» ... ⊢ spin < spin``), re-measured on this bundle with a real build.
    Divergence therefore does not discharge the ``ensures`` clauses vacuously.
    It is still not shipped as a G-PBT reject case, and the reason is the
    witness contract rather than a spec weakness. A reject case must carry a
    witness that ELABORATES against the rival, and the rival's module does not
    compile at all: the descent obligation fails at the ``method`` itself,
    ahead of any appended tester. Measured through the gate's own
    ``_check_witness``, even ``example : True := trivial`` comes back
    ``witness-unproven`` on this rival, which is an INCONCLUSIVE outcome and
    would fail the whole battery rather than pass a case. That is the right
    behavior: a diverging impl has no output at any input, so there is no value
    for a witness to disagree with, and its rejection is a judgement of the
    termination obligation rather than a postcondition violation at a point.
    Recorded as REJECTED-BY-SPEC and not expressible as a witnessed case, which
    is neither a spec hole nor a battery gap.
  * PARTIAL-DOMAIN / VALUE — APPLIES; the headline discriminator. A rival that
    folds carriage returns (whole-sequence or trailing-only) is right on every
    CR-free string and wrong on the F2P sub-domain; a truncation rival is right
    only on a length sub-domain. Each is refuted by the identity postcondition.
  * UNGROUNDED-ORACLE ECHO — N/A. ``readback`` is a concrete ``def`` proven ==
    identity over the method's own input (empty ``axioms`` region); the cheapest
    correct impl evaluates the identity, covered honestly by the positive
    controls.
  * CONTROL-FLOW-EFFECT — N/A. ``readbackStream`` is a pure value transform
    (``List Char -> List Char``); there is no raise / return-code / side-effect
    channel invisible to the value abstraction, so a capability-token rival adds
    nothing (matches the sibling's stated N/A).

WITNESS PLACEMENT. The frozen impl is a backward ``while`` loop whose extracted
tester does NOT reduce under ``decide`` (the fixpoint stays stuck — measured: the
gold witness build fails with ``decide`` stuck on ``readbackStreamTester [...]``),
so each reject rival is a straight-line loop-free CLOSED FORM whose extracted
tester DOES reduce to a literal. Each reject rival therefore carries a
machine-checked refutation ``witness`` — a Velvet tester statement
``readbackStreamTester <text> = false`` at ONE concrete input, checked in a file
whose ``prove_correct`` block is stripped so no tactic script can mask the
verdict. Both halves were checked out-of-band with ``scripts/lean_verify.sh``:
every witness ELABORATES against its loop-free rival (the tester ``decide``s to
``false`` — the rival's output violates the postcondition there) and FAILS
against the frozen loop-solution (whose extracted fixpoint stays stuck under
``decide``), so each rejection is a genuine spec refutation and not mechanical
tactic breakage. No witness binds a hypothesis (the carrier is fully transparent
— ``Char`` literals ``decide``), so there is no joint-satisfiability obligation.

AXIOM lane: EMPTY here (this gate ignores ``AXIOM_TESTS`` regardless). The
sibling's axiom lane validates the A-reference deep model (``cr_folded`` / the
verbatim read-back) against the real platform stream reader; ``meta.json``
records that as G-AX (already passed), so it is DROPPED from this manifest.
"""
from pathlib import Path

INSTANCE = "pytest-dev__pytest-7521"
BACKEND = "velvet"

_BASE = (Path(__file__).parent / "Solution.lean").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# ---- impl-region anchor (the WHOLE `do` body; lies wholly inside the single
# ---- impl region and is unique in Solution.lean). ---------------------------
_IMPL = (
    "    -- impl-start\n"
    "    let mut result : List Char := []\n"
    "    let mut i := text.length\n"
    "    while i > 0\n"
    "      invariant 0 ≤ i ∧ i ≤ text.length\n"
    "      invariant result = readback (text.drop i)\n"
    "      done_with i = 0\n"
    "      decreasing i\n"
    "    do\n"
    "      let c := text[i - 1]!\n"
    "      result := c :: result\n"
    "      i := i - 1\n"
    "    return result\n"
    "    -- impl-end"
)

# ---- proof-body anchor. A `prove_correct` tactic body is elided from the
# ---- consumer spec view, so a variant may retune it without touching the spec
# ---- or dropping the obligation. Unique in the file.
_PROOF = (
    "prove_correct readbackStream by\n"
    "  loom_solve\n"
    "  rw [readback_drop_step text i (by omega) (by omega)]\n"
    "  simp_all"
)

# The reshaped/loop-free variants own no backward loop index `i` in the frozen
# form, so the frozen tactic script (which names `i` and rewrites via
# `readback_drop_step`) does not apply. For loop-free soundness positives we
# retune to the bare solver; for reject rivals we also reduce to the bare solver
# (they must NOT verify regardless — the proof body is elided from the spec
# view, and the rejection is attributed to the postcondition by the witness).
_SOLVE = "prove_correct readbackStream by\n  loom_solve"

assert _BASE.count(_IMPL) == 1, "method impl region drifted from expected text"
assert _BASE.count(_PROOF) == 1, "proof region drifted from expected text"


def _impl(new_impl, proof=_SOLVE):
    """Reshape the whole impl body AND retune the tactic script."""
    return _swap(_swap(_BASE, _IMPL, new_impl), _PROOF, proof)


def _rival(expr):
    """Solution.lean whose impl body is a single loop-free `return (<expr>)`,
    with the tactic script reduced to the bare solver."""
    return _impl(
        "    -- impl-start\n"
        f"    return ({expr})\n"
        "    -- impl-end")


# ---- witness preamble. The spec is a `method` CONTRACT, not a bare predicate,
# ---- so a witness reaches it through Velvet's own tester machinery:
# ---- `readbackStreamTester text = false` says the extracted program's result
# ---- violates the method's postcondition at that concrete input. Checked in a
# ---- file whose `prove_correct` block is stripped, so no tactic script can mask
# ---- the verdict. `text : List Char` is fully transparent (`Char` literals
# ---- decide), so each witness closes by `decide`.
def _tester(body):
    return ("extract_program_for readbackStream\n"
            "prove_precondition_decidable_for readbackStream\n"
            "prove_postcondition_decidable_for readbackStream\n"
            "derive_tester_for readbackStream\n\n" + body)


SPEC_TESTS = [
    # =====================================================================
    # POSITIVE CONTROL (soundness) — the cheapest HONEST impl, which MUST verify
    # (else SPEC-TOO-STRONG). The post-image is the identity on the input
    # (`readback text = text`), GROUNDED in the argument with no opaque answer
    # key, so `return text` is a correct fully-grounded implementation. The loop
    # is gone, so the frozen proof's loop reasoning is unneeded and the residual
    # goals close under the bare `loom_solve` (`readback_id` is `@[grind]`).
    # =====================================================================
    {
        "id": "pos-control-direct-identity",
        "kind": "soundness",
        "expect": "verify",
        "module": _rival("text"),
        "rationale": "the post-image is the identity on the input carrier "
                     "(`out = readback text = text`), GROUNDED in the argument "
                     "(no opaque answer key), so `return text` is the honest "
                     "cheapest CORRECT impl. It MUST verify — the clauses are "
                     "literally `out = readback text` and `out = text` — else the "
                     "postcondition is SPEC-TOO-STRONG. Also shows the spec is not "
                     "echo-vulnerable: any wrong constant/mangled echo fails E2.",
    },
    {
        "id": "pos-control-backward-reshape",
        "kind": "soundness",
        "expect": "verify",
        # Structurally different but CORRECT: keep the frozen backward loop and
        # every invariant byte-identical, only bind `j = i - 1` and read/decrement
        # through it. Observationally identical; the frozen loop proof closes it
        # unchanged (the drop-step still fires on `i`).
        "module": _impl(
            "    -- impl-start\n"
            "    let mut result : List Char := []\n"
            "    let mut i := text.length\n"
            "    while i > 0\n"
            "      invariant 0 ≤ i ∧ i ≤ text.length\n"
            "      invariant result = readback (text.drop i)\n"
            "      done_with i = 0\n"
            "      decreasing i\n"
            "    do\n"
            "      let j := i - 1\n"
            "      let c := text[j]!\n"
            "      result := c :: result\n"
            "      i := j\n"
            "    return result\n"
            "    -- impl-end",
            proof=_PROOF),
        "rationale": "local-variable reshape of the gold backward loop (bind "
                     "j=i-1, read and decrement through it), keeping every loop "
                     "invariant byte-identical. Semantically identical; the frozen "
                     "loop proof (`readback_drop_step` on `i`) closes it unchanged. "
                     "A faithful reshape MUST verify, else the postcondition is "
                     "over-fit to one textual proof FORM => SPEC-TOO-STRONG.",
    },
    {
        "id": "pos-control-forward-append",
        "kind": "soundness",
        "expect": "verify",
        # A genuinely different shape: the gold walks BACKWARD and front-prepends;
        # this walks FORWARD and appends, with the dual invariant
        # `result = text.take i`. The residual goals close under `simp_all`
        # (List.take theory), so no new lemma is introduced.
        "module": _impl(
            "    -- impl-start\n"
            "    let mut result : List Char := []\n"
            "    let mut i := 0\n"
            "    while i < text.length\n"
            "      invariant 0 ≤ i ∧ i ≤ text.length\n"
            "      invariant result = text.take i\n"
            "      done_with i = text.length\n"
            "      decreasing text.length - i\n"
            "    do\n"
            "      let c := text[i]!\n"
            "      result := result ++ [c]\n"
            "      i := i + 1\n"
            "    return result\n"
            "    -- impl-end",
            proof="prove_correct readbackStream by\n  loom_solve\n  all_goals simp_all"),
        "rationale": "a genuinely different shape: forward walk + append (gold "
                     "walks backward + front-prepends), with the dual invariant "
                     "`result = text.take i`. `take` is built-in List theory, so "
                     "the residual goals close under the bare `simp_all` (no new "
                     "lemma). A correct verbatim copy must verify; else the spec is "
                     "over-fit to loop DIRECTION => SPEC-TOO-STRONG.",
    },

    # =====================================================================
    # ADMISSIBILITY — the sibling's probe is a self-call establishing the
    # `Requires` (half-permission) precondition on a fresh F2P-shaped CR input.
    # There is NO `require` clause here (empty pre-conditions region), so that
    # precondition-admits probe is VACUOUS. RE-AIMED at the residual total-domain
    # risk: that the post-image is UNSATISFIABLE / degenerate at the interesting
    # point. This case discharges an in-region `assert` pinning the deep model at
    # the F2P-shaped CR-bearing input "test\r" (readback reproduces it verbatim,
    # INCLUDING the trailing carriage return), so the post-image is non-degenerate
    # exactly on the discriminating sub-domain. The impl is kept verbatim so the
    # method's own obligation still discharges; the assert is live (a false claim
    # leaves an unsolved goal — checked during authoring, closes by `decide`).
    # =====================================================================
    {
        "id": "admiss-f2p-cr-nondegenerate",
        "kind": "admissibility",
        "expect": "verify",
        "module": _impl(
            "    -- impl-start\n"
            "    assert (with_name_prefix `admiss\n"
            "      (readback ['t', 'e', 's', 't', '\\r'] = ['t', 'e', 's', 't', '\\r']))\n"
            "    let mut result : List Char := []\n"
            "    let mut i := text.length\n"
            "    while i > 0\n"
            "      invariant 0 ≤ i ∧ i ≤ text.length\n"
            "      invariant result = readback (text.drop i)\n"
            "      done_with i = 0\n"
            "      decreasing i\n"
            "    do\n"
            "      let c := text[i - 1]!\n"
            "      result := c :: result\n"
            "      i := i - 1\n"
            "    return result\n"
            "    -- impl-end",
            proof=(
                "prove_correct readbackStream by\n"
                "  loom_solve\n"
                "  all_goals first\n"
                "    | decide\n"
                "    | (rw [readback_drop_step text i (by omega) (by omega)]\n"
                "       simp_all)")),
        "rationale": "there is NO `require` clause, so the sibling's "
                     "precondition-admits probe is vacuous. Re-aimed at the "
                     "residual total-domain risk: the post-image is satisfiable AND "
                     "non-degenerate on the discriminating sub-domain. The in-region "
                     "assert pins the deep model at the F2P-shaped CR input "
                     "\"test\\r\" (recovered VERBATIM, trailing carriage return kept) "
                     "and must discharge (else the obligation is unsatisfiable / "
                     "degenerate there); the impl is kept verbatim so the method's "
                     "own `ensures` still discharges.",
    },

    # =====================================================================
    # UNIQUENESS / SPEC-TOO-WEAK rivals — wrong impls sharing the frozen spec
    # that MUST be rejected, each a loop-free closed form with a machine-checked
    # refutation witness at a concrete input and the refinement argument for why
    # its faithful real counterpart would NOT resolve the failing test.
    # =====================================================================

    # ---- IDENTITY clause: whole-sequence carriage-return fold (the regression) --
    {
        "id": "weak-cr-fold",
        "kind": "uniqueness",
        "expect": "reject",
        # The regression: fold every carriage return (13) -> line feed (10) on
        # read-back, else copy verbatim. Correct on every CR-free input, wrong on
        # every '\r'-bearing input (the F2P sub-domain).
        "module": _rival(
            "text.map (fun c => if c = '\\r' then '\\n' else c)"),
        "refinement": "this is EXACTLY the reported regression: the default "
                      "platform read-back policy rewrites every carriage return to "
                      "a line feed. A faithful patch that leaves that default reader "
                      "in place produces this fold and FAILS the F2P "
                      "test_cafd_preserves_newlines[\\r] and [\\r\\n] "
                      "(out.endswith('\\r') / endswith('\\r\\n') are false once the "
                      "CR is folded to '\\n') — a verify-not-resolve break.",
        "rationale": "REJECT from the identity postcondition (out = text, "
                     "equivalently out = readback text): the fold puts 10 where the "
                     "input holds 13, so on any '\\r'-bearing input out != text. "
                     "Verifying would be SPEC-TOO-WEAK (the spec would not sense "
                     "carriage-return loss). Refuted at a LEADING carriage return "
                     "['\\r','a'] — the interior/leading sub-domain where the "
                     "trailing-only near-miss still agrees with gold.",
        "witness": _tester(
            "example : readbackStreamTester ['\\r', 'a'] = false := by\n"
            "  decide\n"),
    },

    # ---- IDENTITY clause: trailing-lone-CR fold (the sharper sub-domain) ----
    {
        "id": "weak-trailing-cr-fold",
        "kind": "uniqueness",
        "expect": "reject",
        # Fold ONLY a trailing lone carriage return -> line feed; every other
        # position copies verbatim. Correct on every input NOT ending in '\r'
        # (including "test\r\n", whose last char is '\n'), wrong on every input
        # ending in a lone '\r'.
        "module": _rival(
            "if text.getLast? = some '\\r' then text.dropLast ++ ['\\n'] else text"),
        "refinement": "folds only a TRAILING lone carriage return -> line feed — "
                      "exactly the borgbackup witness '  0%\\r' and the F2P "
                      "`print(\"test\", end=\"\\r\")` => out == 'test\\r'. A faithful "
                      "patch losing only the trailing CR still FAILS the F2P "
                      "test_cafd_preserves_newlines[\\r] (out.endswith('\\r') is "
                      "false) — verify-not-resolve. Sharper than weak-cr-fold: it is "
                      "correct on \"test\\r\\n\" (last char '\\n') yet still wrong on "
                      "\"test\\r\".",
        "rationale": "REJECT from the identity postcondition: on an input ending in "
                     "a lone '\\r' the last recovered code point is 10, not 13, so "
                     "out != text. Verifying would be SPEC-TOO-WEAK (the spec would "
                     "miss carriage-return loss at the sequence BOUNDARY). Refuted at "
                     "a TRAILING carriage return ['a','\\r'] — the distinct boundary "
                     "sub-domain the whole-sequence witness does not probe.",
        "witness": _tester(
            "example : readbackStreamTester ['a', '\\r'] = false := by\n"
            "  decide\n"),
    },

    # ---- IDENTITY clause: drop the first code point (off-by-one truncation) ----
    {
        "id": "weak-drop-first",
        "kind": "uniqueness",
        "expect": "reject",
        # Return the TAIL, dropping the first code point unconditionally (the
        # sibling's backward loop stopping at i==1 instead of i==0). Correct only
        # on the empty input; for any non-empty input the read-back is missing its
        # first code point and is one shorter.
        "module": _rival("text.tail"),
        "refinement": "off-by-one truncation dropping the first captured code "
                      "point: the read-back is missing its FIRST character and one "
                      "shorter. A faithful patch dropping the first captured code "
                      "point fails the broader capture round-trip the F2P/P2P "
                      "exercise (the recovered text must equal what was written) — "
                      "verify-not-resolve. Supporting near-miss with a real "
                      "refinement.",
        "rationale": "REJECT from the identity postcondition: `text.tail` = "
                     "`text.drop 1` differs from `text` (length one short) on every "
                     "non-empty input, so out != text. Correct only on []. Refuted at "
                     "a CR-FREE length-2 input ['a','b'] — the sub-domain no fold "
                     "witness exercises (no carriage return present), so this pins "
                     "the spec's dependence on LENGTH / position, not just on CR.",
        "witness": _tester(
            "example : readbackStreamTester ['a', 'b'] = false := by\n"
            "  decide\n"),
    },
]


# ---------------------------------------------------------------------------
# Nagini -> velvet accounting. The sibling battery has 7 SPEC cases (2 soundness
# positives, 1 admissibility, 4 uniqueness rivals) plus a 1-case AXIOM lane. This
# bundle models the SAME purely-functional core — the read-back of buffered
# stream content, which must reproduce the buffered code points VERBATIM — over a
# `List Char` carrier instead of the sibling's permission-bearing `List[int]` of
# code points. The value surface (verbatim identity read-back, carriage returns
# preserved) carries across; the permission surface does not exist here.
#
#   sibling case                 -> here                              disposition
#   --------------------------------------------------------------------------
#   pos-control-reshape          -> pos-control-backward-reshape      PORTED
#   pos-control-forward-append   -> pos-control-forward-append        PORTED
#   admiss-selfcall              -> admiss-f2p-cr-nondegenerate        RE-AIMED
#   frame-mutate-written         -> (none)                            VACUOUS
#   weak-cr-fold                 -> weak-cr-fold                       PORTED
#   weak-trailing-cr-fold        -> weak-trailing-cr-fold             PORTED
#   weak-drop-last               -> weak-drop-first                    PORTED
#   AXIOM_TESTS (1)              -> (none)                            DROPPED (G-AX)
#
# Plus one ADDED honest positive (pos-control-direct-identity, `return text`):
#   the cheapest grounded impl, which also demonstrates the post-image is not
#   echo-vulnerable. Not in the sibling (whose grounded oracle needed an in-region
#   ghost loop); trivial here because the post-image is the identity.
#
# 5 ported, 1 re-aimed, 1 added, 1 vacuous, 1 dropped = 7 SPEC cases (3 soundness,
# 1 admissibility, 3 uniqueness).
#
# PORTED (2 positive controls). pos-control-reshape ports 1:1 as a
#   local-variable reshape of the backward loop (bind j=i-1), invariants
#   byte-identical, closed by the frozen loop proof. pos-control-forward-append
#   is a genuinely different shape (forward walk + append, dual invariant
#   result = text.take i) closed by the bare `simp_all` (List.take theory, no new
#   lemma). Both verified to build (exit 0).
# RE-AIMED (admissibility). The sibling establishes the half-permission
#   precondition on a fresh CR input. There is NO `require` clause here, so that
#   probe is vacuous. Re-aimed at the residual total-domain risk: the post-image
#   is non-degenerate at the F2P CR input "test\r" via an in-region assert
#   (readback recovers it verbatim, trailing CR kept), impl kept verbatim, assert
#   discharged by `decide`. Verified to build.
# PORTED (3 rivals). weak-cr-fold (the whole-sequence regression),
#   weak-trailing-cr-fold (trailing lone CR only), weak-drop-first (off-by-one
#   truncation). Each refinement argument carries over (a faithful counterpart
#   with that defect still loses a CR / drops a code point on the failing test, so
#   it would NOT resolve). Each carries a machine-checked witness that ELABORATES
#   against the loop-free rival and FAILS against the frozen loop-solution (two
#   real builds per case, run during authoring).
# VACUOUS (frame-mutate-written). The sibling carries this MANDATORY because
#   `written` is held at half permission and a store into it is rejected for
#   insufficient permission. This backend is referentially transparent and
#   declares no `mut` binder over any input — `text` is an immutable value with
#   no heap footprint — so there is no read-only input to overwrite and no
#   permission system to trip. Not fabricated (porting map: vacuous here). The
#   divergence class is ALSO vacuous here: this is a `total`-termination bundle
#   with a discharged `decreasing` measure, so a non-terminating impl cannot be
#   written (NOT the `partial` known-hole disposition).
# DROPPED (AXIOM_TESTS). The sibling's axiom lane validates its A-reference deep
#   model (the verbatim read-back / cr_folded) against the real platform stream
#   reader. meta.json records that as G-AX (deep_model_references: readback,
#   status pass), and this gate ignores AXIOM_TESTS regardless.
#
# BINDER / CLAUSE COVERAGE. The obligation has ONE input binder,
#   `text : List Char`, and two ensures clauses that are NOT independent:
#   `readback` is proven == identity (readback_id), so
#   `out = readback text ⟺ out = text`. Every rival attacks the single behavioural
#   constraint (verbatim identity) against BOTH clauses at once (the extracted
#   tester checks the whole postcondition). The three reject witnesses probe three
#   DISTINCT input points (pts = 3):
#     ['\r','a']   — LEADING carriage return       (weak-cr-fold)
#     ['a','\r']   — TRAILING carriage return       (weak-trailing-cr-fold)
#     ['a','b']    — CR-FREE length-2 (length/pos)  (weak-drop-first)
#   The binder `text` is varied along the axes the spec depends on: carriage
#   return present at a leading/interior position, at the trailing position, and
#   absent (length/element-position). No two rivals share an input, and the
#   CR-free witness pins the spec's dependence on length and position, not just on
#   carriage-return handling.
# WITNESS DISCRIMINATION (verified during authoring with two real builds per
#   reject case, scripts/lean_verify.sh): each witness ELABORATES against its
#   loop-free rival (the extracted tester `decide`s to false — the rival's output
#   violates the postcondition at the probed input) and FAILS against the frozen
#   loop-solution (whose extracted fixpoint stays stuck under `decide`). No witness
#   binds a hypothesis (the carrier is fully transparent — `Char` literals
#   decide), so there is no joint-satisfiability obligation. No
#   `sorry`/`admit`/`native_decide`/`axiom` appears in any witness.
AXIOM_TESTS = []
