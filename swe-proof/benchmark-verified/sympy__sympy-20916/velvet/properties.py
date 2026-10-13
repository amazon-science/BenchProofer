"""properties.py — G-PBT falsification battery for sympy__sympy-20916 (velvet).

NOT a Velvet module; a record of adversarial cases the G-PBT gate executes.
Each SPEC case is a full ``Solution.lean`` variant that shares the FROZEN spec
byte-for-byte (region surgery: only text inside the ``-- impl-start`` /
``-- impl-end`` region, or inside the ``prove_correct`` tactic body, is changed,
both of which the consumer spec view elides — so ``markers.same_spec`` holds and
the ``prove_correct splitTrailingDigits`` obligation survives with a
byte-identical statement) and swaps in a candidate implementation; it is checked
by the real verifier. ``expect:"verify"`` passes iff (in scope AND verifies);
``expect:"reject"`` passes iff (in scope AND does NOT verify AND its refutation
``witness`` discriminates: the witness must ELABORATE against the rival and FAIL
against the frozen solution, with jointly-satisfiable hypotheses).

DEFENDED SURFACE (``splitTrailingDigits (name : List Char) return (out : List
Char × Option (List Char))``): given a parsed base name, peel off a trailing
block of decimal digits as a subscript when the name — after setting aside at
most one final newline — is a non-empty run of letter code points immediately
followed by a non-empty run made up ENTIRELY of decimal-digit code points.
There is ONE input binder, ``name``, no ``require`` clause (the domain is
total), and ONE ``ensures`` clause:

    (P) ensures out = peelDigits name

``peelDigits`` is a pure ``def`` of the input alone:

    letters := letterPrefix name              -- maximal leading letter run
    rest    := afterLetters name              -- the remainder
    digits  := stripFinalNewline rest         -- rest with ≤1 final newline set aside
    out     := if letters ≠ [] ∧ digits ≠ [] ∧ digits.all isDigitU
               then (letters, some digits)    -- ACCEPT: split off the digit block
               else (name, none)              -- REJECT: name returned whole

So P pins ``out`` to an equality against a fully-unfolded function of ``name``.
The clause has three independent acceptance conjuncts (a non-empty letter run;
a non-empty tail; the tail is all decimal digits) and two mutually-exclusive
output shapes (the split pair on accept; the whole name paired with ``none`` on
reject). A rival is refutable when it disagrees with peelDigits on some
sub-region of ``name``.

THE CARRIER IS AN OPAQUE-AXIOM ORACLE. The per-code-point classifiers
``isLetterU`` / ``isDigitU`` are ``axiom``s with NO computational content and
only three structural facts asserted (disjointness; the underscore is neither),
and ``letterPrefix`` / ``afterLetters`` are ``noncomputable`` (they fold over
``isLetterU``). The method itself is ``noncomputable``. So there is NO executable
content: the tester+``decide`` route (``derive_tester_for`` →
``…Tester args = false``) is UNAVAILABLE (extraction fails with "no executable
code"), and a ``decide`` on a concrete literal gets stuck the instant it meets
``letterPrefix``/``isDigitU``. That does NOT make the reject lane empty. An
opaque term has no VALUE to compute, but it is still a term one can QUANTIFY
over. Every reject rival below is refuted by CONDITIONING ON THE CARRIER: the
Hoare triple is refuted DIRECTLY at a symbolic ``name`` described by hypotheses
on ``letterPrefix name`` / ``stripFinalNewline (afterLetters name)`` — the very
observations peelDigits branches on — so the refutation holds exactly on the
sub-region where the rival diverges from the spec (a STRONGER statement than any
single literal input could make). ``rw [triple, wp_pure]; simp only
[loomLogicSimp]`` reduces the method's WP to the returned pair, after which the
hypotheses drive the ``if`` in both peelDigits and the rival to the branch the
witness attacks. Each witness was SEEN to discriminate with real ``lake``
builds: it ELABORATES against the rival (EXIT 0) and FAILS against the frozen
solution (EXIT ≠ 0), and its hypotheses are jointly satisfiable (the
``example … : False`` consistency probe leaves ``False`` unsolved), so none is a
contradiction-forgery.

WITNESS TAIL DISCIPLINE (imposed by audit; ACTUALLY ENFORCED as of audit a6 —
the previous revision asserted this of all four tails while ``_W_NEVER`` still
carried an explicit ``rw [if_pos ⟨h1, h2, h3⟩]``, so the paragraph was false of
the battery it described. That tail did discriminate, but it has been converted
for the reason below and the claim is now true of all four). Every tail closes by
feeding the hypotheses to ``simp`` (``simp [h1, h2, h3]``) rather than by naming
a branch with an explicit ``rw [if_pos …] / rw [if_neg …]`` and then
hand-finishing with ``absurd``/``Prod.mk.injEq``. The two forms are equally
accepted by the gate —
both make the rival build succeed and the gold build fail — but they fail on
gold for DIFFERENT REASONS, and only one of them is a discriminator. The
explicit-``rw`` forms were measured failing on gold with ``Application type
mismatch`` on an ``if_pos ⟨h1, h2⟩`` whose arity matched the RIVAL's guard,
``Tactic 'rewrite' failed: did not find an occurrence of the pattern if …``
(gold had already discharged both branches, so the second ``rw`` had no ``if``
left), and ``Invalid field 'symm': the environment does not contain
'True.symm'`` (gold's goal had collapsed to ``True``). Each of those is a
SYNTACTIC accident of the tactic script — a missing projection, an exhausted
rewrite, a guard-shape mismatch — not a statement that gold satisfies the spec,
and the gate cannot tell the difference. The hypothesis-driven tails make all
four gold builds fail as ``unsolved goals … ⊢ False``: the semantic reading
"gold does not violate P at this point", which is what the discrimination check
is supposed to establish.

ADVERSARIAL READ of the nagini classes on this carrier:
  * FRAME / PERMISSION-MUTATION — VACUOUS. The nagini sibling carries a MANDATORY
    frame-mutation rival (write to the read-only ``name[0]`` under a half
    permission ``Acc(list_pred(name),1/2)``) because its input is held at a
    fractional heap permission an impl can illegally WRITE. Lean and Velvet are
    referentially transparent: ``name`` is an immutable value, this bundle
    declares NO ``mut`` binder, there is no heap and no aliasing — so there is no
    read-only input to overwrite and no substitute probe to build. Not
    fabricated (per the porting map: this class is vacuous on Lean/Velvet).
  * PARTIAL-DOMAIN / VALUE rivals — the nagini uniqueness rivals live here, each
    right on part of the domain and diverging on a sub-region of the ONE clause.
    They PORT: each is re-expressed against the frozen spec and refuted by
    conditioning on the carrier at the exact observations where the rival's
    returned pair differs from ``peelDigits name``. See the ``weak-*`` cases.
  * UNGROUNDED-ORACLE ECHO — N/A as an ATTACK. peelDigits is a fully-unfolded
    function of the method's own input (echoing it here == doing the actual
    per-code-point work); the only opaque leaves are ``isLetterU``/``isDigitU``,
    validated executably by G-AX (axiom_check.py), not answer-key markers to
    echo. We carry honest cheapest-reshape POSITIVE CONTROLS instead.

DIVERGENCE LANE — measured during audit a6, because the frozen file sets
``set_option loom.semantics.termination "total"`` and under THAT setting a
diverging rival is genuinely rejected, so silence about the class would be an
under-port rather than a non-issue. The previous revision said nothing about it.
Findings, with real builds:

  * The rival IS rejected. A body that keeps the correct returned value but wraps
    it in an unbounded ``while i < 1 do i := 0`` (no decreasing measure) fails at
    exit 1 with ``Decreasing annotations are required in total correctness
    semantics``, plus ``Failed to prove assertion without names: WPGen (forIn
    Lean.Loop.mk …)``. So the termination obligation is live and the spec really
    does exclude a diverging impl — this is NOT a spec hole.
  * But it CANNOT SHIP as a reject case here, for a mechanical reason rather than
    a spec one. The gate requires a reject case's witness to ELABORATE against the
    rival, and ``witness_file`` strips only the ``prove_correct`` block — the
    ``Decreasing annotations`` error is raised at the METHOD BODY (the impl
    region), which survives that stripping. So the rival-side witness build fails
    (exit 1) no matter what the witness claims: measured, the witness above gives
    rival exit 1 and gold exit 1, i.e. the half that must SUCCEED cannot. The gate
    would record ``witness-unproven`` (inconclusive ⇒ MALFORMED-TESTS), which is
    strictly worse than an honest recorded note.

  Disposition: recorded as a KNOWN CARRIER LIMITATION of the witness harness on
  total-semantics bundles, not as a vacuous class and not as a spec hole. The
  termination obligation is confirmed load-bearing by the build above; what is
  missing is only the ability to attach a discriminating witness to it, because a
  non-terminating variant makes its own module uncompilable by construction. A
  ``witness_reference`` does not help either: the reference must VERIFY, and it is
  the RIVAL build that fails here, not the gold-side one.

AXIOM lane: dropped. ``AXIOM_TESTS = []``. The nagini file carries an
axiom-soundness probe (the letter/digit classes are disjoint) and an
axiom-containment / A-reference probe (the deep split model equals the real
regex); both are G-AX's job (axiom_check.py / mapping.md §3), and the G-PBT gate
ignores ``AXIOM_TESTS`` regardless.
"""
from pathlib import Path

INSTANCE = "sympy__sympy-20916"
BACKEND = "velvet"

_BASE = (Path(__file__).parent / "Solution.lean").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# ---- impl-region anchor: the WHOLE frozen impl body (the four `let`s and the
# ---- return). It lies wholly inside the single -- impl-start .. -- impl-end
# ---- region and is unique in Solution.lean (both facts asserted at load by
# ---- _swap), so each edit keeps same_spec by construction and leaves the frozen
# ---- `prove_correct` statement intact.
_IMPL = (
    "    let letters := letterPrefix name\n"
    "    let rest := afterLetters name\n"
    "    let digits := stripFinalNewline rest\n"
    "    let out : List Char × Option (List Char) :=\n"
    "      if letters ≠ [] ∧ digits ≠ [] ∧ digits.all isDigitU then (letters, some digits)\n"
    "      else (name, none)\n"
    "    return out"
)
assert _BASE.count(_IMPL) == 1, "splitTrailingDigits impl region drifted from expected text"


def _impl(new_impl):
    """Full Solution.lean with ONLY splitTrailingDigits' impl-region body replaced."""
    return _swap(_BASE, _IMPL, new_impl)


# ---- ADMISSIBILITY scaffolding. The frozen `prove_correct` block, and the
# ---- retuned form that additionally clears the in-region assert goal. Both the
# ---- impl region and the tactic body are elided from the consumer spec view, so
# ---- swapping either keeps same_spec and leaves the frozen `ensures` statement
# ---- byte-identical.
_PROOF = "prove_correct splitTrailingDigits by\n  loom_solve"
assert _BASE.count(_PROOF) == 1, "prove_correct block drifted from expected text"

# The concrete evaluable point: a single underscore. `underscore_not_letter`
# makes `letterPrefix ['_'] = []`, so the first acceptance conjunct fails and
# peelDigits returns the name whole. Nothing here needs the classifiers to have
# computational content — only the two structural underscore axioms.
_ADMISS_ASSERT = (
    "    assert (with_name_prefix `admiss\n"
    "      (peelDigits ['_'] = (['_'], none)))\n"
)
_ADMISS_PROOF = (
    "prove_correct splitTrailingDigits by\n"
    "  loom_solve\n"
    "  all_goals first\n"
    "    | rfl\n"
    "    | (unfold peelDigits letterPrefix afterLetters stripFinalNewline\n"
    "       simp [List.takeWhile, List.dropWhile, underscore_not_letter])"
)


# ---- WITNESS preamble. The spec is a `method` CONTRACT over an opaque,
# ---- non-computable carrier, so a witness cannot go through the tester
# ---- machinery (extraction fails on `letterPrefix`/`isDigitU`, which have no
# ---- executable code). Each witness instead refutes the method's Hoare triple
# ---- DIRECTLY at a symbolic `name` described by hypotheses on the carrier
# ---- observations peelDigits branches on. `rw [triple, wp_pure]` reduces the
# ---- method's weakest-precondition to `<returned pair> = peelDigits name`;
# ---- `simp only [loomLogicSimp]` clears the `True ≤ ·`; the hypotheses then
# ---- drive both `if`s to the attacked branch. The reduction lemmas (`triple`,
# ---- `wp_pure`, `loomLogicSimp`) all come from the frozen `Velvet.Std` import,
# ---- so nothing extra is imported. Checked in a file whose `prove_correct`
# ---- block has been stripped, so no tactic script can mask the verdict.
def _wit(head_hyps, tail):
    hyp_lines = "".join(f"\n    ({h})" for h in head_hyps)
    return (
        f"example (name : List Char){hyp_lines} :\n"
        "    ¬ triple (l := Prop) True (splitTrailingDigits name)\n"
        "        (fun out => out = peelDigits name) := by\n"
        "  unfold splitTrailingDigits\n"
        "  rw [triple, wp_pure]\n"
        "  simp only [loomLogicSimp]\n"
        "  unfold peelDigits\n"
        + tail
    )


# --- weak-never-split: ignore the trailing-digit exception entirely and return
#     the name whole (the pre-fix shape: an ASCII-only recognizer never matches a
#     Unicode-letter name, so it never peels). Refuted on the ACCEPT sub-region
#     (all three conjuncts hold) where the spec splits but the rival does not.
#     TAIL SHAPE (audit a6): was `rw [if_pos ⟨h1, h2, h3⟩]; simp`, the ONE tail
#     that did not obey the discipline the docstring claims for all four. It did
#     discriminate (rival 0, gold 1 as `unsolved goals … ⊢ False`), so this is a
#     consistency repair rather than a hollow-case repair — but the replacement is
#     strictly better evidence under the forgery test. With the explicit `rw`, the
#     flipped-claim forgery (drop the `¬`, i.e. assert gold IS correct here) failed
#     with `No goals to be solved`; with the hypothesis-driven tail the forgery
#     VERIFIES (exit 0). A forgery that verifies is the strongest available proof
#     that gold's exit code tracks the CLAIM and not the tactic script.
_W_NEVER = _wit(
    ["h1 : letterPrefix name ≠ []",
     "h2 : stripFinalNewline (afterLetters name) ≠ []",
     "h3 : (stripFinalNewline (afterLetters name)).all isDigitU = true"],
    "  simp [h1, h2, h3]\n")

# --- weak-drop-digit-guard: peel whenever there is a non-empty letter run and a
#     non-empty tail, WITHOUT checking the tail is all decimal digits. Refuted on
#     the sub-region where the tail is non-empty but NOT all digits: the spec
#     REJECTS (returns the name whole, `none`) yet the rival ACCEPTS (returns the
#     split pair with `some`).
#     TAIL SHAPE (audit): the tail closes with `simp [h1, h2, h3]`, which drives
#     BOTH `if`s from the hypotheses rather than naming a branch with an explicit
#     `rw [if_pos …]`. That matters for what the GOLD-side failure means. With
#     the explicit `rw`, gold failed on an `if_pos ⟨h1, h2⟩` ARITY mismatch (the
#     frozen guard has three conjuncts, the rival's two) — a SYNTACTIC error
#     about the rival's guard shape, which discriminates for a reason unrelated
#     to the spec. Hypothesis-driven `simp` makes gold fail as `unsolved goals
#     … ⊢ False`: the semantic statement that gold does NOT violate P here.
_W_DIGITGUARD = _wit(
    ["h1 : letterPrefix name ≠ []",
     "h2 : stripFinalNewline (afterLetters name) ≠ []",
     "h3 : (stripFinalNewline (afterLetters name)).all isDigitU = false"],
    "  simp [h1, h2, h3]\n")

# --- weak-empty-bare: always return an empty bare name paired with `none`.
#     Refuted on the REJECT sub-region (no trailing digit block, so the spec
#     returns the name whole) at any NON-EMPTY name: the spec returns
#     `(name, none)` and the rival `([], none)`.
#     TAIL SHAPE (audit): closes with `simp [hd, hn]` rather than an explicit
#     `rw [if_neg …]` + `absurd hnil.symm hn`. The explicit form made gold fail
#     with `Invalid field 'symm': the environment does not contain 'True.symm'`
#     — on gold the goal had already collapsed to `True`, so the script broke on
#     a MISSING PROJECTION, not on gold satisfying the spec. Driving the branch
#     from `hd` instead yields the semantic gold failure `unsolved goals … ⊢ False`.
_W_EMPTY = _wit(
    ["hd : stripFinalNewline (afterLetters name) = []",
     "hn : name ≠ []"],
    "  simp [hd, hn]\n")

# --- weak-untrimmed-bare: on ACCEPT, pair the WHOLE name (not the leading letter
#     run) with the digit block. Gets the accept/reject dispatch and the digit
#     block right, but returns the wrong bare name. Refuted on the ACCEPT
#     sub-region where the name is more than just its leading letter run
#     (`name ≠ letterPrefix name`, i.e. a non-empty digit tail is present).
#     TAIL SHAPE (audit): closes with `simp [h1, h2, h3, hbare]`. The explicit
#     `rw [if_pos …, if_pos …]` form failed on gold with `Tactic 'rewrite'
#     failed: did not find an occurrence of the pattern if ?m … ?m` — on gold
#     both branches had already been discharged, so the SECOND `rw` had no `if`
#     left to rewrite. That is a syntactic exhaustion of the tactic, not a
#     statement about the spec. The hypothesis-driven form fails on gold as
#     `unsolved goals … ⊢ False`, which is the semantic refutation.
_W_UNTRIMMED = _wit(
    ["h1 : letterPrefix name ≠ []",
     "h2 : stripFinalNewline (afterLetters name) ≠ []",
     "h3 : (stripFinalNewline (afterLetters name)).all isDigitU = true",
     "hbare : name ≠ letterPrefix name"],
    "  simp [h1, h2, h3, hbare]\n")

# --- CONJUNCT-1 RIVAL (`letters ≠ []` dropped): NOT SHIPPED. Re-derived
#     independently during audit and the port's disposition is CONFIRMED, on
#     re-measured evidence. The rival (accept whenever the tail is a non-empty
#     all-digit block, even with an EMPTY letter run) IS landable on this
#     carrier: conditioning on `letterPrefix name = [] ∧ digits ≠ [] ∧
#     digits.all isDigitU`, the witness elaborates against the rival (exit 0)
#     and fails on the frozen solution as `unsolved goals … ⊢ False` (exit 1),
#     with its consistency probe leaving `False` unsolved (exit 1). So the
#     omission is NOT an expressibility gap, and the port did not claim it was.
#     It is not shipped because its REFINEMENT cannot be stated truthfully: the
#     sub-region it attacks is unreachable from the pinned assertion set. Running
#     the unchanged parsing loop over every name the test file pins, the set of
#     post-loop base names that reach this step is
#       {alpha, beta, x, w1, w11, w𝟙, w𝟙𝟙, w𝟙2𝟙, ω1, ω11, ω𝟙, ω𝟙2}
#     and NONE is an all-digit string — every one has a non-empty letter run. So
#     a real recognizer that dropped the letter-run non-emptiness requirement
#     would agree with the gold recognizer on every pinned input and RESOLVE the
#     suite. Shipping it would attach a "would NOT resolve" refinement that is
#     demonstrably false, which is a worse defect than a recorded gap: the spec
#     is simply stricter than the tests on this sub-term (gold's letter group is
#     `+`, not `*`), and that strictness is faithful to the gold behavior but not
#     test-discriminating. Recorded as a live gap: `letters ≠ []` is the one
#     acceptance conjunct no shipped rival attacks.


SPEC_TESTS = [
    # =====================================================================
    # POSITIVE CONTROLS (soundness) — structurally different but CORRECT
    # impls that MUST verify. If a faithful reshape cannot verify, the spec is
    # SPEC-TOO-STRONG. Each keeps the `ensures out = peelDigits name` obligation
    # (byte-identical statement) and only reshapes the executable body; the
    # frozen `loom_solve` proof closes for both.
    # =====================================================================
    {
        "id": "pos-accept-hoisted",
        "kind": "soundness",
        "expect": "verify",
        # Reshape: hoist the acceptance condition into a boolean local `accept`,
        # then branch on it. Same value flow, same returned pair.
        "module": _impl(
            "    let letters := letterPrefix name\n"
            "    let rest := afterLetters name\n"
            "    let digits := stripFinalNewline rest\n"
            "    let accept : Bool := letters ≠ [] ∧ digits ≠ [] ∧ digits.all isDigitU\n"
            "    let out : List Char × Option (List Char) :=\n"
            "      if accept then (letters, some digits)\n"
            "      else (name, none)\n"
            "    return out"),
        "rationale": "hoisting the three-conjunct acceptance test into a boolean "
                     "local and branching on it computes the same pair on every "
                     "input, so `out = peelDigits name` (P) still holds pointwise; "
                     "a correct reshape must verify, else SPEC-TOO-STRONG on the "
                     "shape of the acceptance test.",
    },
    {
        "id": "pos-rest-inlined",
        "kind": "soundness",
        "expect": "verify",
        # Reshape: inline `afterLetters name` into the `digits` binding instead of
        # naming `rest`. Identical value; fewer locals.
        "module": _impl(
            "    let letters := letterPrefix name\n"
            "    let digits := stripFinalNewline (afterLetters name)\n"
            "    let out : List Char × Option (List Char) :=\n"
            "      if letters ≠ [] ∧ digits ≠ [] ∧ digits.all isDigitU then (letters, some digits)\n"
            "      else (name, none)\n"
            "    return out"),
        "rationale": "inlining the remainder-after-letters into the `digits` "
                     "binding leaves the branched-on observations unchanged, so "
                     "the post-image is unchanged and P still discharges; a "
                     "correct reshape must verify.",
    },

    # =====================================================================
    # ADMISSIBILITY — RE-AIMED, then REPAIRED (audit a6). The nagini case builds
    # a concrete F2P-shaped input and asserts the Requires half-permission is
    # establishable for a legitimate caller. This backend has NO `require` clause
    # and NO permissions, so that probe is vacuous, and the port correctly
    # re-aimed it at the residual total-domain risk: the sole post clause being
    # UNSATISFIABLE at the modeled point (a spec no faithful impl can meet reads
    # like a spec every impl meets).
    #
    # But the port discharged that with `module = _BASE` — a BYTE-IDENTICAL copy
    # of the frozen file. That case cannot fail unless the frozen bundle itself
    # is broken: it re-runs the frozen build and calls the exit code evidence
    # about the spec. It tests nothing, and the porting rules name exactly the
    # shape that does: discharge the obligation AT A CONCRETE F2P-SHAPED INPUT,
    # by evaluation, as a `have`/`assert`, BEFORE closing the frozen obligation
    # verbatim.
    #
    # The port's implicit reason for not doing that is the carrier being opaque —
    # `isLetterU`/`isDigitU` are content-free axioms, so no `decide` on a literal
    # reduces. MEASURED FALSE during audit. The axioms assert three STRUCTURAL
    # facts, and two of them (`underscore_not_letter`, `underscore_not_digit`)
    # make the single-underscore name FULLY EVALUABLE without any computational
    # content: `letterPrefix ['_'] = []` (takeWhile stops immediately),
    # `afterLetters ['_'] = ['_']`, `stripFinalNewline ['_'] = ['_']`, so the
    # first acceptance conjunct fails and `peelDigits ['_'] = (['_'], none)` — a
    # closed, proven equation at a concrete point on the REJECT branch. All three
    # component lemmas and the composite were built standalone (exit 0).
    #
    # The assert is LIVE, not decoration: asserting the FALSE claim at the same
    # point (`peelDigits ['_'] = ([], some ['_'])`, i.e. that the name DID split)
    # leaves `case «admiss_1: …» ⊢ False` unsolved and the build fails (exit 1).
    # So this case now has a real pass source and a real failure mode. The impl is
    # kept verbatim so the method's own obligation still discharges; only the
    # tactic body is retuned to clear the extra assert goal, which the consumer
    # spec view elides, so same_spec and the frozen statement are untouched.
    # =====================================================================
    {
        "id": "admiss-satisfiable",
        "kind": "admissibility",
        "expect": "verify",
        "module": _swap(
            _swap(_BASE, _IMPL, _ADMISS_ASSERT + _IMPL),
            _PROOF, _ADMISS_PROOF),
        "rationale": "PASS SOURCE = the sole post clause is SATISFIABLE, and "
                     "satisfied by EVALUATION at a concrete point rather than by "
                     "re-running the frozen build. With no precondition to admit, "
                     "the residual admissibility risk on a total domain is that "
                     "`out = peelDigits name` is unmeetable at the modeled point. "
                     "The in-region assert discharges `peelDigits ['_'] = "
                     "(['_'], none)` — a closed equation at a concrete name on the "
                     "REJECT branch, provable from the underscore axioms alone — "
                     "and the frozen `ensures` still discharges alongside it. A "
                     "false claim at the same point leaves an unsolved goal, so "
                     "the probe has a real failure mode. Else SPEC-UNSATISFIABLE.",
    },

    # =====================================================================
    # UNIQUENESS / SPEC-TOO-WEAK rivals — wrong impls sharing the frozen spec
    # that MUST be rejected. Each carries a machine-checked, jointly-satisfiable
    # refutation witness that CONDITIONS on the opaque carrier at the exact
    # observations where the rival diverges from peelDigits, and the refinement
    # argument for why its faithful real counterpart would NOT resolve the
    # failing test.
    # =====================================================================
    {
        "id": "weak-never-split",
        "kind": "uniqueness",
        "expect": "reject",
        # PARTIAL-DOMAIN: ignore the trailing-digit exception and return the name
        # whole. Correct on every no-split input; wrong on EVERY input that
        # should split. This is the pre-fix behaviour (an ASCII-only recognizer
        # never matches a Unicode-letter name, so it never peels the digit block).
        "module": _impl(
            "    let out : List Char × Option (List Char) := (name, none)\n"
            "    return out"),
        "refinement": "returning the name whole is the base_commit behaviour on "
                      "the failing inputs: the pre-fix recognizer never peels a "
                      "trailing digit block off a Unicode-letter name, so the base "
                      "name keeps its digits and no subscript is split off. On the "
                      "failing F2P inputs (a Greek-letter-plus-digits name) the "
                      "observed decomposition is the whole name with no subscript "
                      "where the test demands the letter run paired with the digit "
                      "block — the exact public defect. It would NOT resolve.",
        "rationale": "REJECT from P (`out = peelDigits name`): on the accept "
                     "sub-region the post-image is `(letters, some digits)` and "
                     "the rival returns `(name, none)`. Refuted by conditioning on "
                     "all three acceptance conjuncts holding — the sub-region the "
                     "whole fix is about — where the two pairs differ in their "
                     "`Option` component.",
        "witness": _W_NEVER,
    },
    {
        "id": "weak-drop-digit-guard",
        "kind": "uniqueness",
        "expect": "reject",
        # PARTIAL-DOMAIN: peel whenever there is a non-empty letter run and a
        # non-empty tail, WITHOUT requiring the tail to be all decimal digits.
        # Correct when the tail happens to be all digits; wrong when the tail
        # contains a non-digit (the name does not actually end in a pure digit
        # block).
        "module": _impl(
            "    let letters := letterPrefix name\n"
            "    let rest := afterLetters name\n"
            "    let digits := stripFinalNewline rest\n"
            "    let out : List Char × Option (List Char) :=\n"
            "      if letters ≠ [] ∧ digits ≠ [] then (letters, some digits)\n"
            "      else (name, none)\n"
            "    return out"),
        "refinement": "a recognizer that split off the tail after the leading "
                      "letter run WITHOUT checking it is entirely decimal digits "
                      "would peel a mixed or non-digit tail as though it were a "
                      "subscript, mangling names the anchored pattern does not "
                      "match into a wrong (base, subscript) pair — corrupting the "
                      "parsed token the surrounding printer consumes and breaking "
                      "the exact-tuple comparisons the tests pin. It would NOT "
                      "resolve.",
        "rationale": "REJECT from P: the acceptance test drops the "
                     "`digits.all isDigitU` conjunct, so on a non-empty tail that "
                     "is NOT all digits the spec REJECTS (`(name, none)`) while "
                     "the rival ACCEPTS (`(letters, some digits)`). Refuted by "
                     "conditioning on `letters ≠ [] ∧ digits ≠ [] ∧ "
                     "digits.all isDigitU = false` — a sub-region disjoint from "
                     "the other rivals' (the tail is present but not all digits).",
        "witness": _W_DIGITGUARD,
    },
    {
        "id": "weak-empty-bare",
        "kind": "uniqueness",
        "expect": "reject",
        # PARTIAL-DOMAIN: always return an empty bare name with no subscript.
        # Trivially wrong: it discards the base name on every non-empty input.
        "module": _impl(
            "    let out : List Char × Option (List Char) := ([], none)\n"
            "    return out"),
        "refinement": "a step that emitted an empty base name would drop the "
                      "parsed symbol entirely, so `split_super_sub(name)` would "
                      "return an empty base where the test demands the actual "
                      "letters — every exact-tuple assertion (`(\"w\",[],[\"1\"])`, "
                      "and the unchanged PASS cases) fails. It would NOT resolve.",
        "rationale": "REJECT from P on the REJECT branch: when there is no "
                     "trailing digit block the post-image returns the name whole "
                     "(`(name, none)`), but the rival returns `([], none)`. "
                     "Refuted by conditioning on `stripFinalNewline (afterLetters "
                     "name) = []` (no digit tail, so the spec is on its reject "
                     "branch) at a NON-EMPTY name — the only witness that pins the "
                     "reject-branch OUTPUT value, and the only one placed on the "
                     "no-digit-tail sub-region.",
        "witness": _W_EMPTY,
    },
    {
        "id": "weak-untrimmed-bare",
        "kind": "uniqueness",
        "expect": "reject",
        # NEAR-MISS: gets the accept/reject dispatch AND the digit block right,
        # but pairs the WHOLE name with the subscript instead of only the leading
        # letter run. Correct only when the name IS its whole letter run (no digit
        # tail) — which never coincides with the accept branch.
        "module": _impl(
            "    let letters := letterPrefix name\n"
            "    let rest := afterLetters name\n"
            "    let digits := stripFinalNewline rest\n"
            "    let out : List Char × Option (List Char) :=\n"
            "      if letters ≠ [] ∧ digits ≠ [] ∧ digits.all isDigitU then (name, some digits)\n"
            "      else (name, none)\n"
            "    return out"),
        "refinement": "a recognizer whose captured base group spanned the whole "
                      "name (rather than only the leading letters) would leave the "
                      "digits in the base name while ALSO splitting them off as a "
                      "subscript, so `split_super_sub(\"w1\")` would report base "
                      "\"w1\" where the test demands \"w\" — the trailing digits "
                      "are not removed from the base, which is precisely the "
                      "behaviour the fix must correct. It would NOT resolve.",
        "rationale": "REJECT from P on the ACCEPT branch: the post-image pairs the "
                     "leading letter run `letters` with the digit block, and the "
                     "rival pairs the whole `name`. Refuted by conditioning on the "
                     "three acceptance conjuncts AND `name ≠ letterPrefix name` "
                     "(the name is strictly more than its letter run, i.e. a digit "
                     "tail is present) — the only witness that pins the "
                     "accept-branch BASE value, distinct from weak-never-split "
                     "(which attacks the same branch's `Option` component).",
        "witness": _W_UNTRIMMED,
    },
]


# ---------------------------------------------------------------------------
# NAGINI → VELVET ACCOUNTING. The nagini sibling ships 7 SPEC cases (1 soundness
# positive, 1 admissibility, 1 frame-mutation rival, 4 partial-domain uniqueness
# rivals) plus 2 AXIOM_TESTS. The sibling contracts ONE function,
# split_trailing_digits, over a List[int] carrier with a fractional
# half-permission and grounded @Pure folds (splits/split_point/
# num_leading_letters/all_digits); this bundle contracts ONE method,
# splitTrailingDigits, over a List Char carrier with a deep pure model
# (peelDigits) and two opaque per-code-point axioms (isLetterU/isDigitU). The two
# surfaces model the SAME behavior; the observable is a single opaque-carried
# pair here, which governs the porting mechanics (a decide-on-a-literal witness
# is unavailable — every reject witness conditions on the carrier instead), but
# NOT the reachability of the reject lane.
#
#   nagini case                     kind          -> here                    status
#   -----------------------------------------------------------------------------
#   pos-control-reorder             soundness     -> pos-accept-hoisted       PORTED
#   admiss-w1                       admissibility -> admiss-satisfiable       RE-AIMED
#   frame-mutation-write-name0      uniqueness    -> (none)                   VACUOUS
#   partial-domain-off-by-one       uniqueness    -> weak-untrimmed-bare      RE-SITED
#   partial-domain-never-split      uniqueness    -> weak-never-split         PORTED
#   partial-domain-empty            uniqueness    -> weak-empty-bare          PORTED
#   partial-domain-greedy-overmatch uniqueness    -> weak-drop-digit-guard    RE-SITED
#   ax-sound-disjoint               axiom         -> (none)                   G-AX
#   ax-contain-recogniser           axiom         -> (none)                   G-AX
#
# 3 ported, 2 re-sited, 1 re-aimed, 1 vacuous, 2 -> G-AX. 8 velvet cases
# (2 verify soundness + 1 verify admissibility + 4 reject; 1 added positive over
# the sibling's single reorder — pos-rest-inlined — so the reshape space is
# exercised, not one reorder). Case-count parity with nagini is NOT the target;
# coverage of the single modeled obligation is (see below).
#
# PORTED (soundness): pos-control-reorder's ARGUMENT ("a proof-neutral reshape of
#   the impl that computes the same value must still verify") ports as
#   pos-accept-hoisted (the three-conjunct test hoisted into a boolean local).
#   pos-rest-inlined is ADDED so the reshape space includes local elimination,
#   not just a single reorder. The nagini reorder targeted the `upper` selection,
#   which has no counterpart in the branch-free peelDigits body; the carried
#   argument is what ports.
# RE-AIMED (admissibility): admiss-w1 establishes the fractional half-permission
#   precondition is establishable for a concrete F2P input. This backend has no
#   `require` clause and no permissions, so that probe is vacuous. Re-aimed at
#   the total-domain admissibility risk — the sole post clause being
#   unsatisfiable — witnessed by the gold impl verifying (module = _BASE).
# VACUOUS (frame-mutation-write-name0): the sibling writes to the read-only
#   `name[0]` under a half permission to trip INSUFFICIENT PERMISSION. This
#   backend is referentially transparent, has no heap or aliasing, and this
#   bundle declares NO `mut` binder — there is no read-only input to overwrite
#   and no substitute probe. Not fabricated.
# PORTED / RE-SITED (uniqueness, 4), the load-bearing lane. On the sibling's
#   List[int] carrier each rival is refuted by Viper against the grounded @Pure
#   folds. HERE the observable is a single opaque-carried pair (the classifiers
#   are content-free axioms, the method is noncomputable), so a decide-witness
#   gets stuck — but each rival's violation is a disagreement with peelDigits on
#   a sub-region described by the SAME carrier observations peelDigits branches
#   on, and a witness need not COMPUTE them, only ASSUME them and refute the
#   rival there (conditioning on the carrier; the django-13279 / django-11211
#   technique the porting rules direct one to before declaring the lane
#   inexpressible). Verified with real builds (elaborates on rival, fails on gold,
#   probe leaves False unsolved) for each:
#     - weak-never-split      P on accept: (name,none) vs (letters,some digits)
#     - weak-drop-digit-guard P on reject-vs-accept: drops the all-digits conjunct
#     - weak-empty-bare       P on reject branch: ([],none) vs (name,none)
#     - weak-untrimmed-bare   P on accept: (name,some digits) vs (letters,…)
#   partial-domain-off-by-one (peel k+1 code points into the bare name) re-sites
#   as weak-untrimmed-bare (the bare name over-reaches — the whole name rather
#   than only the letter run — a cleaner expression of "the base captures too
#   much" on this carrier, refuted at the same accept sub-region);
#   partial-domain-greedy-overmatch (cut at the letter boundary with no all-digit
#   requirement) re-sites as weak-drop-digit-guard (drop the `digits.all isDigitU`
#   conjunct — the identical over-acceptance, refuted where the tail is present
#   but not all digits). The refinement argument (a real patch of that shape
#   mangles the parsed token and fails the exact-tuple test) is unchanged in both.
# OMITTED — a conjunct-1 rival (accept even when the letter run is EMPTY, i.e.
#   split an all-digit name). AUDIT-CONFIRMED, with the reason sharpened. It IS
#   refutable on this carrier and was re-landed during audit with real builds:
#   conditioning on `letterPrefix name = [] ∧ digits ≠ [] ∧ digits.all isDigitU`,
#   the witness elaborated against the rival (exit 0), failed on the frozen
#   solution as `unsolved goals … ⊢ False` (exit 1), and its consistency probe
#   left `False` unsolved (exit 1). So this is NOT an expressibility gap.
#   It stays out because its REFINEMENT is false, which was MEASURED rather than
#   argued: running the unchanged parsing loop over every name the test file pins
#   yields post-loop base names {alpha, beta, x, w1, w11, w𝟙, w𝟙𝟙, w𝟙2𝟙, ω1, ω11,
#   ω𝟙, ω𝟙2}, none all-digit. A recognizer that dropped the letter-run
#   non-emptiness requirement therefore agrees with gold on every pinned input
#   and WOULD resolve the suite — so "it would NOT resolve" cannot be asserted.
#   The spec is faithfully stricter than the tests here (gold's letter group is
#   `+`, not `*`); that strictness is correct but not test-discriminating.
#   Recorded as a LIVE GAP, not a closed one: `letters ≠ []` is the one
#   acceptance sub-term no shipped rival attacks. (weak-empty-bare's witness DOES
#   move `letterPrefix name` off the value the accept-branch rivals hold it at,
#   so the binder is still varied.)
#
# BINDER / CLAUSE COVERAGE. The single input binder `name` is an opaque-carried
#   list with no literal value to enumerate; every reject witness quantifies over
#   a symbolic `name` and conditions on a DISTINCT structural fact about it, so it
#   is not held at a single point:
#     - weak-never-split:      letters≠[], digits≠[], all-digit           (pts 1)
#     - weak-drop-digit-guard: letters≠[], digits≠[], NOT all-digit       (pts 2)
#     - weak-empty-bare:       digits=[] (no tail), name≠[]               (pts 3)
#     - weak-untrimmed-bare:   letters≠[], digits≠[], all-digit, name≠letters (pts 4)
#   The four points move `letterPrefix name` across {≠[], =[]}, `stripFinalNewline
#   (afterLetters name)` across {≠[], =[]}, and `digits.all isDigitU` across
#   {true, false}. Independent aspects of the ONE clause P attacked: the
#   accept/reject dispatch (weak-never-split never accepts; weak-drop-digit-guard
#   over-accepts), the accept-branch OUTPUT (its base by weak-untrimmed-bare, its
#   Option/digit component by weak-never-split), and the reject-branch OUTPUT
#   (weak-empty-bare). The `letters ≠ []` acceptance conjunct is the one sub-term
#   left unattacked, for the refinement reason recorded under OMITTED above.
#
# AXIOM_TESTS (2): dropped. The axiom lane is G-AX's job (axiom_check.py records
#   the disjointness / recogniser-containment pass over the real re classes), and
#   the G-PBT gate ignores AXIOM_TESTS regardless.
#
# ---------------------------------------------------------------------------
# INDEPENDENT AUDIT — off-manifest probes run against the FROZEN spec, recorded
# here because a spec that rejects everything and a spec that accepts everything
# both look like a clean battery from the inside. None of these ships as a case;
# they are the evidence that the four that DO ship are not the only thing
# standing between this spec and a hole.
#
# AUDIT a6 (independent re-derivation) added 6 further NEW wrong impls and 4
#   further NEW correct reshapes, disjoint from the 11+4 below. All 6 wrong impls
#   were REJECTED (exit 1) and all 4 reshapes VERIFIED (exit 0), so no spec hole:
#     wrong: return `some letters` as the digit block on ACCEPT; drop `digits ≠ []`
#     while keeping the all-digits test (which is vacuously true of `[]`); test
#     `letters.all isDigitU` instead of `digits.all isDigitU`; return `([], none)`
#     on the REJECT branch; guard on the UNSTRIPPED `rest` while returning the
#     stripped `digits`; strip the final newline TWICE.
#     correct: `if h : …` dependent-if; the three conjuncts as NESTED ifs; the two
#     result pairs hoisted into `let acc`/`let rej` locals; and the body written as
#     `peelDigits name` directly. That last one matters as a read on the positives:
#     the spec's own model is an admissible impl, which is the sharpest statement
#     that P is an equality against a total function of the input and not a
#     shape constraint.
# SPEC-TOO-WEAK probes (11 NEW wrong impls, none in the manifest). Every one was
#   REJECTED by the frozen spec (exit 1), so no spec hole was found:
#     drop the `letters ≠ []` conjunct; drop the `digits ≠ []` conjunct; never
#     strip the tolerated final newline (`digits := afterLetters name`); strip
#     unconditionally (`(afterLetters name).dropLast`); swap the returned pair's
#     components; return `(letters, none)` on ACCEPT; return `(letters, none)` on
#     REJECT; return the UNSTRIPPED `rest` as the digit block; fold one digit into
#     the bare name (`letters ++ digits.take 1` — the sibling's off-by-one shape,
#     landed literally rather than re-sited); drop the last digit
#     (`digits.dropLast`); and cut at the letter boundary unconditionally
#     (`(letters, some digits)` with no guard at all — the sibling's
#     greedy-overmatch shape, landed literally). The two "re-sited" nagini rivals
#     were thus ALSO checked in their original shapes, not only as re-sites.
# SPEC-TOO-STRONG probes (4 NEW correct reshapes, none in the manifest). Every
#   one VERIFIED (exit 0), so the spec rejects no faithful impl tested:
#     `!letters.isEmpty && !digits.isEmpty && digits.all isDigitU` (Bool-valued
#     guard via `isEmpty`/`&&` instead of `≠ []`/`∧`); the three acceptance
#     conjuncts REORDERED (all-digits test first); the branch NEGATED (`if ¬(…)
#     then (name, none) else (letters, some digits)`); and a `match letters,
#     digits with` destructure that dispatches on cons/nil instead of on `≠ []`.
#   That last two matter for reading the positive controls: `loom_solve` closes
#   over a genuinely different control-flow SHAPE and a different guard TYPE, so
#   the two shipped positives are not passing merely because they are
#   syntactically adjacent to the frozen body.
# BINDER MEANINGFULNESS. The four shipped witnesses' hypothesis sets are pairwise
#   incompatible, so they name four genuinely distinct points and not four
#   spellings of one: never-split and drop-digit-guard differ on
#   `digits.all isDigitU` ({true, false} — the same hypotheses otherwise, so they
#   straddle exactly the acceptance boundary); empty-bare alone sits at
#   `digits = []`; untrimmed-bare adds `name ≠ letterPrefix name` on top of the
#   accept region. Each hypothesis is load-bearing in its own build (no witness
#   drew an unused-argument linter warning on the RIVAL side).
AXIOM_TESTS = []
