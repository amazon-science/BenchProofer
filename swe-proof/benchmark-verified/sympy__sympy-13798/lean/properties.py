"""properties.py — G-PBT falsification battery for sympy__sympy-13798 (lean).

NOT a Lean file; a manifest the G-PBT gate executes. Each case is a FULL
``Solution.lean`` variant built by region surgery on the frozen file: only text
strictly inside ``-- impl-start``/``-- impl-end`` — and, for the cases that
legitimately re-prove, inside ``-- proof-start``/``-- proof-end`` — is changed.
So ``markers.same_spec`` holds by construction, the single
``theorem correct_initMulSymbol`` STATEMENT stays byte-identical, and no case
introduces a ``sorry``/``admit``/``native_decide``/new ``axiom``/new
``theorem``. ``expect="verify"`` passes iff the variant elaborates with the
obligation closed; ``expect="reject"`` passes iff it does NOT verify AND the
case's ``witness`` holds of the rival while FAILING on the frozen solution.

PORT NOTE. This is a PORT of the nagini falsification battery
(``../nagini/properties.py``), which is the design document, not a text to
translate. The nagini bundle contracts TWO functions over a
``List[int]``-of-code-points carrier — one per derived separator — each pinned
to its own grounded pure oracle, and holds its input at half permission. This
Lean bundle models the SAME purely functional core as ONE total function whose
result is the PAIR of derived separators over an ``Option String`` carrier, so
nagini's two-function case split collapses two-to-one here (see ``assessment``
for the exact per-case disposition). The grounding is the same in kind: the
postcondition equates the result to ``specMulSymbol``, which is fully unfolded
in terms of the selector (a table lookup, the numeric key rewrite, and the
spacing-command test), so it is a FUNCTION OF THE INPUT and not an opaque
answer key an implementation could echo.

DEFENDED SURFACE (one obligation, one input binder).
``problem_spec_initMulSymbol ms result`` pins EXACTLY

    result = Except.ok (specMulSymbol ms)

which is one top-level equation carrying THREE independent pieces of content,
each attacked below:

  * (C-ok)   the ``Except`` tag: configuring must SUCCEED for an arbitrary
    selector, never take the error branch;
  * (C-gen)  the first component (the general-factor separator): a named
    selector maps to its table form, an unrecognized selector is used verbatim;
  * (C-num)  the second component (the numeric separator): the absent/empty
    selector behaves as the dotted named selector; an unrecognized selector that
    is purely a spacing command falls back to the dotted form; any other
    unrecognized selector is used verbatim.

C-gen and C-num are genuinely independent — they are separate components of the
returned pair, derived by separate branches — so a rival may be right about one
and wrong about the other, and the rivals below do exactly that in both
directions.

BINDER STRUCTURE AND POINT SPREAD. The predicate has ONE input binder, ``ms :
Option String``, but its behavior is partitioned into FIVE sub-domains — the
absent selector, the EMPTY selector, a named table entry, an unrecognized
spacing command, and an unrecognized non-spacing selector — and a rival can be
wrong on any one of them alone. The ten reject witnesses probe NINE distinct
selectors (``none`` carries two of them — see the note below this list), so no
binder value is held fixed across the battery. An earlier revision said "nine
DISTINCT selectors" while listing only eight, miscounting the two cases that
share ``none``; the enumeration below is the audited one:

  * ``none``            — the absent selector (the default rendering path);
  * ``some ""``         — the EMPTY selector: distinct from ``none`` because the
    table does not contain it (so the general separator is the empty string
    verbatim) while the numeric key rewrite still sends it to the dotted named
    entry. It exercises the ``s = ""`` arm of ``numKey``, which ``none`` does
    not reach;
  * ``some "dot"``      — a named table entry;
  * ``some "\\\\,"``      — unrecognized AND a spacing command (the reported case);
  * ``some "\\\\quad"``   — unrecognized AND a spacing command, a macro form;
  * ``some "\\\\,\\n"``     — a spacing command carrying SURROUNDING whitespace, so
    it is spacing-like only after the trim inside the spacing-command test;
  * ``some "\\\\,\\x0c"``   — a spacing command padded with a whitespace character
    that the renderer's trim strips but a narrower, four-character notion of
    whitespace does not. It separates the trim's EXISTENCE (probed by the
    newline-padded selector) from the trim's WHITESPACE SET, which no other
    selector in this battery can distinguish;
  * ``some "\\\\cdot"``   — unrecognized and NOT a spacing command, macro-shaped;
  * ``some "*"``        — unrecognized and NOT a spacing command, punctuation.

The absent selector additionally carries the COMPONENT-ORDER probe, whose rival
returns the right two strings in the wrong two positions.

ADVERSARIAL READ of the nagini case classes on this carrier:

  * FRAME / PERMISSION MUTATION — the PERMISSION half is vacuous, the FRAME half
    is NOT. The nagini sibling's mandatory class is the read-only-input probe:
    its selector is held at half permission and a rival that writes to it must
    fail for insufficient permission. Lean is referentially transparent — the
    selector is an immutable ``Option String`` value, there is no aliasing, no
    permission algebra and no read-only cell to overwrite — so the write itself
    has no counterpart and no permission probe is fabricated.

    The frame CONTENT is a different matter, and an earlier revision of this
    manifest disposed of it wrongly: it claimed frame discipline was discharged
    STRUCTURALLY because the postcondition pins both components of the returned
    pair. Pinning them is only worth what a rival can be built to violate, and
    the two component-specific rivals below each corrupt one component's VALUE —
    so each would still be refuted by a spec that pinned the pair only up to
    permutation. The genuinely frame-shaped rival is one that derives BOTH
    separators correctly and returns them in the wrong two POSITIONS, which no
    other case in the battery detects. ``weak-pair-order`` is that rival,
    refuted at the absent selector, where the two components differ. The nagini
    class is therefore re-shaped rather than dropped.

  * DIVERGENCE / NON-TERMINATION — the class is REJECTED here (not vacuous, and
    not a hole), but an earlier revision of this manifest justified that with a
    claim that is FALSE and is corrected here. It asserted that "a diverging
    implementation cannot be written at all" because ``implementation_*`` is a
    total ``def`` with no recursion and no ``partial``. Both halves are wrong:
    the impl region may be rewritten to add ``partial`` (region surgery is
    unrestricted inside the markers), and a ``while spin > 0 do spin := spin + 1``
    loop can be inserted with no ``partial`` keyword at all — it elaborates
    through ``Lean.Loop``, and such a variant VERIFIES against the frozen
    obligation with the frozen tactic script untouched.

    That variant is nonetheless NOT a spec hole, and the reason is the one worth
    recording: the inserted loop is DEAD CODE. Its result feeds nothing, so both
    the kernel and the compiler erase it — the impl still reduces by ``rfl`` to
    the frozen pair and still ``#eval``s to it without hanging. It denotes the
    same total function, so a spec that accepts it is not accepting divergence.

    When the divergence is made genuinely load-bearing the spec DOES reject it,
    which is what makes this lane shippable-but-already-covered rather than a
    gap. Two shapes were built and both are refuted: (a) a loop whose counter
    reaches the returned pair (``if spin > 0 then latexNum else "X"``), where the
    frozen script fails because ``forIn Lean.Loop.mk`` does not reduce; and (b) a
    ``partial def spinForever ms := spinForever ms`` whose value IS the result,
    where the obligation fails because the recursive constant is irreducible.
    Neither can be added to the reject lane as a shippable case, and this is a
    TOOLING limit rather than a spec one: an unreducible impl cannot carry a
    discriminating witness, because the witness's ``rfl``/``decide`` step is
    stuck for EVERY claim about it (measured: ``decide`` on shape (b) reports
    "failed to synthesize Decidable ¬implementation_initMulSymbol none = …",
    which is the gate's own ``witness-undecided`` stuck-reduction signature, not
    a refutation). The obligation-level rejection above is the real evidence;
    the class needs no manifest case, and the nagini sibling correspondingly
    carries no ``diverge-*``/``nonterm-*`` case to port.

  * UNGROUNDED-ORACLE ECHO — VACUOUS, for the same reason the nagini sibling
    gives: the postcondition's right-hand side is a pure function fully unfolded
    in terms of the selector, so there is no answer key to echo — reproducing it
    IS doing the derivation. In its place the battery carries honest positive
    controls that must verify.

  * PARTIAL-DOMAIN / VALUE — APPLIES, and is the bulk of the battery. TEN rivals
    are each correct on most of the domain and wrong on one sub-domain.

WITNESSES. On a tactic-proof backend "did not verify" is the DEFAULT outcome of
reshaping an implementation — the frozen script is tuned to the frozen form — so
a rejection alone attributes nothing to the spec. Every reject case therefore
carries a Lean snippet that evaluates the rival at ONE concrete selector
(``himpl``, closed by ``rfl`` — the carrier computes), evaluates the spec's own
right-hand side at the same selector (``hspec``, also ``rfl``), rewrites both
into the goal and closes by ``simp`` on the resulting literal disequality. Each
witness head binds NOTHING — every input is a ground literal — so there are no
hypotheses whose joint satisfiability could be in question and no route to the
inconsistent-binder forgery. Each was checked with two real ``lake env lean``
builds: it ELABORATES against its rival and FAILS on the frozen solution
(``rfl`` cannot close ``himpl`` there, because gold's value at that selector is
the spec's), so it discriminates rather than asserting a tautology.

The gold-side failure is a PLAIN EVALUATION refutation, and that was confirmed
rather than assumed: every gold-side build fails at ``himpl``, whose two sides
Lean prints as fully-reduced literals, e.g.

    Tactic `rfl` failed: The left-hand side
      implementation_initMulSymbol (some "\\\\cdot")
    is not definitionally equal to the right-hand side
      Except.ok (" ", "\\\\cdot")

— gold's value there is the spec's, so the RIVAL's value is not derivable for
it. That the exit code TRACKS THE CLAIM was then established by rebuilding, for
each case, a claim-flipped counterpart: the same file with ``himpl``/``hspec``
carrying GOLD's own pair at the same selector and the ``¬`` dropped, i.e.
asserting the obligation HOLDS there. Every such build ELABORATES against the
frozen solution (exit 0) and FAILS against the rival (exit 1) — the exact
mirror of the witness. So the gold-side error is not a form the file emits
regardless of what is claimed; flipping the claim flips both exit codes. No case
here rests on a stuck reduction, a missing ``Decidable`` instance, an unfolding
failure or an unknown name.

REFINEMENT. Each reject case's ``refinement`` argues that its faithful real
counterpart renders at least one product in the F2P assertion set with the wrong
separator, so ``test_latex_basic`` would still fail — making a verifying rival a
true verify-does-not-imply-resolve break rather than an artifact of the model.

AXIOM lane: EMPTY. This bundle declares no ``opaque`` callee and consumes no
``axiom`` (the derivation is modeled deeply and differential-tested by G-CONF),
so there is nothing for an axiom lane to probe; the nagini ``AXIOM_TESTS`` are
dropped as the porting map directs (that lane is G-AX's job).
"""
from pathlib import Path

INSTANCE = "sympy__sympy-13798"
BACKEND = "lean"

_BASE = (Path(__file__).parent / "Solution.lean").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


def _swaps(src, *pairs):
    for old, new in pairs:
        src = _swap(src, old, new)
    return src


# ---------------------------------------------------------------------------
# Region anchors. Each lies ENTIRELY inside the region it names and is unique in
# the frozen file (enforced by _swap's count==1 guard, so the manifest breaks
# loudly if the frozen solution ever drifts).
# ---------------------------------------------------------------------------

# -- impl region: the four arms that decide the two components of the pair.
_I_GEN_SOME = "  | some v => latex := v"
_I_GEN_NONE = '  | none   => latex := ms.getD ""'
_I_NUM_SOME = "  | some v => latexNum := v"
_I_NUM_NONE = ('  | none   =>\n'
               '      if isSpaceLike (ms.getD "") then latexNum := dotLatex\n'
               '      else latexNum := ms.getD ""')
_I_RETURN = "  return Except.ok (latex, latexNum)"

# -- impl region: the whole body, for the two whole-shape positive controls.
_I_BODY = (
    '  let mut latex : String := ""\n'
    '  match mulSymbolTable ms with\n'
    '  | some v => latex := v\n'
    '  | none   => latex := ms.getD ""\n'
    '  let mut latexNum : String := ""\n'
    '  match mulSymbolTable (numKey ms) with\n'
    '  | some v => latexNum := v\n'
    '  | none   =>\n'
    '      if isSpaceLike (ms.getD "") then latexNum := dotLatex\n'
    '      else latexNum := ms.getD ""\n'
    '  return Except.ok (latex, latexNum)')

# -- proof region: the whole frozen tactic body, so a positive that needs a
#    different script can restate it without touching the STATEMENT.
_P_BODY = (
    '  intro ms\n'
    '  unfold problem_spec_initMulSymbol implementation_initMulSymbol '
    'specMulSymbol\n'
    '  simp only [Id.run, bind, pure]\n'
    '  cases h1 : mulSymbolTable ms <;>\n'
    '    cases h2 : mulSymbolTable (numKey ms) <;>\n'
    '    simp only [] <;>\n'
    '    split <;> rfl')


# ---------------------------------------------------------------------------
# Witness scaffold. `inp` is a ground `Option String` literal; `got` is the
# rival's `Except` value there; `want` is the spec's own pair there. Both are
# reduced by `rfl` (the carrier computes at literals), so the head binds nothing
# and the closing step is a literal disequality.
# ---------------------------------------------------------------------------
def _w(inp, got, want):
    return (
        f"example : ¬ problem_spec_initMulSymbol {inp}\n"
        f"    (implementation_initMulSymbol {inp}) := by\n"
        "  unfold problem_spec_initMulSymbol\n"
        f"  have himpl : implementation_initMulSymbol {inp} = {got} := by rfl\n"
        f"  have hspec : specMulSymbol {inp} = {want} := by rfl\n"
        "  rw [himpl, hspec]\n"
        "  simp\n")


SPEC_TESTS = [
    # =====================================================================
    # POSITIVE CONTROLS (soundness) — structurally different but CORRECT
    # implementations that MUST verify, else SPEC-TOO-STRONG.
    #
    # The nagini sibling's two reorder positives (one per contracted function)
    # collapse into this pair: on this carrier both separators are components of
    # one returned pair produced by one function, so "reorder the recognised
    # branches" becomes "reorder the two derivations" and "reshape the whole
    # body".
    # =====================================================================
    {
        "id": "pos-num-first",
        "kind": "soundness",
        "expect": "verify",
        # Derive the SECOND component before the first: the two derivations are
        # independent, so swapping their order changes control flow and leaves
        # every value identical. The frozen tactic body still closes (the case
        # split is on the two lookups, whose order in the script is not tied to
        # their order in the body), so no proof authoring and no new
        # declaration. Verified with a real build.
        "module": _swap(
            _BASE, _I_BODY,
            '  let mut latexNum : String := ""\n'
            '  match mulSymbolTable (numKey ms) with\n'
            '  | some v => latexNum := v\n'
            '  | none   =>\n'
            '      if isSpaceLike (ms.getD "") then latexNum := dotLatex\n'
            '      else latexNum := ms.getD ""\n'
            '  let mut latex : String := ""\n'
            '  match mulSymbolTable ms with\n'
            '  | some v => latex := v\n'
            '  | none   => latex := ms.getD ""\n'
            '  return Except.ok (latex, latexNum)'),
        "rationale": (
            "structurally-different CORRECT implementation: the two component "
            "derivations are emitted in the opposite order. They read the same "
            "input and write different locals, so every input maps to the same "
            "pair and the single postcondition equation "
            "`result = Except.ok (specMulSymbol ms)` still holds — C-ok, C-gen "
            "and C-num are all order-insensitive. Must verify, else "
            "SPEC-TOO-STRONG (the spec would be pinning an incidental "
            "evaluation order rather than the derived separators). Statement "
            "byte-identical, frozen proof body unchanged, nothing assumed. "
            "Ports nagini's pos-control-*-reorder pair, which reorders the "
            "mutually exclusive recognised-selector branches for the same "
            "reason; here the two functions are one, so the reorder that is "
            "available is the order of the two derivations."),
    },
    {
        "id": "pos-let-form",
        "kind": "soundness",
        "expect": "verify",
        # Whole-shape reshape: drop the mutable locals and the statement-level
        # assignment entirely, binding each component with a single immutable
        # `let` whose right-hand side is an expression-level `match`. Same
        # values, a different program shape. The frozen `split <;> rfl` script
        # no longer applies (there is no assignment to split through), so the
        # proof region is RE-PROVED honestly: after unfolding, both sides are
        # definitionally the same expression and `simp only [Id.run, pure]`
        # closes it. The `theorem correct_initMulSymbol` STATEMENT is
        # byte-identical; no helper lemma, no new declaration, no assumption
        # token. Verified with a real build.
        "module": _swaps(
            _BASE,
            (_I_BODY,
             '  let latex : String := match mulSymbolTable ms with\n'
             '    | some v => v\n'
             '    | none   => ms.getD ""\n'
             '  let latexNum : String := match mulSymbolTable (numKey ms) with\n'
             '    | some v => v\n'
             '    | none   => if isSpaceLike (ms.getD "") then dotLatex '
             'else ms.getD ""\n'
             '  return Except.ok (latex, latexNum)'),
            (_P_BODY,
             '  intro ms\n'
             '  unfold problem_spec_initMulSymbol implementation_initMulSymbol '
             'specMulSymbol\n'
             '  simp only [Id.run, pure]'),
        ),
        "rationale": (
            "second, more aggressive CORRECT reshape: the mutable locals and "
            "assignment arms are replaced by two immutable bindings whose "
            "right-hand sides are expression-level matches. Identical values on "
            "every selector, so the postcondition equation still holds; must "
            "verify, else SPEC-TOO-STRONG. This case exists to show the reject "
            "lane below is not just detecting RESHAPES: this reshape is at "
            "least as large as any rival's and it still verifies, so a rival's "
            "rejection is about its values, not its form. Re-proved inside the "
            "proof region only (the frozen `split <;> rfl` has no assignment "
            "left to split through); statement byte-identical, no helper lemma, "
            "nothing assumed."),
    },
    {
        "id": "pos-direct-match",
        "kind": "soundness",
        "expect": "verify",
        # The most aggressive CORRECT reshape available: do not consult
        # `mulSymbolTable` or `numKey` AT ALL. Match the selector directly and
        # emit the two separators as inlined string literals, with the named
        # entries tested in a different order from the table's and the
        # empty-selector case folded into the numeric chain by hand. Same
        # function extensionally; almost no syntactic overlap with the frozen
        # body. Re-proved in the proof region: the named literals are discharged
        # by `subst`+`rfl`, then the residual unrecognized case reduces once the
        # two helpers are unfolded. Verified with a real build.
        "module": _swaps(
            _BASE,
            (_I_BODY,
             '  return Except.ok (\n'
             '    match ms with\n'
             '    | none   => (" ", " \\\\cdot ")\n'
             '    | some s =>\n'
             '      ((if s = "ldot" then " \\\\,.\\\\, "\n'
             '        else if s = "dot" then " \\\\cdot "\n'
             '        else if s = "times" then " \\\\times "\n'
             '        else s),\n'
             '       (if s = "" then " \\\\cdot "\n'
             '        else if s = "ldot" then " \\\\,.\\\\, "\n'
             '        else if s = "dot" then " \\\\cdot "\n'
             '        else if s = "times" then " \\\\times "\n'
             '        else if isSpaceLike s then " \\\\cdot "\n'
             '        else s)))'),
            (_P_BODY,
             '  intro ms\n'
             '  unfold problem_spec_initMulSymbol implementation_initMulSymbol '
             'specMulSymbol\n'
             '  simp only [Id.run, pure]\n'
             '  cases ms with\n'
             '  | none => rfl\n'
             '  | some s =>\n'
             '    by_cases h0 : s = ""\n'
             '    · subst h0; rfl\n'
             '    by_cases h1 : s = "ldot"\n'
             '    · subst h1; rfl\n'
             '    by_cases h2 : s = "dot"\n'
             '    · subst h2; rfl\n'
             '    by_cases h3 : s = "times"\n'
             '    · subst h3; rfl\n'
             '    unfold numKey mulSymbolTable\n'
             '    simp only [h0, h1, h2, h3, if_false, Option.getD]\n'
             '    split <;> rfl'),
        ),
        "rationale": (
            "third and strongest CORRECT reshape, and the one that answers the "
            "sharpest objection to the reject lane: every rival below is built "
            "by editing ONE arm of the frozen body, so a reader could suspect "
            "the spec is really pinning the frozen SHAPE and that the rejections "
            "track syntactic distance from it. This positive shares almost no "
            "syntax with the frozen body — it consults neither `mulSymbolTable` "
            "nor `numKey`, inlines every separator as a literal, tests the named "
            "entries in a different order than the table lists them, and folds "
            "the empty-selector rewrite into the numeric chain by hand — and it "
            "still VERIFIES. So the spec constrains the derived pair and nothing "
            "else, and a rival's rejection is about its values. Must verify, "
            "else SPEC-TOO-STRONG. Re-proved in the proof region only; statement "
            "byte-identical, no helper lemma, nothing assumed."),
    },

    # =====================================================================
    # ADMISSIBILITY (verify) — the obligation is SATISFIABLE, non-vacuously, at
    # exactly the selector the report asks about. The frozen theorem carries no
    # precondition hypothesis (`∀ ms`, unrestricted), so nagini's
    # "does the Requires admit a normal input" probe re-expresses as "is the
    # obligation dischargeable by evaluation at a normal in-domain input" —
    # prepended as a ground `have` to the otherwise verbatim frozen proof.
    # =====================================================================
    {
        "id": "admiss-ground-thinspace",
        "kind": "admissibility",
        "expect": "verify",
        "module": _swap(
            _BASE, _P_BODY,
            '  have _ground : problem_spec_initMulSymbol (some "\\\\,")\n'
            '      (implementation_initMulSymbol (some "\\\\,")) := by\n'
            '    unfold problem_spec_initMulSymbol\n'
            '    have himpl : implementation_initMulSymbol (some "\\\\,")\n'
            '        = Except.ok ("\\\\,", " \\\\cdot ") := by rfl\n'
            '    have hspec : specMulSymbol (some "\\\\,") '
            '= ("\\\\,", " \\\\cdot ") := by rfl\n'
            '    rw [himpl, hspec]\n'
            + _P_BODY),
        "rationale": (
            "the obligation is discharged at a concrete, normal, F2P-shaped "
            "selector — the thin-space spacing command named in the report — by "
            "EVALUATION: the implementation's value and the spec's own "
            "right-hand side are each reduced by `rfl` and shown equal, as a "
            "`have` inside the existing tactic body, after which the frozen "
            "obligation is closed verbatim. This verifies iff the modeled "
            "behavior is satisfiable at exactly the input the report is about — "
            "the analogue of nagini's PRECOND-TOO-STRONG probe, which "
            "self-calls on a freshly constructed in-domain selector. It also "
            "pins the two components apart at that selector (the general "
            "separator is the selector verbatim while the numeric one is the "
            "dotted form), so the case additionally certifies the spec is not "
            "vacuous there. Nothing is assumed: no new declaration, statement "
            "byte-identical. Ports nagini's admiss-general-thinspace and "
            "admiss-numeric-thinspace, which collapse to one case because both "
            "separators are components of one result here."),
    },

    # =====================================================================
    # UNIQUENESS / SPEC-TOO-WEAK rivals — wrong implementations sharing the
    # frozen spec byte-for-byte, each of which MUST be rejected. Every case
    # carries (a) the refinement argument that its faithful real counterpart
    # would NOT resolve the F2P, and (b) a witness, checked by two real builds,
    # pinning the violation at one concrete selector.
    # =====================================================================

    # ---- C-ok: configuring must SUCCEED for an arbitrary selector ----
    {
        "id": "weak-unrecognized-fails",
        "kind": "uniqueness",
        "expect": "reject",
        # The pre-fix behavior on this carrier: a selector outside the named
        # table makes configuring fail outright instead of being honored. Both
        # unrecognized arms take the error branch.
        "module": _swaps(
            _BASE,
            (_I_GEN_NONE, '  | none   => return Except.error ()'),
            (_I_NUM_NONE, '  | none   => return Except.error ()'),
        ),
        "witness": _w(r'(some "\\,")', 'Except.error ()',
                      r'("\\,", " \\cdot ")'),
        "rationale": (
            "MUST reject from the postcondition's `Except` tag (C-ok): the spec "
            "says `result = Except.ok (specMulSymbol ms)` for EVERY selector, "
            "so the error branch is unreachable, but this rival returns "
            "`Except.error ()` for every selector outside the named table. The "
            "binder is `ms`, refuted at the unrecognized spacing-command "
            "selector; the witness evaluates the rival to `Except.error ()` "
            "there while the spec demands `Except.ok`."),
        "refinement": (
            "this is precisely the behavior the report complains about: a "
            "selector outside the four named choices is rejected rather than "
            "honored. Its faithful real counterpart cannot render a product "
            "with a thin-space separator at all — configuring the renderer "
            "raises before any output is produced — so both new F2P assertions "
            "error out instead of producing `3\\,x^{2}\\,y` and "
            "`1.5 \\cdot 3^{x}`, and test_latex_basic would NOT resolve. A "
            "rival that verified here would mean the spec had left the success "
            "tag unpinned, which is the whole content of the requested change."),
    },

    # ---- C-gen: the general-factor separator ----
    {
        "id": "weak-general-blank",
        "kind": "uniqueness",
        "expect": "reject",
        # An unrecognized selector yields a plain blank general separator
        # instead of the selector itself. Correct on every named entry and on
        # the absent selector; wrong exactly on the honored-verbatim sub-domain.
        "module": _swap(_BASE, _I_GEN_NONE, '  | none   => latex := " "'),
        "witness": _w(r'(some "\\cdot")', r'Except.ok (" ", "\\cdot")',
                      r'("\\cdot", "\\cdot")'),
        "rationale": (
            "MUST reject from the first component of the postcondition equation "
            "(C-gen): for an unrecognized selector `specMulSymbol` uses the "
            "selector VERBATIM as its own form, but the rival substitutes a "
            "blank. Refuted at an unrecognized, NON-spacing-command selector, a "
            "sub-domain no other rival probes — chosen deliberately so the "
            "witness isolates C-gen from C-num (the second component is "
            "correct at that selector, so the disagreement can only be the "
            "first). Ports nagini's partial-general-unrec-blank."),
        "refinement": (
            "its faithful real counterpart honors the named selectors but "
            "silently downgrades every other selector to a plain space between "
            "general factors. Rendering a product of general factors with the "
            "thin-space selector would then emit `3 x^{2} y` rather than "
            "`3\\,x^{2}\\,y`, so the first new F2P assertion in "
            "test_latex_basic mismatches and the patch would NOT resolve — the "
            "user's chosen separator is dropped, which is exactly the "
            "complaint."),
    },
    {
        "id": "weak-named-crossed",
        "kind": "uniqueness",
        "expect": "reject",
        # Near-miss on the OTHER side of the table: honors unrecognized
        # selectors correctly (the requested behavior) but crosses two named
        # entries, emitting the crossed form for the dotted named selector.
        # Diverges on exactly one selector.
        "module": _swap(
            _BASE, _I_GEN_SOME,
            '  | some v => latex := if ms = some "dot" then " \\\\times " '
            'else v'),
        "witness": _w(r'(some "dot")', r'Except.ok (" \\times ", " \\cdot ")',
                      r'(" \\cdot ", " \\cdot ")'),
        "rationale": (
            "MUST reject from the first component (C-gen) on the NAMED-entry "
            "sub-domain: the table pins each named selector to its own standard "
            "form, and this rival emits a different named entry's form for one "
            "of them. It is a deliberate near-miss — it agrees with gold "
            "everywhere the other five rivals are refuted, including on the "
            "whole unrecognized sub-domain — so it gets its own witness at the "
            "single selector that distinguishes it, rather than sharing one. "
            "This is what stops the battery from certifying only the NEW "
            "behavior while leaving the pre-existing table unpinned. Ports "
            "nagini's partial-general-dot-as-times."),
        "refinement": (
            "its faithful real counterpart keeps the requested honoring of "
            "arbitrary selectors but corrupts one pre-existing named selector, "
            "rendering products with the crossed symbol where the dotted one is "
            "required. The pre-existing assertion in test_latex_basic that "
            "renders a product of general factors with the dotted named "
            "selector expects `2 \\cdot x \\cdot y` and would receive "
            "`2 \\times x \\times y`, so test_latex_basic — the F2P test "
            "itself, which contains that assertion — would NOT resolve, even "
            "though the two newly added assertions in it would pass."),
    },

    # ---- C-num: the numeric separator ----
    {
        "id": "weak-numeric-no-spacing-fallback",
        "kind": "uniqueness",
        "expect": "reject",
        # Drop the spacing-command fall-back: every unrecognized selector,
        # spacing command or not, is used verbatim for the numeric separator.
        "module": _swap(_BASE, _I_NUM_NONE,
                        '  | none   => latexNum := ms.getD ""'),
        "witness": _w(r'(some "\\quad")', r'Except.ok ("\\quad", "\\quad")',
                      r'("\\quad", " \\cdot ")'),
        "rationale": (
            "MUST reject from the second component (C-num): for an unrecognized "
            "selector that is purely a spacing command, `specMulSymbol` falls "
            "back to the dotted form, and this rival uses the selector "
            "verbatim. The first component is correct at the witness point, so "
            "the disagreement isolates C-num from C-gen — the mirror of "
            "weak-general-blank, which is what shows the two components are "
            "independently defended. Refuted at a spacing MACRO selector "
            "distinct from the one the report names, so the battery does not "
            "conclude the spacing class from a single literal. Ports nagini's "
            "partial-numeric-no-spacing-fallback."),
        "refinement": (
            "its faithful real counterpart honors arbitrary selectors for both "
            "separators but never substitutes the dotted form between numeric "
            "coefficients, so adjacent numbers are separated by nothing but a "
            "spacing command and run together. The second new F2P assertion in "
            "test_latex_basic requires `1.5 \\cdot 3^{x}` and would receive the "
            "spacing command in place of the dotted form, so the patch would "
            "NOT resolve."),
    },
    {
        "id": "weak-numeric-always-dot",
        "kind": "uniqueness",
        "expect": "reject",
        # The complement error: apply the dotted fall-back to EVERY
        # unrecognized selector, not only the spacing commands. Correct on every
        # spacing command (so it passes both new F2P assertions) and wrong on
        # every other unrecognized selector.
        "module": _swap(_BASE, _I_NUM_NONE, '  | none   => latexNum := dotLatex'),
        "witness": _w(r'(some "*")', r'Except.ok ("*", " \\cdot ")',
                      r'("*", "*")'),
        "rationale": (
            "MUST reject from the second component (C-num) on the OTHER side of "
            "the spacing-command test: an unrecognized selector that is NOT a "
            "spacing command must be used verbatim for the numeric separator "
            "too, and this rival overrides it with the dotted form "
            "unconditionally. Refuted at a non-spacing punctuation selector. "
            "Without this case the spacing-command predicate would be attacked "
            "in only one direction, and a rival that ignored the test entirely "
            "would still verify — the has-no-counterpart-in-nagini addition "
            "this carrier makes possible, since here both branches of that test "
            "sit in one modeled function."),
        "refinement": (
            "its faithful real counterpart substitutes the dotted form between "
            "numeric coefficients for EVERY selector outside the named table, "
            "discarding a selector the user explicitly asked for whenever it is "
            "not a spacing command. The report's request is that any supplied "
            "selector be honored; this counterpart honors it between general "
            "factors but silently replaces it between numbers, so rendering a "
            "product of numeric coefficients with, say, a punctuation selector "
            "emits the dotted form instead. It renders the two new F2P "
            "assertions correctly but violates the stated requirement on the "
            "rest of the domain, so a rival verifying here would be a genuine "
            "verify-does-not-imply-correct hole in the requested behavior."),
    },
    {
        "id": "weak-absent-numeric-blank",
        "kind": "uniqueness",
        "expect": "reject",
        # The absent selector's numeric separator becomes a plain blank instead
        # of behaving as the dotted named selector. Diverges on exactly the
        # default rendering path — the one sub-domain the other five rivals all
        # get right, so the `none` binder value is not held fixed.
        "module": _swap(
            _BASE, _I_NUM_SOME,
            '  | some v => latexNum := if ms.isNone then " " else v'),
        "witness": _w('none', r'Except.ok (" ", " ")',
                      r'(" ", " \\cdot ")'),
        "rationale": (
            "MUST reject from the second component (C-num) on the ABSENT-"
            "selector sub-domain: the spec makes the absent selector behave as "
            "the dotted named selector for the numeric separator, and this "
            "rival emits a blank. This is the only case that probes the binder "
            "at `none`; without it every witness would supply `some _`, and a "
            "rival that mishandled only the absent selector — the DEFAULT "
            "rendering path, used by every call that supplies no selector at "
            "all — would verify unnoticed. Ports nagini's "
            "partial-numeric-none-blank."),
        "refinement": (
            "its faithful real counterpart separates adjacent numeric "
            "coefficients with a bare space whenever no selector is supplied, "
            "which is the default for essentially every rendering call in the "
            "suite. The pre-existing assertions in test_latex_basic that render "
            "products of numeric coefficients with no selector expect the "
            "dotted form (e.g. `1.5 \\cdot 10^{20} x`) and would receive a "
            "bare space, so test_latex_basic — the F2P test — would NOT "
            "resolve."),
    },
    {
        "id": "weak-empty-numeric-blank",
        "kind": "uniqueness",
        "expect": "reject",
        # The EMPTY selector's numeric separator becomes the empty string
        # instead of behaving as the dotted named selector. Diverges on exactly
        # one selector, and on the one sub-domain no other case reaches: `some
        # ""` is NOT `none` (the table has no empty entry, so the general
        # component is the empty string verbatim) and it is not an ordinary
        # unrecognized selector either (the numeric key rewrite sends it to the
        # dotted named entry before the lookup, so it never reaches the
        # spacing-command test at all).
        "module": _swap(
            _BASE, _I_NUM_SOME,
            '  | some v => latexNum := if ms = some "" then "" else v'),
        "witness": _w('(some "")', 'Except.ok ("", "")',
                      r'("", " \\cdot ")'),
        "rationale": (
            "MUST reject from the second component (C-num) on the EMPTY-selector "
            "sub-domain, which the rest of the battery leaves unattacked. The "
            "numeric key rewrite has TWO falsy cases — the absent selector and "
            "the empty one — and they are separate arms: weak-absent-numeric-"
            "blank refutes at `none`, so a rival wrong only at `some \"\"` "
            "survived every other case here. That is the sub-domain where the "
            "two components come apart most sharply: the general separator is "
            "the empty string used VERBATIM (the table has no empty entry) while "
            "the numeric one is the dotted form, so the case pins the rewrite "
            "and the lookup as independent steps. Refuted by evaluation at "
            "`some \"\"`."),
        "refinement": (
            "its faithful real counterpart honors every named and unrecognized "
            "selector but emits NOTHING between numeric coefficients when the "
            "selector is supplied as an empty string — the documented way to ask "
            "for no separator between general factors, which must still keep "
            "adjacent numbers apart. Rendering a product of numeric "
            "coefficients that way runs them together into a single unreadable "
            "numeral, so the rendered output for a supplied-but-empty selector "
            "is wrong even though both new F2P assertions pass. A rival "
            "verifying here would mean the spec pinned only one of the two falsy "
            "selectors, leaving the other free."),
    },
    {
        "id": "weak-spacing-test-untrimmed",
        "kind": "uniqueness",
        "expect": "reject",
        # Apply the spacing-command membership test to the RAW selector instead
        # of the trimmed one. Correct on every selector that carries no
        # surrounding whitespace — i.e. on all six selectors the other rivals
        # are refuted at, and on both F2P selectors — and wrong exactly when a
        # spacing command arrives padded.
        "module": _swap(
            _BASE, _I_NUM_NONE,
            '  | none   =>\n'
            '      if ["", " ", "\\\\", "\\\\,", "\\\\:", "\\\\;", '
            '"\\\\quad"].contains\n'
            '          (ms.getD "") then latexNum := dotLatex\n'
            '      else latexNum := ms.getD ""'),
        "witness": _w(r'(some "\\,\n")', 'Except.ok ("\\\\,\\n", "\\\\,\\n")',
                      r'("\\,\n", " \\cdot ")'),
        "rationale": (
            "MUST reject from the second component (C-num) on the TRIM step "
            "inside the spacing-command test — the one clause of the modeled "
            "derivation no other case exercises. weak-numeric-no-spacing-"
            "fallback drops the whole fallback and weak-numeric-always-dot "
            "applies it unconditionally; both are refuted at selectors that are "
            "already trimmed, so each would still be caught by a spec that "
            "tested membership on the raw selector. This rival keeps the "
            "fallback and keeps the membership set, and changes ONLY whether the "
            "selector is trimmed first: it agrees with the frozen derivation on "
            "every selector without surrounding whitespace, including both "
            "selectors the reported case names. Refuted at a spacing command "
            "carrying a trailing newline, where the trim decides the branch. "
            "This is what makes the whitespace class load-bearing in the "
            "battery rather than only in the mapping prose."),
        "refinement": (
            "its faithful real counterpart tests the supplied selector for "
            "membership in the spacing-command set without normalizing it "
            "first, so a selector a user writes with any surrounding whitespace "
            "— the ordinary result of reading it from a config file, a "
            "docstring, or a template — is treated as an arbitrary token rather "
            "than as the spacing command it is. Adjacent numeric coefficients "
            "are then separated by that padded spacing command instead of the "
            "dotted form and run together, which is the same rendering defect "
            "the second new F2P assertion pins for the unpadded selector. The "
            "requested behavior is stated over the selector's content, not over "
            "its incidental padding, so a rival verifying here would leave the "
            "normalization step unpinned."),
    },
    {
        "id": "weak-spacing-test-narrow-ws",
        "kind": "uniqueness",
        "expect": "reject",
        # Keep the trim, keep the membership set, and narrow only the WHITESPACE
        # SET the trim recognizes to the four characters a naive implementation
        # would pick (space, tab, LF, CR) instead of the renderer's full set.
        # Correct on every selector padded with one of those four — including the
        # trailing-newline selector weak-spacing-test-untrimmed is refuted at —
        # and wrong exactly when the padding is a whitespace character outside
        # the narrow set.
        "module": _swap(
            _BASE, _I_NUM_NONE,
            '  | none   =>\n'
            '      let narrowWs : Char → Bool := fun c =>\n'
            "        c = ' ' || c = '\\t' || c = '\\n' || c = '\\r'\n"
            '      let t := String.mk ((((ms.getD "").toList.dropWhile\n'
            '        narrowWs).reverse.dropWhile narrowWs).reverse)\n'
            '      if ["", " ", "\\\\", "\\\\,", "\\\\:", "\\\\;", '
            '"\\\\quad"].contains t then\n'
            '        latexNum := dotLatex\n'
            '      else latexNum := ms.getD ""'),
        "witness": _w(r'(some "\\,\x0c")', r'Except.ok ("\\,\x0c", "\\,\x0c")',
                      r'("\\,\x0c", " \\cdot ")'),
        "rationale": (
            "MUST reject from the second component (C-num) on the WHITESPACE SET "
            "the trim ranges over — the last clause of the modeled derivation "
            "left unattacked, and one no other case can reach. "
            "weak-spacing-test-untrimmed removes the trim ENTIRELY, so it is "
            "refuted by any padded selector and would still be caught by a spec "
            "whose trim recognized only the four common whitespace characters. "
            "This rival KEEPS the trim and keeps the membership set, and narrows "
            "only which characters count as whitespace: it agrees with the frozen "
            "derivation on every selector whose padding is a space, tab, line "
            "feed or carriage return — including the trailing-newline selector "
            "the untrimmed rival is refuted at — and diverges only when the "
            "padding is one of the other whitespace characters the renderer's "
            "trim also strips. Refuted at a spacing command padded with a form "
            "feed, where the two whitespace notions disagree: the frozen "
            "derivation trims it and falls back to the dotted form, the rival "
            "does not and emits the padded selector verbatim. Without this case "
            "the whitespace set is pinned only by the mapping prose and by "
            "G-CONF, never by a rival the spec has to refute."),
        "refinement": (
            "its faithful real counterpart normalizes the supplied selector with "
            "a hand-rolled trim over the four whitespace characters most "
            "implementations think of, rather than the full set the renderer's "
            "own string trim strips. A selector padded with any of the others — "
            "the ordinary result of reading it from a form feed-separated "
            "template, a spreadsheet export, or text carrying non-breaking or "
            "typographic spaces — is then classified as an arbitrary token "
            "instead of the spacing command it is, so adjacent numeric "
            "coefficients are separated by the padded spacing command and run "
            "together. That is the same rendering defect the second new F2P "
            "assertion pins for the unpadded selector, reached through a "
            "different padding character. The requested behavior is stated over "
            "the selector's content after normalization, so a rival verifying "
            "here would leave the normalization's whitespace notion unpinned."),
    },
    {
        "id": "weak-pair-order",
        "kind": "uniqueness",
        "expect": "reject",
        # The FRAME-shaped rival (see the porting map above): derive both
        # separators exactly as the frozen body does, then return them in the
        # wrong two positions. Every VALUE it computes is correct; only their
        # placement in the result is wrong.
        "module": _swap(_BASE, _I_RETURN,
                        "  return Except.ok (latexNum, latex)"),
        "witness": _w('none', r'Except.ok (" \\cdot ", " ")',
                      r'(" ", " \\cdot ")'),
        "rationale": (
            "MUST reject from the postcondition equation as a WHOLE, and it is "
            "the only case here that does. The spec pins an ordered pair: the "
            "FIRST component is the general-factor separator and the SECOND is "
            "the numeric one. Every other rival corrupts one component's value, "
            "so every other rival would still be refuted by a spec that pinned "
            "the pair only up to permutation — meaning the battery, before this "
            "case, never tested that the two derived separators are attributed "
            "to the right roles. This rival computes BOTH separators exactly as "
            "the frozen derivation does and returns them transposed, so it is "
            "refutable only from the ordering. This is the port's substitute for "
            "nagini's frame-mutation class: on a referentially transparent "
            "carrier the read-only-input WRITE is inexpressible, but the frame "
            "CONTENT it protects — that the result's components are not confused "
            "with one another — is expressible exactly this way. Refuted at the "
            "absent selector, where the two components differ."),
        "refinement": (
            "its faithful real counterpart assigns each derived string to the "
            "OTHER of the two settings the renderer consumes, so the separator "
            "meant for numeric coefficients is inserted between general factors "
            "and vice versa. With no selector supplied that swaps a bare space "
            "for the dotted form in both roles at once: products of general "
            "factors are rendered with the dotted separator and adjacent "
            "numeric coefficients with a bare space. The pre-existing "
            "assertions in test_latex_basic pin both roles at the default "
            "selector (`2 x y` for general factors, `1.5 \\cdot 10^{20} x` "
            "between numbers), so both would mismatch and test_latex_basic — "
            "the F2P test — would NOT resolve."),
    },
]
