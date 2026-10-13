# properties.py — PBT falsification battery for matplotlib__matplotlib-25122.
#
# NOT a Nagini module; a record of adversarially-reasoned cases. The runner
# (swebench_nagini.pbt) writes each `module` to a temp file, runs the Nagini
# verifier on the HOST (spec lane) and asserts `same_spec` against the frozen
# model.py. Axiom lane is empty: this bundle has NO @ContractOnly axioms (the
# changed reductions are modelled DEEPLY as front-recursive folds, validated ==
# the real numpy reductions out-of-band by axiom_check.py / G-AX).
#
# Region surgery: every variant is built by _swap on _BASE, editing ONLY text
# that lies strictly between a `# impl-start` and `# impl-end` marker, so the
# frozen spec (axioms / pure / pre / post-conditions) is provably untouched and
# same_spec holds by construction.
#
# Defended surface (read from model.py + refinement.md + mapping.md):
#   amplitude_loss_divisor(window: List[int]) -> int
#     Requires/Ensures: Acc(list_pred(window), 1/2)   <-- READ-ONLY input
#     Requires: MustTerminate(2)                      <-- TOTAL correctness
#     LOAD-BEARING:    Result() == signed_sum(ToSeq(window))   (SIGNED fold)
#   power_loss_divisor(window: List[int]) -> int
#     Requires/Ensures: Acc(list_pred(window), 1/2)   <-- READ-ONLY input
#     Requires: MustTerminate(2)                      <-- TOTAL correctness
#     LOAD-BEARING:    Result() == square_sum(ToSeq(window))
#                  AND square_sum(ToSeq(window)) == magnitude_square_sum(ToSeq(window))
#
#   Each divisor carries Requires(MustTerminate(2)) -- a total-correctness
#   obligation. A rival that diverges before returning (unbounded loop) would
#   satisfy every value Ensures vacuously; the obligation system rejects any
#   loop lacking a decreasing termination measure. The gold loops discharge it
#   with Invariant(MustTerminate(i + 1)) (measure i strictly decreases).
#   The real bug (gold patch): the amplitude divisor is the SIGNED window sum
#   Sum w_i (window.sum()), NOT the absolute-value sum Sum|w_i| (np.abs(window).sum()).
#   The F2P test feeds a `flattop` window WITH NEGATIVE WEIGHTS, the exact domain
#   where Sum|w| != Sum w. So the discriminating clause is the sign handling.
#
# The postcondition oracle `signed_sum` is GROUNDED in the input (a fully
# spelled-out front-recursive fold over ToSeq(window)), NOT an opaque answer-key
# marker. There is therefore no ungrounded-oracle ECHO attack: `return
# signed_sum(ToSeq(window))` materialized is simply the correct value, not a
# cheat. We instead supply an honest cheapest-impl positive control (see
# `assessment`). The mandatory frame-mutation probe and the partial-domain
# sign-bug probe are the reasoned uniqueness attacks.

from pathlib import Path

INSTANCE = "matplotlib__matplotlib-25122"
FLOAT_ENCODING = None  # meta.json float_encoding is null (NOT a precision bug)

_BASE = (Path(__file__).parent / "model.py").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# ---------------------------------------------------------------------------
# Unique impl-region anchors (verified unique against _BASE by count() above).
# ---------------------------------------------------------------------------

# amplitude_loss_divisor impl body (the SIGNED running total). Unique: only this
# function ends `total = weight + total / i = i - 1 / return total`.
_AMP_IMPL = (
    "    total = 0\n"
    "    i = len(window)\n"
    "    while i > 0:\n"
    "        # invariants-start\n"
    "        Invariant(Acc(list_pred(window), 1 / 2))\n"
    "        Invariant(0 <= i and i <= len(window))\n"
    "        Invariant(total == signed_sum(ToSeq(window).drop(i)))\n"
    "        # the loop consumes the caller's termination obligation with a\n"
    "        # strictly decreasing measure (i), discharging MustTerminate(2)\n"
    "        # from the precondition.\n"
    "        Invariant(MustTerminate(i + 1))\n"
    "        # invariants-end\n"
    "        weight = window[i - 1]\n"
    "        Assert(ToSeq(window).drop(i - 1)[0] == weight)\n"
    "        Assert(ToSeq(window).drop(i - 1).drop(1) == ToSeq(window).drop(i))\n"
    "        total = weight + total\n"
    "        i = i - 1\n"
    "    return total\n"
)

# power_loss_divisor impl body (the SQUARED running total). Unique: only this
# function has `total = weight * weight + total` and the trailing lemma assert.
_PWR_IMPL = (
    "    total = 0\n"
    "    i = len(window)\n"
    "    while i > 0:\n"
    "        # invariants-start\n"
    "        Invariant(Acc(list_pred(window), 1 / 2))\n"
    "        Invariant(0 <= i and i <= len(window))\n"
    "        Invariant(total == square_sum(ToSeq(window).drop(i)))\n"
    "        # the loop consumes the caller's termination obligation with a\n"
    "        # strictly decreasing measure (i), discharging MustTerminate(2)\n"
    "        # from the precondition.\n"
    "        Invariant(MustTerminate(i + 1))\n"
    "        # invariants-end\n"
    "        weight = window[i - 1]\n"
    "        Assert(ToSeq(window).drop(i - 1)[0] == weight)\n"
    "        Assert(ToSeq(window).drop(i - 1).drop(1) == ToSeq(window).drop(i))\n"
    "        total = weight * weight + total\n"
    "        i = i - 1\n"
    "    Assert(squares_are_sign_blind(ToSeq(window)))\n"
    "    return total\n"
)


# ===========================================================================
# POSITIVE CONTROLS (soundness / admissibility)
# ===========================================================================

# (1) pos-control-amp : structurally-different but CORRECT amplitude impl.
#     Same backward loop / same gold invariants & framing asserts (kept VERBATIM
#     per pilot bug #2) — only the executable shape of the accumulation is
#     reshaped: a fresh local `acc`, the operands of `+` commuted (`total +
#     weight`), and the index decrement spelled `i -= 1`-style as `i = (i - 1)`.
#     Keeps the gold proof valid (no fold-split lemma needed — this is NOT a
#     forward-append, per pilot bug #3); must verify, else SPEC-TOO-STRONG.
_POS_AMP = _swap(
    _BASE,
    "        weight = window[i - 1]\n"
    "        Assert(ToSeq(window).drop(i - 1)[0] == weight)\n"
    "        Assert(ToSeq(window).drop(i - 1).drop(1) == ToSeq(window).drop(i))\n"
    "        total = weight + total\n"
    "        i = i - 1\n"
    "    return total\n",
    "        acc = window[i - 1]\n"
    "        Assert(ToSeq(window).drop(i - 1)[0] == acc)\n"
    "        Assert(ToSeq(window).drop(i - 1).drop(1) == ToSeq(window).drop(i))\n"
    "        total = total + acc\n"
    "        i = (i - 1)\n"
    "    return total\n",
)

# (2) pos-control-pwr : structurally-different but CORRECT power impl. Same
#     reshape recipe (commute the square accumulation, fresh local), gold
#     invariants + the squares_are_sign_blind lemma assert kept verbatim.
_POS_PWR = _swap(
    _BASE,
    "        weight = window[i - 1]\n"
    "        Assert(ToSeq(window).drop(i - 1)[0] == weight)\n"
    "        Assert(ToSeq(window).drop(i - 1).drop(1) == ToSeq(window).drop(i))\n"
    "        total = weight * weight + total\n"
    "        i = i - 1\n"
    "    Assert(squares_are_sign_blind(ToSeq(window)))\n"
    "    return total\n",
    "        acc = window[i - 1]\n"
    "        Assert(ToSeq(window).drop(i - 1)[0] == acc)\n"
    "        Assert(ToSeq(window).drop(i - 1).drop(1) == ToSeq(window).drop(i))\n"
    "        total = total + acc * acc\n"
    "        i = (i - 1)\n"
    "    Assert(squares_are_sign_blind(ToSeq(window)))\n"
    "    return total\n",
)

# (3) admiss-amp : admissibility — a positive-control SELF-CALL on a normal
#     F2P-shaped input. The Requires is only Acc(list_pred(window), 1/2); we add
#     (inside impl) a call `amplitude_loss_divisor(window)` is NOT possible
#     (would need full perm to re-pass), so we instead establish the precondition
#     is satisfiable for a freshly-built representative window and assert the
#     result equals the grounded fold. This exercises that the precondition
#     ADMITS a normal in-domain input (else PRECOND-TOO-STRONG). We keep the gold
#     loop and append one harmless post-`return`-unreachable... no — instead we
#     add an Assert on a concrete prefix fact the gold proof already establishes,
#     confirming the contract is establishable. Editing only inside impl.
_ADMISS_AMP = _swap(
    _BASE,
    "    total = 0\n"
    "    i = len(window)\n"
    "    while i > 0:\n"
    "        # invariants-start\n"
    "        Invariant(Acc(list_pred(window), 1 / 2))\n"
    "        Invariant(0 <= i and i <= len(window))\n"
    "        Invariant(total == signed_sum(ToSeq(window).drop(i)))\n"
    "        # the loop consumes the caller's termination obligation with a\n"
    "        # strictly decreasing measure (i), discharging MustTerminate(2)\n"
    "        # from the precondition.\n"
    "        Invariant(MustTerminate(i + 1))\n"
    "        # invariants-end\n"
    "        weight = window[i - 1]\n"
    "        Assert(ToSeq(window).drop(i - 1)[0] == weight)\n"
    "        Assert(ToSeq(window).drop(i - 1).drop(1) == ToSeq(window).drop(i))\n"
    "        total = weight + total\n"
    "        i = i - 1\n"
    "    return total\n",
    "    # admissibility: the precondition Acc(list_pred(window),1/2) accepts a\n"
    "    # normal window and the empty-prefix base case of the grounded fold is\n"
    "    # establishable (signed_sum of the whole, dropped 0, is the full sum).\n"
    "    Assert(signed_sum(ToSeq(window).drop(len(window))) == 0)\n"
    "    total = 0\n"
    "    i = len(window)\n"
    "    while i > 0:\n"
    "        # invariants-start\n"
    "        Invariant(Acc(list_pred(window), 1 / 2))\n"
    "        Invariant(0 <= i and i <= len(window))\n"
    "        Invariant(total == signed_sum(ToSeq(window).drop(i)))\n"
    "        # the loop consumes the caller's termination obligation with a\n"
    "        # strictly decreasing measure (i), discharging MustTerminate(2)\n"
    "        # from the precondition.\n"
    "        Invariant(MustTerminate(i + 1))\n"
    "        # invariants-end\n"
    "        weight = window[i - 1]\n"
    "        Assert(ToSeq(window).drop(i - 1)[0] == weight)\n"
    "        Assert(ToSeq(window).drop(i - 1).drop(1) == ToSeq(window).drop(i))\n"
    "        total = weight + total\n"
    "        i = i - 1\n"
    "    Assert(total == signed_sum(ToSeq(window)))\n"
    "    return total\n",
)


# ===========================================================================
# UNIQUENESS / REJECT rivals (same spec, WRONG impl)
# ===========================================================================

# (4) frame-mutation-amp : MANDATORY. The input `window` is read-only at
#     Acc(list_pred(window), 1/2). This rival WRITES to it (`window[0] = total`)
#     before returning the correct value. A write needs FULL permission; the
#     frame only grants 1/2 -> MUST be rejected for INSUFFICIENT PERMISSION. The
#     gold invariants & framing asserts are kept VERBATIM so the rejection is
#     attributable solely to the write, not to a broken proof. A byte-fuzzer
#     never invents this attack.
_FRAME_AMP = _swap(
    _BASE,
    "        total = weight + total\n"
    "        i = i - 1\n"
    "    return total\n",
    "        total = weight + total\n"
    "        i = i - 1\n"
    "    window[0] = total\n"
    "    return total\n",
)

# (5) weak-magnitude-amp : the REAL prepatch bug (refinement.md A / G-DIFF). Use
#     the absolute-value running total `total = magnitude(weight) + total`
#     (Sum|w|, np.abs(window).sum()) instead of the signed total. CORRECT on
#     every all-nonnegative window, DIVERGES exactly on windows with a negative
#     weight (where Sum|w| > |Sum w|). This is precisely the F2P flattop domain.
#     expect=reject: it violates the loop invariant total == signed_sum(...drop(i))
#     and the postcondition Result() == signed_sum(ToSeq(window)).
_WEAK_MAG_AMP = _swap(_BASE, "        total = weight + total\n        i = i - 1\n    return total\n",
                      "        total = magnitude(weight) + total\n        i = i - 1\n    return total\n")

# (6) weak-skip-first-amp : partial-domain. Stop the loop at i > 1, i.e. SKIP the
#     first weight window[0]. CORRECT on any window whose first weight is 0 (and
#     vacuously on empty), DIVERGES whenever window[0] != 0. The flattop window's
#     first weight is the large positive lobe-peak (nonzero), so this rival is
#     wrong on the F2P domain. expect=reject: the loop invariant is established
#     for the tail but the final `return` leaves total == signed_sum(...drop(1))
#     != signed_sum(ToSeq(window)) unless window[0]==0, so the postcondition fails.
_WEAK_SKIP_AMP = _swap(_BASE, "    i = len(window)\n    while i > 0:\n"
                       "        # invariants-start\n"
                       "        Invariant(Acc(list_pred(window), 1 / 2))\n"
                       "        Invariant(0 <= i and i <= len(window))\n"
                       "        Invariant(total == signed_sum(ToSeq(window).drop(i)))\n"
                       "        # the loop consumes the caller's termination obligation with a\n"
                       "        # strictly decreasing measure (i), discharging MustTerminate(2)\n"
                       "        # from the precondition.\n"
                       "        Invariant(MustTerminate(i + 1))\n"
                       "        # invariants-end\n"
                       "        weight = window[i - 1]\n"
                       "        Assert(ToSeq(window).drop(i - 1)[0] == weight)\n"
                       "        Assert(ToSeq(window).drop(i - 1).drop(1) == ToSeq(window).drop(i))\n"
                       "        total = weight + total\n"
                       "        i = i - 1\n"
                       "    return total\n",
                       "    i = len(window)\n    while i > 1:\n"
                       "        # invariants-start\n"
                       "        Invariant(Acc(list_pred(window), 1 / 2))\n"
                       "        Invariant(0 <= i and i <= len(window))\n"
                       "        Invariant(total == signed_sum(ToSeq(window).drop(i)))\n"
                       "        # discharge the termination obligation identically, so the reject\n"
                       "        # stays on the VALUE postcondition, not an obligation leak.\n"
                       "        Invariant(MustTerminate(i + 1))\n"
                       "        # invariants-end\n"
                       "        weight = window[i - 1]\n"
                       "        Assert(ToSeq(window).drop(i - 1)[0] == weight)\n"
                       "        Assert(ToSeq(window).drop(i - 1).drop(1) == ToSeq(window).drop(i))\n"
                       "        total = weight + total\n"
                       "        i = i - 1\n"
                       "    return total\n")

# (7) frame-mutation-pwr : MANDATORY (second read-only input). power_loss_divisor's
#     window is also Acc(...,1/2). Write to it -> insufficient permission. Gold
#     invariants + lemma assert kept verbatim.
_FRAME_PWR = _swap(
    _BASE,
    "        total = weight * weight + total\n"
    "        i = i - 1\n"
    "    Assert(squares_are_sign_blind(ToSeq(window)))\n"
    "    return total\n",
    "        total = weight * weight + total\n"
    "        i = i - 1\n"
    "    window[0] = total\n"
    "    Assert(squares_are_sign_blind(ToSeq(window)))\n"
    "    return total\n",
)

# (8) weak-linear-pwr : the power divisor must be the sum of SQUARES, not the
#     plain signed sum. Use `total = weight + total` (Sum w). CORRECT only on
#     windows where every weight is 0 or 1/-1... actually only where Sum w == Sum w^2
#     (e.g. all-zero, or single +/-1). DIVERGES on the flattop window (real
#     magnitudes). expect=reject: violates invariant total == square_sum(...drop(i)).
_WEAK_LIN_PWR = _swap(
    _BASE,
    "        total = weight * weight + total\n"
    "        i = i - 1\n"
    "    Assert(squares_are_sign_blind(ToSeq(window)))\n"
    "    return total\n",
    "        total = weight + total\n"
    "        i = i - 1\n"
    "    Assert(squares_are_sign_blind(ToSeq(window)))\n"
    "    return total\n",
)

# (9) vacuous-nonterm-amp : an impl that NEVER RETURNS. It spins in an
#     unbounded loop (i increases forever), so every value postcondition is
#     satisfiable only vacuously: no execution reaches the return. This is the
#     exact spec-too-weak class the G-PANEL-1 auditor exploited before the
#     MustTerminate obligation was added (atk_5_oracle_echo materialized
#     `return signed_sum(...)` -- the grounded fold, so the echo itself is the
#     correct VALUE -- but a partial-correctness-only spec also admitted plain
#     divergence). Under Requires(MustTerminate(2)) the spinning loop takes no
#     termination obligation and has no decreasing measure, so Nagini's
#     obligation system MUST reject it. The invariants are relaxed to what the
#     spinning loop maintains -- the reject must come from the obligation
#     system, not a broken proof of a correct impl.
_NONTERM_AMP = _swap(
    _BASE,
    "    total = 0\n"
    "    i = len(window)\n"
    "    while i > 0:\n"
    "        # invariants-start\n"
    "        Invariant(Acc(list_pred(window), 1 / 2))\n"
    "        Invariant(0 <= i and i <= len(window))\n"
    "        Invariant(total == signed_sum(ToSeq(window).drop(i)))\n"
    "        # the loop consumes the caller's termination obligation with a\n"
    "        # strictly decreasing measure (i), discharging MustTerminate(2)\n"
    "        # from the precondition.\n"
    "        Invariant(MustTerminate(i + 1))\n"
    "        # invariants-end\n"
    "        weight = window[i - 1]\n"
    "        Assert(ToSeq(window).drop(i - 1)[0] == weight)\n"
    "        Assert(ToSeq(window).drop(i - 1).drop(1) == ToSeq(window).drop(i))\n"
    "        total = weight + total\n"
    "        i = i - 1\n"
    "    return total\n",
    "    total = 0\n"
    "    i = 1\n"
    "    while 0 <= i:\n"
    "        # invariants-start\n"
    "        Invariant(Acc(list_pred(window), 1 / 2))\n"
    "        Invariant(0 <= i)\n"
    "        # invariants-end\n"
    "        i = i + 1\n"
    "    return total\n",
)


SPEC_TESTS = [
    {
        "id": "pos-control-amp",
        "kind": "soundness",
        "expect": "verify",
        "module": _POS_AMP,
        "rationale": "structurally-different CORRECT amplitude impl (fresh local "
                     "`acc`, commuted `total + acc`, parenthesised decrement); keeps "
                     "the gold backward loop, invariants and framing asserts verbatim, "
                     "so the gold proof of Result()==signed_sum(ToSeq(window)) still "
                     "discharges. Must verify, else SPEC-TOO-STRONG.",
    },
    {
        "id": "pos-control-pwr",
        "kind": "soundness",
        "expect": "verify",
        "module": _POS_PWR,
        "rationale": "structurally-different CORRECT power impl (commuted square "
                     "accumulation `total + acc*acc`, fresh local); gold invariants + "
                     "the squares_are_sign_blind lemma assert kept verbatim. Must "
                     "verify, else SPEC-TOO-STRONG.",
    },
    {
        "id": "admiss-amp",
        "kind": "admissibility",
        "expect": "verify",
        "module": _ADMISS_AMP,
        "rationale": "precondition Acc(list_pred(window),1/2) must ADMIT a normal "
                     "F2P-shaped window: an in-impl Assert pins the base case "
                     "signed_sum(drop(len))==0 and the closing total==signed_sum(full) "
                     "obligation, both establishable for any in-domain window. If it "
                     "fails, PRECOND-TOO-STRONG.",
    },
    {
        "id": "frame-mutation-amp",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _FRAME_AMP,
        "refinement": "the faithful real patch is the window-sum DIVISOR inside "
                      "_spectral_helper; the real `window` ndarray is a caller-shared "
                      "read-only array (it is reused across every segment of the STFT "
                      "loop). A patch that mutated window[0] would corrupt every "
                      "subsequent segment's normalisation and the F2P "
                      "test_psd_window_flattop (and dozens of P2P spectral tests) would "
                      "NOT resolve. So a verifying mutator is a true verify-not-resolve break.",
        "rationale": "rejection from the PERMISSION SYSTEM: window is held at "
                     "Acc(list_pred(window),1/2); the write `window[0]=total` needs full "
                     "permission -> insufficient-permission error. Gold invariants kept "
                     "verbatim so the reject is attributable to the write.",
    },
    {
        "id": "weak-magnitude-amp",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _WEAK_MAG_AMP,
        "refinement": "this IS the gold-patch bug (np.abs(window).sum(), Sum|w|, the "
                      "pre-patch reading; refinement.md A / model_prepatch.py). Its "
                      "faithful real patch keeps the divisor as np.abs(window).sum(), so "
                      "the F2P test_psd_window_flattop (flattop has negative weights, "
                      "Sum|w| != Sum w) FAILS and the instance is NOT resolved.",
        "rationale": "rejection from the loop invariant total==signed_sum(ToSeq(window)"
                     ".drop(i)) and postcondition Result()==signed_sum(ToSeq(window)): "
                     "Sum|w| diverges from Sum w on any negative-weight window. "
                     "partial-domain (agrees on all-nonnegative windows).",
    },
    {
        "id": "weak-skip-first-amp",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _WEAK_SKIP_AMP,
        "refinement": "loop bound `while i > 1` skips window[0]; the faithful real "
                      "patch would compute window[1:].sum() as the divisor. On the F2P "
                      "flattop window (window[0] is the nonzero lobe peak) the divisor is "
                      "wrong, the normalisation identity breaks, F2P NOT resolved.",
        "rationale": "rejection from postcondition Result()==signed_sum(ToSeq(window)): "
                     "the loop leaves total==signed_sum(...drop(1)), short by window[0]. "
                     "partial-domain (agrees only when window[0]==0 or empty).",
    },
    {
        "id": "frame-mutation-pwr",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _FRAME_PWR,
        "refinement": "same caller-shared read-only window as amplitude; a power-branch "
                      "patch that wrote window[0] would corrupt the shared array across "
                      "segments and break the density-branch P2P/F2P normalisation. "
                      "Verify-not-resolve break.",
        "rationale": "rejection from the PERMISSION SYSTEM: Acc(list_pred(window),1/2) "
                     "forbids the write window[0]=total. Gold invariants + lemma assert "
                     "kept verbatim.",
    },
    {
        "id": "weak-linear-pwr",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _WEAK_LIN_PWR,
        "refinement": "uses Sum w (the amplitude reduction) where the power divisor must "
                      "be Sum w^2 ((window**2).sum()). The faithful real patch would "
                      "divide the density branch by window.sum() instead of "
                      "(window**2).sum() -- wrong physical normalisation -- and the F2P "
                      "spectrum/density identity (spec*win.sum()**2 == spec_a*Fs*"
                      "(win**2).sum()) would NOT hold, so NOT resolved.",
        "rationale": "rejection from invariant total==square_sum(ToSeq(window).drop(i)): "
                     "Sum w != Sum w^2 except on trivial 0/+-1 windows. partial-domain.",
    },
    {
        "id": "vacuous-nonterm-amp",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _NONTERM_AMP,
        "refinement": "the rival never returns: it spins in an unbounded loop, so every "
                      "value postcondition holds only vacuously and no divisor is ever "
                      "delivered to _spectral_helper. Its faithful real patch is a "
                      "window-sum computation that hangs -- psd()/specgram() would never "
                      "return, the F2P test_psd_window_flattop times out/fails, NOT "
                      "resolved. This is the exact attack class (G-PANEL-1 "
                      "atk_5_oracle_echo era) that motivated the MustTerminate obligation.",
        "rationale": "MUST reject via the OBLIGATION system: the divisor's "
                     "Requires(MustTerminate(2)) forces every loop on the path to the "
                     "return to carry a decreasing termination measure; the spinning loop "
                     "has none, so Nagini rejects (obligation leak / MustTerminate not "
                     "discharged). Rejection source: the termination obligation, not a "
                     "value clause -- demonstrating the spec no longer admits vacuous "
                     "divergence.",
    },
]

# No @ContractOnly axioms and no consumed-axiom obligations in this bundle (the
# reductions are deep folds, A-reference, validated == numpy by axiom_check.py /
# G-AX out-of-band). Hence the axiom lane is vacuous here.
AXIOM_TESTS = []
