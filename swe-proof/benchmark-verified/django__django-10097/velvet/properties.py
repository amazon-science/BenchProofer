"""properties.py — G-PBT falsification battery for django__django-10097 (velvet).

NOT a Velvet module; a record of adversarial cases the G-PBT gate executes.
Each SPEC case is a full ``Solution.lean`` variant that shares the FROZEN spec
byte-for-byte (region surgery: only text inside the ``-- impl-start`` /
``-- impl-end`` region, or inside the ``prove_correct`` tactic body, is changed —
both of which the consumer spec view elides, so ``markers.same_spec`` holds and
the ``prove_correct validateAuthsegment`` obligation survives with a
byte-identical statement) and swaps in a candidate implementation; it is checked
by the real verifier. ``expect:"verify"`` passes iff (in scope AND verifies);
``expect:"reject"`` passes iff (in scope AND does NOT verify AND its refutation
``witness`` discriminates — the witness must ELABORATE against the rival and FAIL
against the frozen solution).

DEFENDED SURFACE (one contracted method over a single code-point sequence):

  validateAuthsegment (seg : List Char) return (ok : Bool)
    ensures ok = accepts seg            -- THE load-bearing (and only) clause

with ``accepts`` a fully-unfolded ``def`` in the ``pure`` region:

  accepts (c :: cs) = bodyOk (c :: cs) && colons (c :: cs) ≤ 1 && c.toNat != 58
  accepts []        = false

so the single clause pins FOUR independent sub-behaviours of a candidate
authentication segment (the code-point run before a terminating separator):

  * NON-EMPTY: the empty run is rejected (``accepts [] = false``);
  * BODY: every code point is an authentication character (not whitespace and not
    one of the three separators, code points 58 / 64 / 47) OR the single
    permitted separator colon (58) — the front-recursive fold ``bodyOk`` with
    ``isUchar`` / ``isWhitespace``;
  * COLON-COUNT: at most one separator colon (``colons seg ≤ 1``);
  * LEADING: the run does not begin with the separator colon
    (``seg[0].toNat != 58`` — the leading authentication run is mandatory).

``accepts`` is GROUNDED in the input (a total fold over ``seg``); the ``axioms``
region is empty (``accepts`` is a deep A-reference validated == the real matcher
by axiom_check.py, NOT a consumed answer key), so there is no wrong echo to build
and the ungrounded-oracle probe is replaced by two honest positive controls. The
sole INPUT BINDER is ``seg``.

THE CARRIER IS FULLY TRANSPARENT. ``accepts`` / ``bodyOk`` / ``colons`` /
``isUchar`` / ``isWhitespace`` all compute on ``Char`` literals, so a witness
reaches the impl through Velvet's extractor (``extract_program_for
validateAuthsegment`` gives ``validateAuthsegmentExec seg = NonDetT.run
(validateAuthsegment seg)``) and states ``validateAuthsegmentExec s ≠
DivM.res (accepts s)`` at a concrete ``s`` (no opaque leaf, so no witness binds a
hypothesis and there is no joint-satisfiability obligation). Each reject rival is
a straight-line loop-free CLOSED FORM whose extracted program reduces to a
literal, so the witness ELABORATES against the rival.

WHICH SUBJECT REFUTES THE WITNESS, AND WHY THE TACTIC IS ``all_goals decide``.
The frozen impl's ``while`` loop is NOT kernel-reducible: its extracted program
keeps an un-normalised ``forIn Lean.Loop.mk`` term, so on the frozen solution the
elaborator cannot even synthesize ``Decidable`` for the claim
(``error: failed to synthesize Decidable ¬(NonDetT.run do let r ← forIn
Lean.Loop.mk ...)``). That is a STUCK build, not a refutation, for five of the six
reject cases — only the ``[]`` case decides on gold, because ``accepts []``
reduces without entering the loop. So the discriminating subject for those five is
the battery's own ``pos-control-direct`` positive: a loop-free VERIFYING impl of
this same frozen spec, which the gate independently re-checks (shares the spec
AND verifies) before refuting the witness against it. An impl the verifier accepts
cannot violate its own spec, so a genuine refutation must still fail there.

The tactic matters, and a bare trailing ``decide`` makes the case HOLLOW. When the
claim is TRUE of the subject, ``simp`` closes the goal outright and a bare
``decide`` then errors ``No goals to be solved`` — the same exit 1 a genuine
refutation produces. Measured on this cell: at the disagreement point
``['a',':','b',':','c']`` the real witness and its exact OPPOSITE (``=`` for
``≠``) BOTH failed against ``pos-control-direct`` with exit 1, so the subject's
exit code carried no information about the claim and a witness asserting the impl
is CORRECT there would have been recorded as a refutation. ``all_goals decide``
tolerates an already-closed goal, so the exit now TRACKS the claim: verified per
case, the real ``≠`` witness exits 0 on the rival and 1 on the subject, while the
flipped ``=`` claim exits 1 on the rival and 0 on the subject. A forgery at an
AGREEMENT point (``['a','b']``, where rival and ``accepts`` concur) exits 0 on
BOTH, so it cannot clear the discrimination check.

ADVERSARIAL READ of the nagini classes on this carrier:
  * FRAME / PERMISSION-MUTATION — VACUOUS. The nagini sibling carries this as a
    MANDATORY rival (store ``seg[i-1] := 102`` through a read-only reference held
    at ``Acc(list_pred(seg), 1/2)``) because a store needs full permission. Lean
    and Velvet are referentially transparent: ``seg`` is an immutable value, this
    bundle declares NO ``mut`` binder over any input, and there is no heap and no
    aliasing — so there is no read-only input to overwrite and no substitute
    probe to build. Not fabricated (per the porting map: this class is vacuous on
    Lean/Velvet).
  * PARTIAL-DOMAIN / VALUE — APPLIES; the heart of the port. Each nagini
    partial-domain rival re-expresses directly onto one clause of ``accepts``,
    plus three added rivals: the NON-EMPTY clause the nagini sibling folds into
    its length guard, the non-ASCII half of the whitespace class, and the
    OVER-strict direction (a mandatory separator).
  * ADMISSIBILITY — APPLIES, re-aimed. The sibling's precondition-admits-a-normal-
    input probe has no permission analogue here (no ``require`` clause), but the
    total-carrier analogue does apply: the obligation must be SATISFIABLE and
    non-degenerate at an F2P-shaped input. See ``admiss-f2p-accepts-satisfiable``.
  * UNGROUNDED-ORACLE ECHO — N/A. ``accepts`` is a total ``def`` over the
    method's own input; there is no answer key to echo. Replaced by the honest
    positive controls (the cheapest direct impl + a structurally different loop).

AXIOM lane: EMPTY (``meta.json`` declares no consumed ``axiom``; ``accepts`` is a
deep A-reference validated == the real compiled matcher by axiom_check.py — that
is G-AX's job, and this gate ignores ``AXIOM_TESTS`` regardless).
"""
from pathlib import Path

INSTANCE = "django__django-10097"
BACKEND = "velvet"

_BASE = (Path(__file__).parent / "Solution.lean").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# ---------------------------------------------------------------------------
# Anchors. Each lies wholly inside a region the spec view elides (the impl body
# between -- impl-start / -- impl-end, or the prove_correct tactic body) and is
# unique in Solution.lean; both facts are asserted at load by _swap. Editing only
# these keeps markers.same_spec True and the prove_correct validateAuthsegment
# statement byte-identical.
# ---------------------------------------------------------------------------

# The WHOLE executable body of the method (the backward per-code-point loop plus
# the final decision). Reject rivals replace it with a loop-free closed form
# (so their extracted program reduces under decide); the direct positive control
# replaces it with `return accepts seg`.
_IMPL = (
    "    let n := seg.length\n"
    "    if n = 0 then\n"
    "      return false\n"
    "    else\n"
    "      let mut good : Bool := true\n"
    "      let mut ncolon : Nat := 0\n"
    "      let mut i := n\n"
    "      while i > 0\n"
    "        invariant 0 ≤ i ∧ i ≤ n\n"
    "        invariant n = seg.length\n"
    "        invariant good = bodyOk (seg.drop i)\n"
    "        invariant ncolon = colons (seg.drop i)\n"
    "        done_with i = 0\n"
    "        decreasing i\n"
    "      do\n"
    "        let c := seg[i - 1]!\n"
    "        if c.toNat = 58 then\n"
    "          ncolon := ncolon + 1\n"
    "        else if !isUchar c then\n"
    "          good := false\n"
    "        i := i - 1\n"
    "      let c0 := seg[0]!\n"
    "      return good && ncolon ≤ 1 && c0.toNat != 58\n"
)

# The per-code-point discriminating block (the colon-count bump / uchar check).
# The reorder positive control splits it into two INDEPENDENT guarded ifs.
_DISCR = (
    "        if c.toNat = 58 then\n"
    "          ncolon := ncolon + 1\n"
    "        else if !isUchar c then\n"
    "          good := false\n"
)

# The frozen prove_correct tactic body (the whole block, unique in the file and
# elided from the spec view). The direct positive control retunes it (the loop is
# gone, so `loom_solve` alone closes the residual goal); every reject rival keeps
# it as-is (it fails to close the wrong impl, which is exactly the intended
# rejection, but the witness — not the tactic failure — is what the gate scores).
_PROOF = (
    "prove_correct validateAuthsegment by\n"
    "  loom_solve <;>\n"
    "  first\n"
    "  | (rw [drop_pred_cons seg i (by omega) (by omega)]\n"
    "     simp_all [bodyOk_cons, colons_cons] <;> omega)\n"
    "  | (have hempty : seg = [] := by\n"
    "       rw [← List.length_eq_zero_iff]; assumption\n"
    "     rw [hempty]; rfl)\n"
    "  | (have hne : seg ≠ [] := by\n"
    "       simp only [ne_eq, ← List.length_eq_zero_iff]; assumption\n"
    "     have hlen : 0 < seg.length := List.length_pos_iff.mpr hne\n"
    "     rw [accepts_cons seg hne,\n"
    "       List.getElem!_eq_getElem?_getD, List.getElem?_eq_getElem hlen, Option.getD_some]\n"
    "     simp_all [List.drop_zero])\n"
)


def _rival(expr: str) -> str:
    """Solution.lean whose impl body is a single loop-free `return (<expr>)`."""
    return _swap(_BASE, _IMPL, f"    return ({expr})\n")


# ---- witness preamble. The spec is a `method` CONTRACT over a fully-transparent
# ---- carrier, so a witness reaches the impl through Velvet's extractor:
# ---- `validateAuthsegmentExec s` is `NonDetT.run (validateAuthsegment s)`;
# ---- `≠ DivM.res (accepts s)` says the impl's output contradicts the
# ---- postcondition at that concrete input. Checked in a file whose
# ---- `prove_correct` block is stripped, so no tactic script can mask the
# ---- verdict. The loop-free rival reduces under `decide`; gold's loop stays
# ---- stuck, so the same witness fails on gold — the required discrimination.
_EXTRACT = "extract_program_for validateAuthsegment\n\n"


def _witness(inp: str) -> str:
    """The refutation at `inp`, with a CLAIM-TRACKING closing tactic.

    `all_goals decide`, never a bare `decide`. Against a subject the claim is
    TRUE of, `simp` closes the goal by itself and a bare `decide` then errors
    `No goals to be solved` — indistinguishable, by exit code, from the
    `decide proved ... is false` a genuine refutation produces. Both halves of
    the gate's discrimination check read exit codes, so under a bare `decide`
    the flipped claim (asserting the impl is CORRECT at this input) fails on the
    subject exactly as the real witness does, and the case attests to nothing.
    Measured on this cell with real builds; see the module docstring.
    """
    return _EXTRACT + (
        "example : validateAuthsegmentExec " + inp + " ≠ "
        "DivM.res (accepts " + inp + ") := by\n"
        "  unfold validateAuthsegmentExec validateAuthsegment\n"
        "  simp [NonDetT.run, pure]\n"
        "  all_goals decide\n"
    )


SPEC_TESTS = [
    # =====================================================================
    # POSITIVE CONTROL (soundness) — the cheapest HONEST impl, which MUST verify
    # (else SPEC-TOO-STRONG). `accepts seg` is GROUNDED in the argument (a total
    # fold), so `return accepts seg` is a correct fully-grounded implementation,
    # not an ungrounded-oracle echo — and it doubles as proof the spec is not
    # echo-vulnerable: any WRONG constant/echo fails `ok = accepts seg`. The loop
    # is gone, so the frozen proof body's loop reasoning is unneeded and the
    # residual goal closes under `loom_solve` alone.
    # =====================================================================
    {
        "id": "pos-control-direct",
        "kind": "soundness",
        "expect": "verify",
        "module": _swap(
            _rival("accepts seg"),
            _PROOF,
            "prove_correct validateAuthsegment by\n  loom_solve"),
        "rationale": "the post-image `accepts seg` is GROUNDED in the input (a "
                     "total fold, no opaque answer key), so `return accepts seg` "
                     "is the honest cheapest CORRECT impl. It MUST verify — the "
                     "clause is literally `ok = accepts seg` — else the single "
                     "postcondition clause is SPEC-TOO-STRONG. Also shows the "
                     "spec is not echo-vulnerable: any wrong constant/echo would "
                     "fail `ok = accepts seg`.",
    },

    # =====================================================================
    # POSITIVE CONTROL (soundness) — a structurally DIFFERENT but CORRECT impl
    # that keeps the frozen backward loop and its invariants BYTE-IDENTICAL, only
    # reshaping the per-code-point discriminating step: the gold `if colon / else
    # if not-uchar` is split into two INDEPENDENT guarded ifs (the second guarded
    # by `c != 58`, so a colon never clears `good`, matching `bodyOk` which treats
    # ':' as acceptable). Semantically identical, so every loop invariant and the
    # `ok = accepts seg` obligation still discharge under the frozen proof script
    # with no retune. A faithful correct reshape that could NOT verify would mean
    # the postcondition is over-fit to one branch FORM => SPEC-TOO-STRONG.
    # =====================================================================
    {
        "id": "pos-control-reorder",
        "kind": "soundness",
        "expect": "verify",
        "module": _swap(
            _BASE, _DISCR,
            "        if c.toNat = 58 then\n"
            "          ncolon := ncolon + 1\n"
            "        if c.toNat != 58 && !isUchar c then\n"
            "          good := false\n"),
        "rationale": "structurally different CORRECT reshape: the colon-count bump "
                     "and the uchar check are split into two independent guarded "
                     "ifs (the second guarded by `c != 58` so a colon never clears "
                     "`good`, matching `bodyOk`), keeping every loop invariant "
                     "byte-identical. `ok = accepts seg` still discharges under the "
                     "frozen proof. A faithful reshape MUST verify, else the clause "
                     "is over-fit to the if/else-if FORM => SPEC-TOO-STRONG.",
    },

    # =====================================================================
    # ADMISSIBILITY (PRECOND-TOO-STRONG) — the direction the other two lanes
    # cannot see. The frozen obligation carries NO `require` clause, so there is
    # no precondition to admit; on a TOTAL carrier the analogue is the obligation
    # being UNSATISFIABLE at an F2P-shaped input, i.e. the post-image collapsing
    # to a constant or refusing every well-formed segment. That is what this case
    # tests directly: a `have ... := by decide` discharges `accepts` BY EVALUATION
    # at seven concrete F2P-shaped code-point runs before the frozen obligation is
    # closed verbatim, pinning that the acceptance predicate is
    #   * SATISFIED at a bare authentication run, at a run with the one permitted
    #     separator, and at a run whose post-separator segment is empty; and
    #   * REFUSED at the three narrowed-away shapes (a non-colon forbidden
    #     separator inside the run, a second forbidden separator, two separator
    #     colons) and at an empty leading run.
    # Both directions together are what make it non-vacuous: a spec that accepted
    # nothing would fail the first three conjuncts, and one that accepted
    # everything would fail the last four. The impl is kept BYTE-IDENTICAL and the
    # frozen tactic body follows the `have` unchanged, so the method's own
    # `ok = accepts seg` obligation still discharges on its own terms; the `have`
    # is discarded (`clear`) so it cannot contribute to that proof.
    # LIVENESS was checked with a real build, not assumed: flipping ONE conjunct
    # to a false claim (`accepts ['f','o','o','/','b','a','r'] = true`) makes the
    # file FAIL (`decide` proved the conjunction false), so the `have` is a live
    # obligation rather than a decoration.
    # =====================================================================
    {
        "id": "admiss-f2p-accepts-satisfiable",
        "kind": "admissibility",
        "expect": "verify",
        "module": _swap(
            _BASE, _PROOF,
            "prove_correct validateAuthsegment by\n"
            "  have hadmiss :\n"
            "      accepts ['f', 'o', 'o'] = true\n"
            "      ∧ accepts ['f', 'o', 'o', ':', 'b', 'a', 'r'] = true\n"
            "      ∧ accepts ['f', 'o', 'o', ':'] = true\n"
            "      ∧ accepts ['f', 'o', 'o', '/', 'b', 'a', 'r'] = false\n"
            "      ∧ accepts ['f', 'o', 'o', '@', 'b', 'a', 'r'] = false\n"
            "      ∧ accepts ['f', 'o', 'o', ':', 'b', ':', 'z'] = false\n"
            "      ∧ accepts [':', 'p'] = false := by decide\n"
            "  clear hadmiss\n" + _PROOF.split("\n", 1)[1]),
        "rationale": "PRECOND-TOO-STRONG probe, re-aimed at what the analogue is "
                     "on a total carrier: the obligation `ok = accepts seg` is "
                     "SATISFIABLE — and non-degenerate — at F2P-shaped inputs. "
                     "The `have` discharges `accepts` by EVALUATION at seven "
                     "concrete runs, three that must be accepted (a bare "
                     "authentication run, a run with the one permitted separator, "
                     "a run whose post-separator part is empty) and four that must "
                     "be refused (a non-colon forbidden separator inside the run, "
                     "a second forbidden separator, two separator colons, an empty "
                     "leading run). If the acceptance predicate refused every "
                     "well-formed run the first three conjuncts would fail => "
                     "PRECOND-TOO-STRONG; if it accepted everything the last four "
                     "would. The impl is byte-identical and the `have` is cleared, "
                     "so the frozen obligation still discharges on its own terms.",
    },

    # =====================================================================
    # UNIQUENESS / SPEC-TOO-WEAK rivals — wrong impls sharing the frozen spec
    # that MUST be rejected, each a loop-free closed form with a machine-checked
    # refutation witness at a concrete input and the refinement argument for why
    # its faithful real counterpart would NOT resolve the failing test.
    # =====================================================================

    # ---- COLON-COUNT clause: drop the `colons ≤ 1` conjunct ----
    {
        "id": "weak-drop-colon-guard",
        "kind": "uniqueness",
        "expect": "reject",
        # Keep the body and leading-colon checks but drop the at-most-one-colon
        # guard: any run with two or more separator colons is wrongly accepted.
        "module": _rival(
            "match seg with | [] => false "
            "| c :: cs => bodyOk (c :: cs) && (c.toNat != 58)"),
        "refinement": "dropping the at-most-one-separator guard accepts a "
                      "segment carrying two or more separators (the body fold "
                      "permits the separator, so nothing else rejects it), which "
                      "the narrowed matcher rejects — it allows only a single "
                      "optional separator introducing the second run. A faithful "
                      "counterpart that omitted the separator-count bound would "
                      "still accept a multi-separator authentication segment that "
                      "the failing tests now require to be rejected, so it would "
                      "NOT resolve.",
        "rationale": "REJECT from `ok = accepts seg` (COLON-COUNT half): with the "
                     "`colons seg ≤ 1` conjunct dropped, a run with ≥2 separators "
                     "satisfies the rival but not `accepts`. Refuted at "
                     "`['a', ':', 'b', ':', 'c']` (two separators): the rival "
                     "returns true, `accepts` returns false. Varies `seg` to a "
                     "multi-separator run.",
        "witness": _witness("['a', ':', 'b', ':', 'c']"),
    },

    # ---- BODY clause: only whitespace excluded (the pre-narrowing behaviour) ----
    {
        "id": "weak-whitespace-only",
        "kind": "uniqueness",
        "expect": "reject",
        # The body predicate accepts every code point that is not whitespace (and
        # the separator colon), so the two OTHER forbidden separators (64, 47) are
        # wrongly treated as authentication characters.
        "module": _rival(
            "match seg with | [] => false "
            "| c :: cs => (c :: cs).all (fun ch => !isWhitespace ch || ch.toNat == 58) "
            "&& colons (c :: cs) ≤ 1 && c.toNat != 58"),
        "refinement": "excluding only whitespace from the body (the pre-narrowing "
                      "behaviour) treats the two other forbidden separators as "
                      "acceptable inside the segment, so a segment containing them "
                      "un-encoded is accepted — exactly the class of segment the "
                      "narrowed body now forbids. A faithful counterpart keeping "
                      "the whitespace-only body still accepts such segments (the "
                      "example from the issue among them), which the failing tests "
                      "require to be rejected, so it would NOT resolve.",
        "rationale": "REJECT from `ok = accepts seg` (BODY half): the "
                     "whitespace-only body admits code point 47, which `isUchar` "
                     "(hence `bodyOk`) excludes. Refuted at `['f', 'o', 'o', '/', "
                     "'b']` (contains code point 47): the rival returns true, "
                     "`accepts` returns false. Varies `seg` to a run carrying a "
                     "non-colon forbidden separator inside the body.",
        "witness": _witness("['f', 'o', 'o', '/', 'b']"),
    },

    # ---- LEADING clause: drop the leading-separator guard ----
    {
        "id": "weak-leading-colon",
        "kind": "uniqueness",
        "expect": "reject",
        # Drop the `seg[0].toNat != 58` conjunct, so a run that BEGINS with the
        # separator (empty leading run) is wrongly accepted.
        "module": _rival(
            "match seg with | [] => false "
            "| c :: cs => bodyOk (c :: cs) && colons (c :: cs) ≤ 1"),
        "refinement": "dropping the leading-separator guard accepts a run that "
                      "begins with the separator — i.e. an EMPTY leading "
                      "authentication run — which the narrowed matcher rejects (the "
                      "leading run is mandatory, one-or-more not zero-or-more). A "
                      "faithful counterpart that admitted a leading separator would "
                      "accept a segment with no leading run, which the failing "
                      "tests require to be rejected, so it would NOT resolve.",
        "rationale": "REJECT from `ok = accepts seg` (LEADING half): with the "
                     "`seg[0].toNat != 58` conjunct dropped, a single-separator run "
                     "has `bodyOk = true` and `colons = 1 ≤ 1`, so the rival "
                     "returns true while `accepts` returns false. Refuted at "
                     "`[':']` — a run whose first code point is the separator. "
                     "Varies `seg` to a leading-separator run of length one.",
        "witness": _witness("[':']"),
    },

    # ---- NON-EMPTY clause: accept the empty run ----
    {
        "id": "weak-accept-empty",
        "kind": "uniqueness",
        "expect": "reject",
        # Drop the non-empty guard: `bodyOk [] = true`, `colons [] = 0 ≤ 1`, and
        # the leading check is vacuous on `[]`, so the empty run is wrongly
        # accepted (the frozen spec / gold impl reject it).
        "module": _rival(
            "bodyOk seg && colons seg ≤ 1 "
            "&& (match seg with | [] => true | c :: _ => c.toNat != 58)"),
        "refinement": "accepting the empty run drops the mandatory-leading-run "
                      "requirement (the leading run is one-or-more), so an "
                      "authentication segment with no characters at all is "
                      "accepted, which the narrowed matcher rejects. A faithful "
                      "counterpart that admitted an empty segment would accept a "
                      "malformed authentication group the failing tests require to "
                      "be rejected, so it would NOT resolve.",
        "rationale": "REJECT from `ok = accepts seg` (NON-EMPTY half): `accepts [] "
                     "= false`, but the rival's guards all hold on `[]` "
                     "(`bodyOk [] = true`, `colons [] = 0 ≤ 1`, leading check "
                     "vacuous), so it returns true. Refuted at the empty run "
                     "`([] : List Char)` — varies `seg` to length zero, the one "
                     "input the other three rivals never probe.",
        "witness": _witness("([] : List Char)"),
    },

    # ---- BODY clause, NON-ASCII half: only the ASCII whitespace run excluded ----
    # Added by the audit. `weak-whitespace-only` above attacks the body predicate
    # only through a non-colon forbidden separator (code point 47); nothing in the
    # battery probed the OTHER half of `isUchar`, the whitespace class itself, so a
    # body predicate that excluded merely the ASCII run {9..13, 32} and admitted
    # all 23 non-ASCII whitespace code points went unattacked. `isWhitespace`
    # enumerating the FULL Unicode class is a load-bearing claim of the deep model
    # (mapping.md §3.1 calls the equivalence "universal, not ASCII-only"), so it
    # needs its own rival.
    {
        "id": "weak-ascii-whitespace-only",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _rival(
            "match seg with | [] => false "
            "| c :: cs => (c :: cs).all (fun ch => "
            "(!((9 ≤ ch.toNat && ch.toNat ≤ 13) || ch.toNat == 32) "
            "&& ch.toNat != 58 && ch.toNat != 64 && ch.toNat != 47) "
            "|| ch.toNat == 58) "
            "&& colons (c :: cs) ≤ 1 && c.toNat != 58"),
        "refinement": "narrowing the excluded whitespace class to its ASCII run "
                      "alone admits every non-ASCII whitespace code point inside "
                      "the segment, so a run carrying one is accepted while the "
                      "narrowed matcher rejects it — the matcher's whitespace "
                      "class is Unicode-aware, not ASCII-only. A faithful "
                      "counterpart that checked only ASCII whitespace would still "
                      "accept an authentication segment containing a non-ASCII "
                      "whitespace code point, which the failing tests require to "
                      "be rejected, so it would NOT resolve.",
        "rationale": "REJECT from `ok = accepts seg` (BODY half, whitespace side): "
                     "the ASCII-only body admits code point 0xa0, which "
                     "`isWhitespace` (hence `isUchar`, hence `bodyOk`) excludes. "
                     "Refuted at `['a', '\\u00a0', 'b']`: the rival returns true, "
                     "`accepts` returns false. Varies `seg` to a run carrying a "
                     "NON-ASCII whitespace code point — the half of `isUchar` no "
                     "other rival probes.",
        "witness": _witness("['a', '\\u00a0', 'b']"),
    },

    # ---- OVER-STRICT direction: the separator made MANDATORY ----
    # Added by the audit. Every rival above is a spec-too-WEAK probe (it accepts a
    # run `accepts` rejects), so the whole reject lane pushed in one direction and
    # a rival that REFUSES a well-formed run — the failure mode a narrowing change
    # is most likely to introduce by accident — was never tested. This one turns
    # the optional separator into a required one, so a bare authentication run with
    # no separator at all is refused.
    {
        "id": "weak-separator-mandatory",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _rival(
            "match seg with | [] => false "
            "| c :: cs => bodyOk (c :: cs) "
            "&& colons (c :: cs) == 1 && c.toNat != 58"),
        "refinement": "requiring exactly one separator instead of at most one "
                      "makes the second run MANDATORY, so a segment that is a "
                      "bare authentication run with no separator is refused — the "
                      "narrowed matcher accepts it (the separator group is "
                      "optional, zero-or-one not exactly-one). A faithful "
                      "counterpart that made the separator mandatory would reject "
                      "authentication segments the validator must keep accepting, "
                      "breaking the currently-passing tests rather than resolving "
                      "the failing ones — verify-not-resolve in the OVER-strict "
                      "direction.",
        "rationale": "REJECT from `ok = accepts seg` (COLON-COUNT clause, upper "
                     "side): `accepts` bounds the separator count ABOVE (≤ 1) and "
                     "not below, so a separator-free run satisfies `accepts` but "
                     "not the rival's `== 1`. Refuted at `['a', 'b']`: the rival "
                     "returns false, `accepts` returns true. The ONLY rival here "
                     "that is wrong by being too STRICT — every other reject case "
                     "is a too-weak probe, so without it the lane tests one "
                     "direction of the clause only.",
        "witness": _witness("['a', 'b']"),
    },
]


# ---------------------------------------------------------------------------
# Nagini -> velvet accounting. The sibling battery has 7 SPEC cases (2 soundness
# positives, 1 admissibility, 1 frame-mutation rival, 3 partial-domain rivals)
# plus a 1-case AXIOM lane. This bundle models the SAME purely-functional core —
# whether an authentication segment is accepted — over the SAME carrier shape
# (`List Char`, a backward per-code-point fold), so the two positive controls and
# the three partial-domain rivals port near 1:1; the frame case is genuinely
# vacuous, the admissibility case is vacuous, and one rival is ADDED to cover the
# non-empty clause the sibling folds into its length guard.
#
#   sibling case                  -> here                       disposition
#   ---------------------------------------------------------------------------
#   pos-control-reorder           -> pos-control-reorder         PORTED
#   pos-control-direct            -> pos-control-direct          PORTED
#   admiss-selfcall               -> admiss-f2p-accepts-         RE-AIMED
#                                    satisfiable                 (audit)
#   frame-mutate-seg              -> (none)                      VACUOUS
#   weak-drop-colon-guard         -> weak-drop-colon-guard       PORTED
#   weak-whitespace-only          -> weak-whitespace-only        PORTED
#   weak-leading-colon            -> weak-leading-colon          PORTED
#   (no sibling)                  -> weak-accept-empty           ADDED
#   (no sibling)                  -> weak-ascii-whitespace-only  ADDED (audit)
#   (no sibling)                  -> weak-separator-mandatory    ADDED (audit)
#   AXIOM_TESTS (1)               -> (none)                      DROPPED (G-AX)
#
# 5 ported, 1 re-aimed, 3 added, 1 vacuous, 1 dropped = 9 SPEC cases
# (2 soundness, 1 admissibility, 6 uniqueness).
#
# PORTED (2 positive controls): the sibling's branch-reorder splits the gold
#   `if colon / elif not-uchar` into two independent guarded statements; here the
#   analogous reshape splits the same discriminating step into two independent
#   guarded ifs (the second guarded by `c != 58`), keeping every loop invariant
#   byte-identical, so the frozen proof closes with no retune. The sibling's
#   direct control (`return accepts(ToSeq(seg))`) ports as `return accepts seg`;
#   the loop is gone, so its residual goal closes under `loom_solve` alone. Both
#   verified to build.
# PORTED (3 partial-domain rivals): drop-colon-guard, whitespace-only, and
#   leading-colon re-express DIRECTLY onto the corresponding conjunct of
#   `accepts` — the at-most-one-separator bound, the body predicate (only
#   whitespace excluded == the pre-narrowing behaviour), and the leading-separator
#   guard. Each refinement argument carries over: a faithful counterpart with that
#   defect still accepts a segment the narrowed matcher rejects (a multi-separator
#   run, a run carrying a non-colon forbidden separator, a run with an empty
#   leading run), so it would NOT resolve the failing tests.
# ADDED (1): weak-accept-empty attacks the NON-EMPTY clause (`accepts [] =
#   false`). The nagini sibling folds this into an early `if n == 0: return False`
#   length guard rather than a separate rival, but here the single `ok = accepts
#   seg` clause pins non-emptiness independently, so a rival that drops the
#   non-empty guard (accepting `[]`) is a real spec-strength probe and is the ONLY
#   witness at the length-zero input.
# RE-AIMED (admiss-selfcall -> admiss-f2p-accepts-satisfiable): the sibling
#   self-calls on an F2P-shaped input to prove the precondition
#   `Acc(list_pred(seg), 1/2)` admits it. This bundle declares no `require`
#   clause, so there is no permission precondition to admit — but "no
#   precondition" is NOT a reason to drop the lane, and the audit corrected an
#   earlier disposition that said so. On a total carrier the analogue is the
#   obligation being UNSATISFIABLE, or degenerate, at an F2P-shaped input, and
#   that is a real risk here even with a total post-image: `accepts` being defined
#   everywhere does not make it non-degenerate, since a predicate that refused
#   every well-formed run (or accepted every malformed one) is equally total. The
#   re-aimed case discharges `accepts` BY EVALUATION at seven concrete F2P-shaped
#   runs — three that must be accepted, four that must be refused — as a `have`,
#   before closing the frozen obligation verbatim, so it pins satisfiability in
#   both directions. Liveness confirmed with a real build: one conjunct flipped to
#   a false claim makes the file fail.
# VACUOUS (frame-mutate-seg): the sibling carries this MANDATORY because `seg` is
#   held at Acc(list_pred(seg), 1/2) and a rival can illegally store into it. This
#   backend is referentially transparent and declares no `mut` binder — `seg` is
#   an immutable value with no heap footprint — so there is no read-only input to
#   overwrite and no substitute probe. Not fabricated.
# AXIOM_TESTS: dropped. The axiom lane is G-AX's job (axiom_check.py validates the
#   deep A-reference `accepts` == the real compiled matcher); this bundle consumes
#   no axiom `ensures`, and the gate ignores AXIOM_TESTS regardless.
#
# BINDER / CLAUSE COVERAGE. The obligation has a single input binder,
#   `seg : List Char`, and a single top-level clause, `ok = accepts seg`, with
#   four independent sub-obligations (non-empty, body, colon-count, leading). The
#   six reject witnesses probe six DISTINCT input points — `[]` (non-empty),
#   `['f','o','o','/','b']` (body, forbidden separator 47), `['a',' ','b']`
#   (body, non-ASCII whitespace), `['a',':','b',':','c']` (colon-count, upper
#   bound), `['a','b']` (colon-count, NO lower bound), `[':']` (leading
#   separator) — so `seg` is varied in length (0, 1, 2, 3, 5) and contents, and
#   every sub-obligation is attacked. Two of the six pushed directions the earlier
#   battery did not: the whitespace half of `isUchar` (as opposed to its forbidden
#   separators) and the OVER-strict direction (a rival wrong by refusing a
#   well-formed run rather than by accepting a malformed one). The two positive
#   controls plus the admissibility case defend the whole obligation. No two
#   rivals are refuted at the same input. pts = 6 distinct input points.
# WITNESS DISCRIMINATION — re-derived by the audit with real builds, four per
#   reject case, and the earlier claim was found to be too weak. Each witness
#   ELABORATES against its loop-free rival (exit 0) and FAILS against the
#   discriminating subject (exit 1). For five of the six cases that subject is the
#   `pos-control-direct` positive rather than the frozen solution: gold's
#   un-normalised `forIn Lean.Loop.mk` term makes `Decidable` unsynthesizable for
#   ANY claim at those inputs, so gold's exit code carries no information there
#   (only the `[]` case decides on gold, since `accepts []` reduces without
#   entering the loop). The gate re-checks that subject shares the frozen spec and
#   VERIFIES before using it. And the closing tactic is `all_goals decide`, not a
#   bare `decide`, because a bare one made the exit code claim-independent — see
#   the module docstring and `_witness`. Per case, the FORGERY pair now
#   distinguishes: the flipped `=` claim exits 1 on the rival and 0 on the subject,
#   the exact mirror of the real witness, and a forgery at an agreement point exits
#   0 on both so it cannot clear the check. No witness binds a hypothesis (the
#   carrier is fully transparent), so there is no joint-satisfiability obligation.
#   No `sorry`/`admit`/`native_decide`/`axiom` appears.
# SPEC-STRENGTH PROBES the audit ran and the spec SURVIVED (attacks D and E; not
#   shipped as cases, recorded so the next reader knows they were tried). Five NEW
#   wrong impls beyond the six above were built and all were rejected: the two
#   landed here, plus a body admitting code point 64, a colon bound loosened to
#   ≤ 2, and a leading guard testing the LAST code point instead of the first. Two
#   NEW correct reshapes were built and both VERIFY, so the single clause is not
#   over-fit: a `List.all`-based body with an inline induction lemma replacing the
#   `bodyOk` fold, and the three conjuncts permuted (separator bound first).
# DIVERGENCE / NON-TERMINATION -- CLOSED BY THE SEMANTICS, and re-measured rather
#   than argued. An earlier revision of the line above deferred this lane as "the
#   `partial` termination lane", a known and already escalated spec hole. That is
#   withdrawn on both counts. This bundle sets
#   `set_option loom.semantics.termination "total"` and opens `TotalCorrectness`,
#   as do all 500 velvet bundles (none sets `partial`), and the `set_option`
#   elaborator itself runs `openScope `TotalCorrectness`
#   (`Loom/MonadAlgebras/WP/Options.lean:169-186`), so the two lines cannot
#   disagree. Under `total` a postcondition is claimed of ALL runs rather than only
#   terminating ones, so the verifier demands a decreasing measure on every loop
#   AND discharges its descent. Measured on this cell: a loop that CARRIES a
#   measure its body never changes (`let mut q : Nat := 1; while q > 0 /
#   invariant 0 <= q / done_with q = 0 / decreasing q do q := q`) spliced at the
#   impl anchor, proof reduced to a bare `loom_solve`, is REJECTED at exit 1 on the
#   measure's own goal: `case «decreasing_1: q»`, residual `q < q`. That shape is
#   the decisive one, since a measure-less loop could be dismissed as tripping only
#   the annotation linter. So a diverging rival is rejected and no hole is open. No
#   reject case is shipped for the class, for a witness-contract reason rather than
#   a spec one: the refusal fires on the `method` command, so the rival's module
#   never compiles and the witness the gate builds from it cannot elaborate, which
#   records `witness-unproven` (INCONCLUSIVE, forcing MALFORMED-TESTS).
AXIOM_TESTS = []
