"""properties.py — G-PBT falsification battery for django__django-11728 (velvet).

NOT a Velvet module; a record of adversarial cases the G-PBT gate executes.
Each SPEC case is a full ``Solution.lean`` variant that shares the FROZEN spec
byte-for-byte (region surgery: only text inside the ``-- impl-start`` /
``-- impl-end`` region, or inside the ``prove_correct`` tactic body, is changed
— both regions the consumer spec view elides, so ``markers.same_spec`` holds and
the ``prove_correct scanGroupEnd`` obligation survives with a byte-identical
statement) and swaps in a candidate implementation; it is checked by the real
verifier. ``expect:"verify"`` passes iff (in scope AND verifies);
``expect:"reject"`` passes iff (in scope AND does NOT verify AND its refutation
``witness`` discriminates: it must ELABORATE against the rival and FAIL against
the frozen solution).

DEFENDED SURFACE (one contracted method):

  scanGroupEnd (rest : List Char) return (out : Option Nat)
    ensures out = scanLen none 1 rest                               (C1)

The operation scans the characters that FOLLOW an already-open grouping token to
locate the bracket that balances it, reporting the number of leading characters
consumed UP TO AND INCLUDING that balancing bracket, or the absent marker
(``none``) when the depth never returns to zero. The single top-level clause C1
pins the reported count EXACTLY to the modeled forward scan ``scanLen none 1
rest`` — a fully transparent, front-recursive ``def`` over the sole input
``rest`` that folds the running unescaped-bracket depth one character at a time
(``nextBal``) and stops at the first return to depth zero. There is NO opaque
answer key to echo: ``scanLen``/``nextBal`` are concrete ``def``s in the
``pure`` region (the ``axioms`` region is empty), validated == the real repo
scan out-of-band by axiom_check.py (G-AX). The method has NO precondition (the
``pre-conditions`` region is empty), so the admitted input domain is total.

The load-bearing behavior the F2P demands: the reported count must include the
balancing bracket even when that bracket is the FINAL character of ``rest``
(``scanLen`` returns ``some rest.length`` there, not ``none``). Recording the
span one scan-step late — the pre-patch shape — drops exactly such a
trailing-bracket group; pinning ``out`` to the EXACT ``scanLen`` count is what
refutes that.

CARRIER — fully transparent, so the whole reject lane is expressible. Because
``scanLen`` is a concrete recursive ``def`` (not an opaque callee), C1 can be
probed at a concrete input by ``decide``. The subtlety is the frozen impl is a
``while`` loop, whose EXTRACTED ``scanGroupEndExec`` program does not reduce
under ``decide`` at a concrete input (the ``forIn``/invariant-gadget form stays
stuck). So each rival is written as a STRAIGHT-LINE impl whose ``…Exec`` DOES
reduce, and every witness states — via the extracted ``scanGroupEndExec``
program matched to its result — that the rival's output differs from the modeled
scan ``scanLen none 1 rest`` at one concrete ``rest`` (a direct attack on C1).
The witness is checked in a file whose ``prove_correct`` block has been
stripped, so no tactic script can mask the verdict.

ADVERSARIAL READ of the nagini classes (the sibling contracts TWO byte-identical
functions — a named-group and an unnamed-group site — over a permission-bearing
``List[int]`` with the scan run by a verified backward ``while`` loop; this
backend models the ONE shared scan operation as the single method
``scanGroupEnd`` over a ``List Char`` with the count pinned to the transparent
``scanLen``):
  * FRAME / PERMISSION-MUTATION — VACUOUS on this backend. The class exists on
    nagini because a read-only input held at ``Acc(list_pred(region),1/2)``
    carries a fractional heap permission an impl can overwrite (the sibling's
    MANDATORY frame-write rival: ``region[0]=…`` before scanning, rejected for
    INSUFFICIENT PERMISSION). Lean and Velvet are referentially transparent;
    this bundle declares no ``mut`` PARAMETER (``rest`` is an immutable value;
    the ``let mut`` locals in the frozen impl are function-local, not inputs),
    there is no heap and no aliasing. There is no read-only input to mutate and
    no permission system to trip, so the class is vacuous. Its ARGUMENT (a
    faithful patch corrupting the scanned pattern text would break the
    downstream slice/substitution) has no value footprint the spec can force
    here — the scan is read-only by construction — so no substitute is
    fabricated (per the porting map, this class is legitimately dropped).
  * UNGROUNDED-ORACLE ECHO — N/A. C1 is a total function of the sole input
    ``rest``; there is no opaque answer key a wrong impl could echo. The
    cheapest correct impl returns the scan directly, which the positive controls
    cover honestly.
  * CONTROL-FLOW-EFFECT — N/A. The method returns a pure ``Option Nat``; there
    is no raise / return-vs-fallthrough / side effect invisible to the value
    abstraction. The stop-vs-continue and count control points ARE the returned
    value, fully captured by C1.
  * PARTIAL-DOMAIN / VALUE — APPLIES, and is the whole reject surface: the
    trailing-bracket pre-patch shape (right on every group whose balancing
    bracket is followed by a character, wrong when it is the FINAL character —
    the reported bug); an off-by-one that reports the close OFFSET rather than
    the count including it (the gold's own ``+1`` correction, wrong on every
    balanced group); and the symmetric over-count (one character too many, wrong
    on every balanced group).

WITNESS PLACEMENT. The three reject witnesses sit at THREE DISTINCT ``rest``
points — ``[')']`` (balancing bracket is the FINAL character), ``[')', 'x']``
(balancing bracket first, a character follows), ``['a', ')', 'x']`` (an ordinary
character, then the balancing bracket, then a trailing character) — so the sole
binder ``rest`` moves across the battery (trailing-close / close-then-char /
char-close-char) and no clause is demonstrated at a single pinned point. Each
witness elaborates against its rival and FAILS against the frozen solution (the
required discrimination), confirmed empirically with scripts/lean_verify.sh.

AXIOM lane: EMPTY. ``meta.json`` declares no consumed ``axiom``; the deep models
``scanLen``/``nextBal`` are A-references validated == the real repo scan by
axiom_check.py (G-AX). Nothing in the proof rests on an axiom, and this gate
ignores ``AXIOM_TESTS`` regardless.
"""
from pathlib import Path

INSTANCE = "django__django-11728"
BACKEND = "velvet"

_BASE = (Path(__file__).parent / "Solution.lean").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# ---- impl-region anchor: the entire frozen forward-scan loop body. Lies wholly
# ---- inside the single `-- impl-start`/`-- impl-end` region and is unique in
# ---- Solution.lean (both facts asserted at load by _swap).
_GOLD_IMPL = (
    "    let mut res : Option Nat := none\n"
    "    let mut i := 0\n"
    "    let mut bal := 1\n"
    "    let mut prev : Option Char := none\n"
    "    let mut stopped := false\n"
    "    while i < rest.length ∧ stopped = false\n"
    "      invariant i ≤ rest.length\n"
    "      invariant if stopped then res = scanLen none 1 rest\n"
    "                else res = none ∧\n"
    "                     scanLen none 1 rest = (scanLen prev bal (rest.drop i)).map (· + i)\n"
    "      done_with stopped = true ∨ i = rest.length\n"
    "      decreasing (rest.length - i) + (if stopped then 0 else 1)\n"
    "    do\n"
    "      let c := rest[i]!\n"
    "      let bal' := nextBal prev bal c\n"
    "      if bal' = 0 then\n"
    "        res := some (i + 1)\n"
    "        stopped := true\n"
    "      else\n"
    "        prev := some c\n"
    "        bal := bal'\n"
    "        i := i + 1\n"
    "    return res"
)

assert _BASE.count(_GOLD_IMPL) == 1, "function impl region drifted from expected text"

# ---- proof-body anchor. The frozen tactic script is tuned to the frozen
# ---- forward-scan loop (it discharges the loop-body goal via the scan-shift
# ---- lemma). A positive control that reshapes the impl away from that loop must
# ---- retune the tactic body; both the impl region and the `prove_correct` body
# ---- are elided from the spec view, so same_spec still holds and the
# ---- `prove_correct scanGroupEnd` obligation survives with an identical
# ---- statement. Unique in the file.
_GOLD_PROOF = (
    "prove_correct scanGroupEnd by\n"
    "  loom_solve\n"
    "  all_goals\n"
    "    first\n"
    "    | (rw [scanLen_shift rest i prev bal (by omega)] at invariant_2; simp_all)\n"
    "    | simp_all"
)

assert _BASE.count(_GOLD_PROOF) == 1, "proof region drifted from expected text"

# A reshaped straight-line impl (no loop) leaves `loom_solve` a goal that closes
# without the loop-body scan-shift lemma; retune to the bare tactic.
_PROOF_STRAIGHT = "prove_correct scanGroupEnd by\n  loom_solve"


def _impl(new_body):
    """Full Solution.lean variant with ONLY the impl region body replaced
    (frozen tactic script kept — used for reject rivals, expected NOT to
    verify)."""
    return _swap(_BASE, _GOLD_IMPL, new_body)


def _impl_proof(new_body, new_proof):
    """Reshape the impl region AND retune the tactic body (soundness positives
    whose reshaped impl no longer matches the frozen loop-tuned script)."""
    return _swap(_swap(_BASE, _GOLD_IMPL, new_body), _GOLD_PROOF, new_proof)


# ---- witness preamble. The frozen `while`-loop `scanGroupEndExec` does not
# ---- reduce under `decide` (the invariant-gadget form stays stuck), so each
# ---- witness extracts the executable program and states, at a concrete input,
# ---- that the rival's own output DIFFERS from the modeled scan `scanLen` — a
# ---- direct C1 violation, which `decide` closes because both the STRAIGHT-LINE
# ---- rival's `…Exec` and `scanLen` reduce at the concrete input. Checked in a
# ---- file whose `prove_correct` block has been stripped, so no tactic script
# ---- interferes.
_EXTRACT = "extract_program_for scanGroupEnd\n\n"


def _witness(inp):
    return (
        _EXTRACT +
        "example :\n"
        f"    (match scanGroupEndExec ({inp}) with | DivM.res r => r | _ => none)\n"
        f"     ≠ scanLen none 1 ({inp}) := by\n"
        "  decide\n")


SPEC_TESTS = [
    # =====================================================================
    # POSITIVE CONTROLS (soundness) — structurally different but CORRECT
    # impls that MUST verify. If a faithful correct impl cannot verify, the
    # spec is SPEC-TOO-STRONG. Each replaces the frozen forward-scan loop with
    # a straight-line reduction and retunes the tactic body to `loom_solve` (the
    # loop-body scan-shift lemma is no longer needed).
    # =====================================================================
    {
        "id": "pos-control-direct",
        "kind": "soundness",
        "expect": "verify",
        # Reshape: report the modeled scan directly, no per-character loop.
        # Trivially meets C1 (`out = scanLen none 1 rest`).
        "module": _impl_proof(
            "    return scanLen none 1 rest",
            _PROOF_STRAIGHT),
        "rationale": (
            "a straight-line reduction (`return scanLen none 1 rest`) is the "
            "simplest correct impl; it meets C1 by definition. If it fails to "
            "verify the spec is SPEC-TOO-STRONG (a faithful correct impl "
            "rejected on branch shape / loop-vs-fold)."),
    },
    {
        "id": "pos-control-let-bind",
        "kind": "soundness",
        "expect": "verify",
        # Reshape: bind the scan to a local, then return it. Observationally
        # identical to pos-control-direct but a distinct executable surface — a
        # second correct reshape defending the soundness surface.
        "module": _impl_proof(
            "    let out : Option Nat := scanLen none 1 rest\n    return out",
            _PROOF_STRAIGHT),
        "rationale": (
            "`let out := scanLen none 1 rest; return out` computes the identical "
            "result as pos-control-direct through a distinct executable surface, "
            "so C1 still discharges; a second structurally-different correct "
            "reshape. If it fails => SPEC-TOO-STRONG."),
    },

    # =====================================================================
    # ADMISSIBILITY (expect=verify). The method has NO `require` clause, so the
    # sibling's "a normal input satisfies the precondition" probe is vacuous
    # here (every input is in-domain). This case is re-aimed at the residual
    # admissibility risk on a total domain: that the post-image is DEGENERATE at
    # the interesting corners — a spec no impl distinguishes reads exactly like
    # one every impl meets. It discharges an in-region `assert` pinning `scanLen`
    # at THREE non-degenerate points: a trailing balancing bracket maps to its
    # length (the F2P corner, `[')'] => some 1`), a nested group maps past its
    # inner brackets (`['(', ')', ')'] => some 3`), and an ESCAPED bracket does
    # NOT close (`['\\', ')'] => none`), exercising the escape semantics. The
    # frozen loop and obligation statement are kept verbatim; the proof is
    # retuned to discharge both the live assert goal and the frozen loop-body
    # goal, so C1 still holds and the assert is live (a false claim would leave
    # an unsolved goal).
    # =====================================================================
    {
        "id": "admiss-nondegenerate-scan",
        "kind": "admissibility",
        "expect": "verify",
        "module": _impl_proof(
            "    assert (with_name_prefix `assert\n"
            "      (scanLen none 1 ([')'] : List Char) = some 1\n"
            "       ∧ scanLen none 1 (['(', ')', ')'] : List Char) = some 3\n"
            "       ∧ scanLen none 1 (['\\\\', ')'] : List Char) = none))\n"
            + _GOLD_IMPL,
            "prove_correct scanGroupEnd by\n"
            "  loom_solve\n"
            "  all_goals\n"
            "    first\n"
            "      | decide\n"
            "      | (rw [scanLen_shift rest i prev bal (by omega)] at invariant_2; simp_all)\n"
            "      | simp_all"),
        "rationale": (
            "the post-image is satisfiable AND non-degenerate at three "
            "qualitatively distinct corners: a trailing balancing bracket maps "
            "to its length (`scanLen none 1 [')'] = some 1`, the F2P corner), a "
            "nested group consumes past its inner brackets "
            "(`scanLen none 1 ['(', ')', ')'] = some 3`), and an ESCAPED bracket "
            "does NOT close the group (`scanLen none 1 ['\\\\', ')'] = none`, "
            "exercising the escape semantics). The in-region assert must "
            "discharge (else the modeled scan would be degenerate at those "
            "points); the frozen loop and obligation are verbatim so C1 still "
            "discharges too. If it fails => the modeled scan is unsatisfiable at "
            "a normal input (degeneracy)."),
    },

    # =====================================================================
    # UNIQUENESS / SPEC-TOO-WEAK rivals — wrong impls sharing the frozen spec
    # that MUST be rejected, each a straight-line impl carrying a machine-checked
    # refutation witness at a DISTINCT concrete `rest` and the refinement
    # argument that its faithful real counterpart would NOT resolve the failing
    # tests.
    # =====================================================================
    {
        "id": "rej-prepatch-trailing",
        "kind": "uniqueness",
        "expect": "reject",
        # THE pre-patch bug. Recording the span one scan-step late means a group
        # whose balancing bracket is the FINAL character is dropped (there is no
        # next step to record it): on this carrier that is exactly reporting the
        # absent marker `none` whenever the balancing bracket is at the last
        # position (count = rest.length), while every group followed by a
        # character is reported correctly.
        "module": _impl(
            "    match scanLen none 1 rest with\n"
            "    | none => return none\n"
            "    | some k => if k = rest.length then return none else return (some k)"),
        "refinement": (
            "this is the pre-patch shape: the balance check is applied one "
            "scan-step late, so a group whose balancing bracket is the final "
            "character is never recorded (the loop ends before the deferred "
            "record fires) and the group is dropped entirely. The F2P test on a "
            "pattern with a trailing capture group and no trailing delimiter "
            "still observes the group UNREPLACED and stays RED — it is the very "
            "bug the change fixes. It would NOT resolve."),
        "rationale": (
            "REJECT from C1: on an input whose balancing bracket is the final "
            "character the impl reports `none` where the post-image demands "
            "`some rest.length`. If it verifies => SPEC-TOO-WEAK on the "
            "trailing-bracket sub-domain (the reported regression). Refuted at "
            "`rest = [')']` (balancing bracket is the only, hence final, "
            "character), the trailing point no other rival isolates."),
        "witness": _witness("[')']"),
    },
    {
        "id": "rej-offbyone-short",
        "kind": "uniqueness",
        "expect": "reject",
        # The gold's own off-by-one: report the close OFFSET (count minus one)
        # rather than the count INCLUDING the balancing bracket. Wrong on every
        # balanced group (whenever the scan reports `some k`, this reports
        # `some (k - 1)`); keeps `none` on unbalanced input.
        "module": _impl(
            "    return (scanLen none 1 rest).map (· - 1)"),
        "refinement": (
            "reporting the close OFFSET instead of the count INCLUDING the "
            "balancing bracket is the off-by-one the change corrects (the slice "
            "end one character short). A real patch with this offset slices the "
            "captured group one character short, dropping its closing bracket, "
            "so the downstream substitution produces the wrong text. The F2P/P2P "
            "tests pinning the exact replaced pattern still observe the "
            "one-char-short group and stay RED. It would NOT resolve."),
        "rationale": (
            "REJECT from C1: whenever the scan reports `some k`, the impl reports "
            "`some (k - 1)`, contradicting `out = scanLen none 1 rest` on every "
            "balanced group. If it verifies => SPEC-TOO-WEAK (the +1 that "
            "includes the balancing bracket is unpinned). Refuted at "
            "`rest = [')', 'x']` (balancing bracket first, count `some 1`), where "
            "the impl reports `some 0`."),
        "witness": _witness("[')', 'x']"),
    },
    {
        "id": "rej-offbyone-long",
        "kind": "uniqueness",
        "expect": "reject",
        # The symmetric over-count: report one character too many. Wrong on every
        # balanced group (`some k` -> `some (k + 1)`); keeps `none` on unbalanced
        # input. The other-direction dual of rej-offbyone-short.
        "module": _impl(
            "    return (scanLen none 1 rest).map (· + 1)"),
        "refinement": (
            "over-counting by one reports a slice end one character PAST the "
            "balancing bracket. A real patch with this offset extends the "
            "captured group by the character after its closing bracket, so the "
            "downstream substitution matches/replaces the wrong span. The tests "
            "pinning the exact replaced pattern still observe the over-long group "
            "and stay RED. It would NOT resolve."),
        "rationale": (
            "REJECT from C1: whenever the scan reports `some k`, the impl reports "
            "`some (k + 1)`, contradicting `out = scanLen none 1 rest` on every "
            "balanced group. If it verifies => SPEC-TOO-WEAK (the count's upper "
            "bound is unpinned). Refuted at `rest = ['a', ')', 'x']` (ordinary "
            "char, then the balancing bracket, count `some 2`), where the impl "
            "reports `some 3` — a distinct `rest` shape from the other rivals, "
            "isolating the over-count direction."),
        "witness": _witness("['a', ')', 'x']"),
    },
]


# ---------------------------------------------------------------------------
# Nagini -> velvet accounting. The sibling battery has 7 SPEC cases (2 soundness
# positives, 1 admissibility, 4 uniqueness — one of which is the mandatory frame-
# mutation rival) plus 0 AXIOM_TESTS. The sibling contracts TWO byte-identical
# functions — a named-group and an unnamed-group scan site — over a
# permission-bearing `List[int]`, with the scan run by a verified backward
# `while` loop and the count pinned to a grounded @Pure fold (`close_off`). This
# backend models the ONE shared scan operation as the single method
# `scanGroupEnd` over a `List Char`, with the count pinned to the transparent
# `scanLen`. The value surface carries across intact; the permission surface, the
# loop shape, and the two-function split do not exist here. Every sibling case is
# accounted for below.
#
#   sibling case (nagini)       -> here                            disposition
#   -----------------------------------------------------------------------------
#   pos-break-reshape           -> pos-control-direct              RE-SHAPED
#   pos-grounded-oracle         -> pos-control-let-bind            RE-SHAPED
#   adm-nonvacuous-precond      -> admiss-nondegenerate-scan       RE-AIMED
#   rej-frame-mutation          -> (none)                          VACUOUS
#   rej-prepatch-top-check      -> rej-prepatch-trailing           PORTED
#   rej-offbyone-named          -> rej-offbyone-short              PORTED
#   rej-offbyone-unnamed        -> (collapsed) + rej-offbyone-long ADDED
#
# 2 ported, 2 re-shaped, 1 re-aimed, 1 vacuous, 1 collapsed; 1 rival added.
#
# RE-SHAPED (pos-*): the sibling's two positive controls run the gold loop with a
#   relaxed guard + explicit break (pos-1) and materialize the grounded oracle
#   directly (pos-2). This backend's frozen impl is a `while` loop whose exact
#   guard-relax reshape is not the natural analogue; the reshape SPIRIT —
#   "structurally different, behaviourally identical" — is carried by dropping
#   the loop and reporting the modeled scan directly (pos-control-direct, which
#   IS the grounded-oracle control since `scanLen` is a fully-unfolded function
#   of the input, not an opaque answer key) and a second let-bound reshape
#   (pos-control-let-bind). Both retune the tactic body (elided from the spec
#   view) to `loom_solve`.
# RE-AIMED (adm): the sibling's admissibility case asserts `len(region) >= 1`
#   inside the impl to prove the precondition `close_off(...) < len(region)` is
#   non-vacuous. This method has NO `require` clause (the pre-conditions region
#   is empty), so the "admits a normal input" reading is vacuous. The case is
#   re-aimed at proving the post-image is satisfiable and NON-degenerate at three
#   qualitatively distinct corners (trailing close, nested group, escaped
#   bracket), discharged against concrete literals; the frozen loop and
#   obligation are kept verbatim so C1 still discharges.
# VACUOUS (rej-frame-mutation): the sibling's MANDATORY frame-mutation rival
#   keeps the gold body verbatim then writes back into the read-only `region`
#   input granted only at half permission (`region[0]=…`) and must be rejected
#   for INSUFFICIENT PERMISSION. This backend is referentially transparent:
#   `rest` is an immutable value, this bundle declares no `mut` PARAMETER, there
#   is no heap and no aliasing. There is no read-only input to overwrite and no
#   permission system to trip, so the class is vacuous. Its ARGUMENT (a faithful
#   patch corrupting the scanned pattern text would break the downstream
#   slice/substitution) has no value footprint the spec can force here — the scan
#   is read-only by construction — so no substitute is fabricated (per the
#   porting map, this class is legitimately dropped).
# COLLAPSED + ADDED (rej-offbyone-unnamed): the sibling's second off-by-one rival
#   is a DIFFERENTIAL witness on the SECOND modeled function (the unnamed-group
#   site), asserting its postcondition is independently tight. This backend
#   models the two byte-identical scan sites as the ONE method `scanGroupEnd`
#   (they share the exact scan; only the surrounding base offset differs, and the
#   base offset is a genuinely-unchanged callee not modeled here), so the second
#   function has no counterpart and the differential case collapses. In its place
#   rej-offbyone-long is ADDED: the symmetric OVER-count (report one char too
#   many), the other-direction dual of rej-offbyone-short, so the count clause is
#   pinned from BOTH sides (short and long) at a third distinct `rest` point.
#
# BINDER / CLAUSE COVERAGE. The sole input binder is `rest`; the single
#   top-level clause is C1 (`out = scanLen none 1 rest`). C1 is attacked by all
#   three rivals, each at a distinct sub-domain: the trailing-bracket regression
#   (rej-prepatch-trailing), the count-too-short off-by-one (rej-offbyone-short),
#   and the count-too-long off-by-one (rej-offbyone-long). `rest` is varied
#   across THREE DISTINCT witness inputs (pts=3): [')'] (balancing bracket is the
#   final character), [')', 'x'] (bracket first, char follows), ['a', ')', 'x']
#   (char, bracket, char) — covering the trailing sub-domain (the F2P corner) and
#   both off-by-one directions at interior positions. The admissibility case
#   additionally exercises the escape and nesting semantics of the scan.
#
# WITNESS FORM. The frozen `while`-loop `scanGroupEndExec` does not reduce under
#   `decide`. So each rival is a STRAIGHT-LINE impl whose `…Exec` reduces, and
#   each witness asserts the rival's extracted output differs from the
#   transparent scan `scanLen` at its concrete point — a direct C1 violation.
#   Every witness binds nothing (no conditioning is needed — the carrier is
#   transparent), so the consistency probe is trivially satisfied. Confirmed
#   empirically: each witness elaborates against its rival and FAILS against the
#   frozen solution (the required discrimination).
#
# AXIOM_TESTS: dropped. The axiom lane is G-AX's job; this gate ignores it. The
#   deep models `scanLen`/`nextBal` are A-references validated == the real repo
#   scan by axiom_check.py, not a G-PBT concern, and the `axioms` region is
#   empty.
AXIOM_TESTS = []
