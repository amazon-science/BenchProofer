"""properties.py — G-PBT falsification battery for astropy__astropy-14365 (velvet).

NOT a Velvet module; a record of adversarial cases the G-PBT gate executes. Each
SPEC case is a full ``Solution.lean`` variant that shares the FROZEN spec
byte-for-byte (region surgery: only text inside an ``-- impl-start`` /
``-- impl-end`` region, or inside a ``prove_correct`` tactic body, is changed —
both of which the consumer spec view elides, so ``markers.same_spec`` holds and
every ``prove_correct`` header survives) and swaps in a candidate
implementation. It is checked by the real verifier. ``expect:"verify"`` passes
iff (in scope AND verifies); ``expect:"reject"`` passes iff (in scope AND does
NOT verify AND its refutation ``witness`` discriminates: the witness must
elaborate against the rival and FAIL against the frozen solution).

DEFENDED SURFACE (two contracted methods, three input binders total):

  lineType  (line : List Char)             ensures out = classify true line
  maskFlags (tokens : List (List Char))    ensures out = maskSeq true tokens

Neither method carries a ``require`` clause, so the admitted domain of each is
TOTAL: every ``List Char`` / ``List (List Char)`` is in scope, and the post-image
must hold at every one of them. That totality is what makes each partial-domain
rival below refutable at a concrete literal point.

Both post-images are stated against DEEP models in the ``pure`` region
(``classify``/``maskSeq``, built from ``eqFold``/``isMarkerTok``/``isNanTok``/
``isDirective``/``isDecimal``/``words``/``stripWs``); the ``axioms`` region is
EMPTY. So the carrier is fully transparent and every witness below decides at a
literal input — no opaque term has to be conditioned on, and there is no
ungrounded answer-key an impl could echo without doing the work (the "grounded
echo" the sibling ships as a positive control is simply the cheapest CORRECT
impl here, which is why it appears below as ``pos-maskflags-direct-map``).

The load-bearing clause in each method is its single value equation. Both
equations decompose into independent sub-behaviors the rivals attack in turn:

  * ``out = classify true line`` — the FOLD FLAG threaded into every reserved-word
    comparison (the abstract case-insensitive behavior the spec pins), the
    ordered alternation between the directive / break-marker / data-row shapes,
    and the operand COUNT carried by a data row.
  * ``out = maskSeq true tokens`` — the fold flag inside the per-cell marker
    decision, the exactness of that comparison (whole token, not a prefix), and
    the element-wise ALIGNMENT of the flag list with the row's cells.

ADVERSARIAL READ of the sibling's classes:

  * FRAME-MUTATION — INEXPRESSIBLE against THIS frozen spec, and NOT fabricated a
    substitute. The class exists on the sibling because an input may carry a
    fractional heap permission a rival can overwrite to satisfy a postcondition
    vacuously. Note the reason here is NOT that the backend lacks mutation —
    velvet does have a ``mut`` parameter binder, and other bundles in this corpus
    contract methods that declare one. It is that NEITHER frozen signature here
    declares one, and a binder lives in the method SIGNATURE, which is part of the
    consumer spec view: ``markers.same_spec`` elides only the impl regions and
    ``prove_correct`` tactic bodies, so a variant cannot add ``mut``. Both halves
    were checked with real builds rather than argued:
      - adding ``mut tokens`` to ``maskFlags``'s signature is rejected as
        OUT-OF-SCOPE by ``variant_scope.variant_problems`` (``spec view differs
        (same_spec failed)``), and the file does not even elaborate (exit 1:
        the ``mut`` binder renames the value to ``tokensOld``, so the frozen
        ``ensures``/``invariant`` lose their referent — ``Unknown identifier
        `tokens```);
      - writing the input from INSIDE the impl region — the one place a variant
        may legally edit — is in scope mechanically but does not compile (exit 1:
        ``` `tokens` cannot be mutated, only variables declared using `let mut`
        can be mutated ```).
    So there is no read-only input a variant can overwrite and no analogous probe:
    the frame here is enforced by the binder's absence, statically, before any
    postcondition is consulted.
  * DIVERGENCE / NON-TERMINATION - CLOSED BY THE SEMANTICS, not a spec hole, and
    still not shippable as a reject case. Every factual claim an earlier revision
    of this bullet made about this class was wrong, and each is retracted here
    against a real build rather than an argument.
    (i) It said this bundle sets ``loom.semantics.termination "partial"``. It does
    not: line 4 of the frozen ``Solution.lean`` reads ``"total"``, and the only
    correctness namespace the file opens is ``open TotalCorrectness
    DemonicChoice``. Those two lines cannot disagree, because the ``set_option``
    elaborator ITSELF runs ``openScope `TotalCorrectness``
    (``Loom/MonadAlgebras/WP/Options.lean:169-186``); the option value and the
    ``open`` move together by construction.
    (ii) It said a non-terminating impl satisfies every ``ensures`` clause
    vacuously and VERIFIES, and reported a diverging prefix spliced ahead of the
    frozen ``lineType`` body as exiting 0. Under ``total`` a postcondition is
    claimed of ALL runs, not only terminating ones, and the verifier demands a
    decreasing measure on every loop. Both diverging shapes are REJECTED,
    measured on this bundle with the proofs reduced to a bare ``loom_solve``:
      - a spun loop with NO ``decreasing`` clause is refused at elaboration,
        ``error: Decreasing annotations are required in total correctness
        semantics``;
      - the sharper shape, which cannot be dismissed as merely missing the
        annotation, CARRIES a measure that does not decrease
        (``while q > 0 / invariant 0 ≤ q / done_with q = 0 / decreasing q`` with a
        body of ``q := q``): also REJECTED, exit 1, and it fails on the MEASURE's
        own goal - ``case «decreasing_1: i»`` with the residual ``⊢ q < q``.
    So the descent obligation is emitted and live, and a rival that never answers
    does not satisfy this spec. Nothing is escalated; the frozen spec needs no
    change.
    (iii) It said the class is inexpressible because no witness can refute a rival
    the spec satisfies. The spec does not satisfy it, so that reason is void. The
    real obstruction is the WITNESS CONTRACT, and it is mechanical: a reject case
    needs a witness that ELABORATES against its rival, but a rejected diverging
    rival's module does not compile at all - the obligation fails at the ``method``
    itself, ahead of any appended tester - so the gate would return
    ``witness-unproven`` -> INCONCLUSIVE instead of a rejection. Hence no case
    That is the shape with NO measure. A rival that CARRIES a measure which
    does not decrease is refused at the ``prove_correct`` site instead, which
    the witness file strips, so that module does elaborate; but its post-image
    is then an unreduced ``forIn Lean.Loop.mk`` term carrying
    ``invariantGadget`` / ``onDoneGadget`` / ``decreasingGadget``, which the
    kernel will not normalise to a value a concrete-input tester can decide.
    Both shapes therefore land ``witness-unproven``.
    ships, but the class is closed by the semantics rather than open in the spec.
  * PARTIAL-DOMAIN / VALUE — the main class here, and the sibling's own. Each
    rival is right on the sub-domain the sibling's witness clauses pin and
    diverges on a case variant, an operand count, or a cell alignment that the
    failing test depends on.

WITNESS MECHANICS. Each witness reaches the ``method`` contract through Velvet's
own tester machinery (``extract_program_for`` / ``derive_tester_for``) and asserts
``<name>Tester <input> = false`` — i.e. the rival's extracted program provably
violates its own contract at that input. It is checked in a file whose
``prove_correct`` blocks have been stripped, so no tactic script can mask the
verdict.

Both frozen impls are shaped so the discrimination is about WRONGNESS, not about
loop shape. ``lineType``'s frozen body is already loop-free, so its testers
reduce under ``decide`` for gold and rival alike and the gold-side failure is a
genuine "``decide`` proved this proposition is false" — the spec HOLDS of gold at
that input. ``maskFlags``'s frozen body is a ``while`` loop whose extracted
program does not reduce, so its gold-side failure is a non-reduction; that alone
would be a weak discriminator, so it was checked by hand that a CORRECT loop-free
``maskFlags`` (``return maskSeq true tokens``) also fails each ``maskFlags``
witness. The witnesses therefore separate wrong-from-right, not
reshaped-from-frozen.

WITNESS PLACEMENT. Every input binder of both spec predicates is VARIED across
the reject witnesses, at eight distinct input points:

  line   : "read serr 1 2"  (a lower-case directive)
           "1 no"           (a data row whose cell is a lower-case sentinel)
           "1 2"            (a plain two-operand data row — no letters at all)
           "NO"             (a single marker cell — the break branch's arity guard)
           "1 -nan"         (a signed not-a-number cell — the sign alternative)
  tokens : ["nO"]           (a trailing-character-only case difference)
           ["No"]           (one mixed-case sentinel cell)
           ["1", "NO"]      (a two-cell row — probes ALIGNMENT, not case)

No binder is held at one value across the battery, and the two near-miss rivals
(``weak-maskflags-first-char-fold``, ``weak-linetype-directive-only-fold``) are
each refuted at the input that separates them from the blunter rival attacking
the same clause, so the sub-domain each claims is machine-demonstrated rather
than merely asserted. Both separations are machine-checked in BOTH directions,
which is what makes the "near-miss" label an observation rather than a claim:

  * ``weak-maskflags-single-case-marker`` is refuted at ``["nO"]`` (exit 0
    against the rival), while ``weak-maskflags-first-char-fold`` SURVIVES that
    same witness (exit 1) — it decides ``["nO"]`` exactly as the spec demands.
    So the two rivals are genuinely refuted on different sub-domains. An earlier
    revision aimed the blunt rival at ``["no"]``, where the near-miss is ALSO
    wrong (verified: the near-miss admits that witness too), so the input
    attested nothing about the separation it was chosen to demonstrate.
  * ``weak-linetype-directive-only-fold`` survives the witness that refutes
    ``weak-linetype-single-case-recognition`` (``"read serr 1 2"``, exit 1), and
    is refuted one shape later at ``"1 no"``.

AXIOM lane: EMPTY (the ``axioms`` region declares no ``axiom``; both changed
behaviors are modeled deeply and their soundness against the real callees is a
G-AX concern owned by axiom_check.py). The gate ignores ``AXIOM_TESTS``.
"""
from pathlib import Path

INSTANCE = "astropy__astropy-14365"
BACKEND = "velvet"

_BASE = (Path(__file__).parent / "Solution.lean").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# ---------------------------------------------------------------------------
# Frozen anchors. Each fragment lies WHOLLY inside the region it names (an impl
# region, or a `prove_correct` tactic body) and is unique in the file — both
# asserted at import, so the manifest breaks loudly if Solution.lean ever moves.
# ---------------------------------------------------------------------------

# `lineType`'s impl-region body, verbatim (comments included, so a rival that
# replaces it cannot leave stale narration behind).
_LT_BODY = (
    "    -- Classify the line with case-folding ENABLED (the abstract "
    "case-insensitive\n"
    "    -- behavior). The recognizer has no internal loop; `line` is read-only.\n"
    "    return classify true line\n"
)

# `maskFlags`'s impl-region body, verbatim.
_MF_BODY = (
    "    -- Backward scan over the row's cells, deciding the missing-value flag of\n"
    "    -- each with case-folding ENABLED. `tokens` is read-only (not mutated).\n"
    "    let mut result : List Bool := []\n"
    "    let mut i := tokens.length\n"
    "    while i > 0\n"
    "      invariant 0 ≤ i ∧ i ≤ tokens.length\n"
    "      invariant result = maskSeq true (tokens.drop i)\n"
    "      done_with i = 0\n"
    "      decreasing i\n"
    "    do\n"
    "      let t := tokens[i - 1]!\n"
    "      result := isMarkerTok true t :: result\n"
    "      i := i - 1\n"
    "    return result\n"
)

# The single per-cell decision line inside `maskFlags`'s loop, for the in-loop
# reshape positive.
_MF_STEP = "      result := isMarkerTok true t :: result\n"

# The two frozen proof blocks. A tactic body is elided from the consumer spec
# view, so a variant may retune it; the `prove_correct <name>` header must (and
# does, in every case below) survive.
_PROVE_LT = "prove_correct lineType by\n  loom_solve\n"
_PROVE_MF = (
    "prove_correct maskFlags by\n"
    "  loom_solve\n"
    "  rw [maskSeq_drop_step tokens i (by omega) (by omega)]\n"
    "  simp_all\n"
)

for _frag in (_LT_BODY, _MF_BODY, _MF_STEP, _PROVE_LT, _PROVE_MF):
    if _BASE.count(_frag) != 1:
        raise AssertionError(f"frozen anchor drifted / non-unique: {_frag[:60]!r}")


def _lt(body, prove=None):
    """Variant replacing `lineType`'s whole impl body (and optionally retuning
    its proof)."""
    out = _swap(_BASE, _LT_BODY, body)
    return _swap(out, _PROVE_LT, prove) if prove else out


def _mf(body, prove=None):
    """Variant replacing `maskFlags`'s whole impl body (and optionally retuning
    its proof)."""
    out = _swap(_BASE, _MF_BODY, body)
    return _swap(out, _PROVE_MF, prove) if prove else out


# ---------------------------------------------------------------------------
# Witness preamble: reach the `method` contract through Velvet's own tester.
# ---------------------------------------------------------------------------

def _tester(m):
    return (f"extract_program_for {m}\n"
            f"prove_precondition_decidable_for {m}\n"
            f"prove_postcondition_decidable_for {m}\n"
            f"derive_tester_for {m}\n\n")


def _witness(m, call):
    return _tester(m) + f"example : {m}Tester {call} = false := by\n  decide\n"


SPEC_TESTS = [
    # =====================================================================
    # POSITIVE CONTROLS (soundness) — structurally different but CORRECT
    # impls that MUST verify. If a faithful correct impl cannot verify, the
    # spec is SPEC-TOO-STRONG.
    # =====================================================================
    {
        "id": "pos-linetype-blank-guard-first",
        "kind": "soundness",
        "expect": "verify",
        # Hoist the blank-line decision out in front as an explicit branch
        # instead of letting the modeled classifier take it internally. Same
        # value on every line; the proof splits the branch and folds each side
        # back to the model.
        "module": _lt(
            "    let s := stripWs line\n"
            "    let r := if s = [] then LType.comment else classify true line\n"
            "    return r\n",
            "prove_correct lineType by\n"
            "  loom_solve\n"
            "  by_cases h : stripWs line = [] <;> simp [classify, h]\n"),
        "rationale": "hoisting the blank/decorative-line case into an explicit "
                     "leading branch is observationally the modeled classifier "
                     "on EVERY line (the model takes the same decision first), "
                     "so `out = classify true line` still holds pointwise and "
                     "the proof closes by splitting the branch. A correct "
                     "reshape must verify, else SPEC-TOO-STRONG.",
    },
    {
        "id": "pos-maskflags-direct-map",
        "kind": "soundness",
        "expect": "verify",
        # Replace the backward accumulator loop by a forward element-wise map.
        # A genuinely different traversal shape (and the cheapest correct impl,
        # since the post-image is grounded in the argument rather than pinned to
        # an opaque oracle), reproved by induction on the row.
        "module": _mf(
            "    return tokens.map (isMarkerTok true)\n",
            "prove_correct maskFlags by\n"
            "  loom_solve\n"
            "  induction tokens <;> simp_all [maskSeq]\n"),
        "rationale": "a forward element-wise map over the row computes the same "
                     "per-cell flag list as the frozen backward accumulator "
                     "loop, so `out = maskSeq true tokens` holds and the proof "
                     "closes by induction on the row. This is also the honest "
                     "cheapest-correct impl: the post-image is GROUNDED in the "
                     "argument (a deep model, empty axioms region), so the "
                     "direct restatement is correct rather than a wrong echo — "
                     "its verifying is the evidence that there is no ungrounded "
                     "answer key to exploit. Must verify.",
    },
    {
        "id": "pos-maskflags-inline-fold-compare",
        "kind": "soundness",
        "expect": "verify",
        # Keep the frozen loop and inline the per-cell decision as the raw
        # case-folded comparison instead of calling the named helper. Same value
        # flow; the proof unfolds the helper before the drop-step rewrite.
        "module": _swap(
            _swap(_BASE, _MF_STEP,
                  "      result := eqFold true t \"NO\".toList :: result\n"),
            _PROVE_MF,
            "prove_correct maskFlags by\n"
            "  loom_solve\n"
            "  rw [maskSeq_drop_step tokens i (by omega) (by omega)]\n"
            "  simp_all [isMarkerTok]\n"),
        "rationale": "inlining the case-folded comparison against the reserved "
                     "marker in the loop body computes exactly what the named "
                     "per-cell helper does (the helper IS that comparison), so "
                     "the value equation still holds and the proof closes with "
                     "the helper unfolded. Must verify.",
    },

    # =====================================================================
    # ADMISSIBILITY — neither method carries a `require` clause, so nothing
    # could exclude a normal input and the sibling's "the precondition admits
    # an F2P-shaped input" probe is vacuous here. RE-AIMED at the residual
    # admissibility risk on a total domain: that the post-image is
    # UNSATISFIABLE or DEGENERATE at the interesting points. The case
    # discharges a live in-region assertion that the modeled classifier maps
    # the two shapes the failing test exercises to two DISTINCT, non-trivial
    # classifications — a lower-case directive line to the directive class,
    # and a four-operand data row to the data class carrying count 4. The
    # frozen impl is kept verbatim so the value clause still discharges too.
    # =====================================================================
    {
        "id": "admiss-classify-nondegenerate",
        "kind": "admissibility",
        "expect": "verify",
        "module": _lt(
            "    assert (with_name_prefix `assert\n"
            "      (classify true \"read serr 1 2\".toList = LType.command\n"
            "        ∧ classify true \"1 0.5 1 0.5\".toList = LType.data 4))\n"
            "    return classify true line\n",
            "prove_correct lineType by\n"
            "  loom_solve\n"
            "  decide\n"),
        "rationale": "the post-image is satisfiable AND non-degenerate at the "
                     "shapes the failing test exercises: it demands the "
                     "directive classification for a lower-case header "
                     "directive and the data classification with operand count "
                     "exactly 4 for a four-cell row — two DISTINCT non-trivial "
                     "images, so the obligation is not collapsed to a constant. "
                     "The in-region assertion must discharge (else the "
                     "post-image would be unsatisfiable at the interesting "
                     "point, PRECOND-TOO-STRONG); the frozen impl is kept "
                     "verbatim so the value clause discharges as well.",
    },

    # =====================================================================
    # UNIQUENESS / SPEC-TOO-WEAK rivals — wrong impls sharing the frozen spec
    # that MUST be rejected, each with a machine-checked refutation witness at
    # a concrete input and the argument that its faithful real counterpart
    # would NOT resolve the failing test.
    # =====================================================================
    {
        "id": "weak-linetype-single-case-recognition",
        "kind": "uniqueness",
        "expect": "reject",
        # The fold flag is threaded as `false`: reserved words are recognized
        # only in their single canonical case. This is the whole behavior the
        # spec exists to pin, attacked head-on.
        "module": _lt("    return classify false line\n"),
        "refinement": "a counterpart recognizing the format's reserved words in "
                      "only one letter case rejects a header directive written "
                      "in the other case, so the failing scenario — the same "
                      "table presented with its non-decorative lines in the "
                      "other case — still aborts at line classification with "
                      "the line unrecognized, exactly the reported symptom. It "
                      "would NOT resolve.",
        "rationale": "REJECT from `out = classify true line`: the post-image "
                     "demands recognition with case-folding ENABLED, and at a "
                     "lower-case header directive the folded classifier returns "
                     "the directive class while the unfolded one rejects the "
                     "line. Refuted at `\"read serr 1 2\"`, the directive "
                     "sub-domain.",
        "witness": _witness("lineType", '"read serr 1 2".toList'),
    },
    {
        "id": "weak-linetype-directive-only-fold",
        "kind": "uniqueness",
        "expect": "reject",
        # NEAR-MISS of the rival above: folds case for the header-directive
        # shape only, and falls back to single-case recognition for every other
        # shape. Agrees with the spec on the directive sub-domain the previous
        # rival is refuted on, so it needs its own separating input: a DATA row
        # whose cell is the sentinel word in the other case.
        "module": _lt(
            "    let s := stripWs line\n"
            "    let r := if isDirective true s then LType.command\n"
            "             else classify false line\n"
            "    return r\n"),
        "refinement": "a counterpart that case-folds only the header-directive "
                      "recognition leaves the DATA-row grammar single-case, so a "
                      "row containing the reserved sentinel word in the other "
                      "case is not a recognized data row at all and the read "
                      "still aborts at line classification — one line later "
                      "than before, but on the same failing scenario. It would "
                      "NOT resolve.",
        "rationale": "REJECT from `out = classify true line`: the fold flag is "
                     "threaded into EVERY reserved-word comparison, not just "
                     "the directive's. Refuted at `\"1 no\"`, where the "
                     "post-image demands the data class with count 2 and the "
                     "rival rejects the line. That input separates this "
                     "near-miss from weak-linetype-single-case-recognition, "
                     "which this rival agrees with gold about "
                     "(`\"read serr 1 2\"` classifies correctly here) — so the "
                     "sub-domain it claims is demonstrated, not asserted.",
        "witness": _witness("lineType", '"1 no".toList'),
    },
    {
        "id": "weak-linetype-operand-count-off-by-one",
        "kind": "uniqueness",
        "expect": "reject",
        # Attacks a DIFFERENT sub-behavior of the same clause: the recognition
        # is entirely right (every branch, both cases) but the operand COUNT
        # carried by a data row is inflated by one. Refuted at a row with no
        # letters at all, so this case is independent of the fold flag.
        "module": _lt(
            "    let base := classify true line\n"
            "    let r := match base with\n"
            "             | LType.data n => LType.data (n + 1)\n"
            "             | other => other\n"
            "    return r\n"),
        "refinement": "a counterpart reporting one operand too many for every "
                      "data row makes each row's declared width disagree with "
                      "the header's column count, so the round-trip in the "
                      "failing test reads a table of the wrong shape and still "
                      "fails on the surplus column — in BOTH the folded and "
                      "unfolded presentations. It would NOT resolve.",
        "rationale": "REJECT from `out = classify true line`: the data "
                     "classification carries the row's operand count, and the "
                     "post-image pins it exactly. Refuted at `\"1 2\"`, a "
                     "two-operand row containing no letters — so this rival is "
                     "refuted on a sub-domain where the fold flag is entirely "
                     "irrelevant, which is what makes it an attack on the "
                     "COUNT sub-behavior rather than a second case-recognition "
                     "rival.",
        "witness": _witness("lineType", '"1 2".toList'),
    },
    {
        "id": "weak-maskflags-single-case-marker",
        "kind": "uniqueness",
        "expect": "reject",
        # The other method's fold flag, attacked head-on: the per-cell missing-
        # value decision recognizes the sentinel in one case only.
        "module": _mf("    return maskSeq false tokens\n"),
        "refinement": "a counterpart deciding the missing-value flag with a "
                      "single-case comparison leaves a sentinel cell written in "
                      "the other case unflagged, so it is instead parsed as a "
                      "number; the round-trip in the failing test then either "
                      "errors on the unparseable cell or produces a table whose "
                      "missing entries are absent, and the comparison against "
                      "the original still fails. It would NOT resolve.",
        "rationale": "REJECT from `out = maskSeq true tokens`: the post-image "
                     "demands the per-cell decision with case-folding ENABLED. "
                     "Refuted at `[\"nO\"]` — a single sentinel cell differing "
                     "from the canonical spelling only in its TRAILING "
                     "character, which the folded decision flags and the "
                     "unfolded one does not. That input is also the one the "
                     "near-miss rival below decides CORRECTLY (machine-checked: "
                     "this witness elaborates against this rival and FAILS "
                     "against weak-maskflags-first-char-fold), so the two "
                     "maskFlags case rivals are demonstrably refuted on "
                     "different sub-domains rather than on one shared point.",
        "witness": _witness("maskFlags", '["nO".toList]'),
    },
    {
        "id": "weak-maskflags-first-char-fold",
        "kind": "uniqueness",
        "expect": "reject",
        # NEAR-MISS of the rival above: folds the case of the sentinel's FIRST
        # character only and compares the remainder verbatim. So it agrees with
        # the spec on the fully-canonical spelling AND on the spelling that
        # differs only in the FIRST character — which is exactly the cell the
        # rival above is refuted at (`["nO"]`), handled correctly here. Its own
        # separating input is therefore a spelling whose REMAINDER differs in
        # case: the mixed-case cell.
        "module": _mf(
            "    return tokens.map (fun t =>\n"
            "      (t.take 1).map Char.toUpper = \"N\".toList "
            "&& t.drop 1 = \"O\".toList)\n"),
        "refinement": "a counterpart that folds only the sentinel's leading "
                      "character still misses the fully-other-case and "
                      "mixed-case spellings, so a hand-written table using "
                      "either leaves those cells unflagged and parsed as "
                      "numbers; the failing scenario's presentation is exactly "
                      "the fully-other-case one, so the round-trip still fails. "
                      "It would NOT resolve.",
        "rationale": "REJECT from `out = maskSeq true tokens`: the fold applies "
                     "to the WHOLE token, not a prefix of it. Refuted at "
                     "`[\"No\"]`, the mixed-case cell — the sub-domain that "
                     "separates this near-miss from "
                     "weak-maskflags-single-case-marker, since this rival flags "
                     "the canonical spelling and the "
                     "leading-character-only variant (`[\"nO\"]`, the point the "
                     "blunter rival is refuted at) correctly, and is wrong only "
                     "where the remainder's case differs. Machine-checked in "
                     "both directions: this rival ADMITS the `[\"nO\"]` witness "
                     "and is refuted by this one.",
        "witness": _witness("maskFlags", '["No".toList]'),
    },
    {
        "id": "weak-maskflags-drop-leading-cell",
        "kind": "uniqueness",
        "expect": "reject",
        # Attacks a sub-behavior no case rival touches: the element-wise
        # ALIGNMENT of the flag list with the row's cells. Every flag it does
        # emit is correct (and correctly case-folded); the list is simply
        # shifted, losing the leading cell. Refuted at a two-cell row, the
        # smallest input where a shift is observable.
        "module": _mf("    return (maskSeq true tokens).tail\n"),
        "refinement": "a counterpart that drops the leading cell's flag "
                      "mis-aligns every missing-value decision against the row "
                      "it came from, so a row whose FIRST cell is the sentinel "
                      "has that entry parsed as a number while a later entry is "
                      "flagged instead; the round-trip in the failing test then "
                      "compares a table whose missing entries sit in the wrong "
                      "columns and still fails. It would NOT resolve.",
        "rationale": "REJECT from `out = maskSeq true tokens`: the equation is "
                     "element-wise against the row, pinning both the flags and "
                     "their POSITIONS (and hence the list's length). Refuted at "
                     "`[\"1\", \"NO\"]` — a two-cell row with no case variation "
                     "at all, so the refutation is attributable to alignment "
                     "rather than to the fold flag the other two maskFlags "
                     "rivals attack.",
        "witness": _witness("maskFlags", '["1".toList, "NO".toList]'),
    },
    {
        "id": "weak-linetype-newblock-drop-length-guard",
        "kind": "uniqueness",
        "expect": "reject",
        # Attacks a branch of the ordered alternation NO other rival touches: the
        # break-marker shape's ARITY guard. Every reserved word is folded
        # correctly and every other branch is the modeled one; only the
        # requirement that a break marker carry at least two cells is weakened to
        # "at least one", so a ONE-cell row consisting solely of the marker is
        # mis-classified as a break instead of as a single-cell data row.
        # Refuted at a single upper-case marker cell, so the fold flag is
        # irrelevant to the refutation.
        "module": _lt(
            "    let s := stripWs line\n"
            "    let core := s.takeWhile (· ≠ '!')\n"
            "    let toks := words core\n"
            "    let r := if s = [] then LType.comment\n"
            "             else if isDirective true s then LType.command\n"
            "             else if toks.all (isMarkerTok true) && toks ≠ [] then "
            "LType.newblock\n"
            "             else if toks = [] then "
            "(if s.any (· = '!') then LType.comment else LType.reject)\n"
            "             else if toks.all (isDataTok true) then "
            "LType.data toks.length\n"
            "             else LType.reject\n"
            "    return r\n"),
        "refinement": "a counterpart that treats a one-cell all-marker row as a "
                      "table break rather than as a data row splits a table at "
                      "every row whose single cell is the sentinel, so a read of "
                      "any table containing one emits an extra empty table and "
                      "the surviving tables lose that row; the round-trip "
                      "comparison against the original then fails on table count "
                      "and row content, in BOTH the folded and unfolded "
                      "presentations. It would NOT resolve.",
        "rationale": "REJECT from `out = classify true line`: the alternation's "
                      "break-marker branch is guarded by an operand-count "
                      "condition that the post-image pins along with everything "
                      "else, and the modeled classifier requires at least two "
                      "cells there. Refuted at `\"NO\"`, a single canonical "
                      "marker cell: the post-image demands the data class with "
                      "count 1 and the rival answers the break class. The input "
                      "is fully upper-case, so this rival is refuted on a "
                      "sub-domain where the fold flag is irrelevant — it attacks "
                      "the ordered alternation's BRANCH GUARDS, a sub-behavior "
                      "no other rival here probes.",
        "witness": _witness("lineType", '"NO".toList'),
    },
    {
        "id": "weak-linetype-drop-signed-nan-cell",
        "kind": "uniqueness",
        "expect": "reject",
        # The sibling's dropped case, landed here after all (see the accounting
        # note): the data-cell grammar's not-a-number alternative admits an
        # OPTIONAL leading sign, and this rival drops it while folding case
        # correctly everywhere. Independent of the fold flag: refuted at a cell
        # written in the canonical lower case the unfolded comparison also
        # accepts.
        "module": _lt(
            "    let s := stripWs line\n"
            "    let core := s.takeWhile (· ≠ '!')\n"
            "    let toks := words core\n"
            "    let r := if s = [] then LType.comment\n"
            "             else if isDirective true s then LType.command\n"
            "             else if 2 ≤ toks.length && toks.all (isMarkerTok true) "
            "then LType.newblock\n"
            "             else if toks = [] then "
            "(if s.any (· = '!') then LType.comment else LType.reject)\n"
            "             else if toks.all (fun t => isDecimal t "
            "|| isMarkerTok true t\n"
            "                                        || eqFold true t "
            "\"nan\".toList) then\n"
            "               LType.data toks.length\n"
            "             else LType.reject\n"
            "    return r\n"),
        "refinement": "a counterpart whose data-cell grammar drops the SIGNED "
                      "not-a-number alternative rejects any row containing such "
                      "a cell, so reading a table that uses one aborts at line "
                      "classification instead of producing the row. The table in "
                      "THIS instance's failing scenario contains no such cell, so "
                      "this rival would not by itself keep that scenario failing "
                      "— but a companion scenario in the same suite reads a "
                      "table whose last row carries exactly that cell, and it "
                      "would abort there. So the sub-behavior is load-bearing for "
                      "the suite the change must not break, which is why the case "
                      "is shipped with the honest scope of its argument stated "
                      "rather than an overclaimed one.",
        "rationale": "REJECT from `out = classify true line`: the data-row "
                      "branch admits a cell that is a numeric literal, the "
                      "marker, or the not-a-number word WITH AN OPTIONAL SIGN, "
                      "and the post-image pins that alternation. Refuted at "
                      "`\"1 -nan\"`, where the post-image demands the data class "
                      "with count 2 and the rival rejects the line. The cell is "
                      "written in the canonical lower case, which the unfolded "
                      "comparison accepts too, so the refutation is attributable "
                      "to the dropped SIGN alternative and not to the fold flag "
                      "every other lineType rival probes.",
        "witness": _witness("lineType", '"1 -nan".toList'),
    },
]


# ---------------------------------------------------------------------------
# Sibling -> velvet accounting.
#
# The sibling battery ships 15 cases against 3 contracted leaf deciders
# (`masked_field`, `reserved_data_token`, `command_line`) over a per-code-point
# integer-sequence carrier under fractional-permission framing. This bundle
# contracts the SAME two changed behaviors at a coarser grain: ONE line
# classifier (`lineType`, which subsumes the sibling's `command_line` AND its
# `reserved_data_token` as the directive / data-token branches of a single
# modeled alternation) and ONE per-row missing-value decider (`maskFlags`, which
# subsumes `masked_field` element-wise over a row). So three sibling surfaces
# collapse into two obligations, and the sibling's five positive controls
# collapse correspondingly. Case-count parity is NOT the target; coverage of the
# surface THIS bundle models is.
#
#   sibling case                        -> here
#   ---------------------------------------------------------------------
#   pos-masked-branch-reorder           -> pos-maskflags-inline-fold-compare  PORTED
#   pos-command-branch-reorder          -> pos-linetype-blank-guard-first     PORTED
#   pos-masked-grounded-echo            \
#   pos-reserved-grounded-echo           > pos-maskflags-direct-map           MERGED
#   pos-command-grounded-echo           /
#   admiss-reserved-gold                -> admiss-classify-nondegenerate      RE-AIMED
#   frame-mutation-masked               \
#   frame-mutation-command               > (none)                             VACUOUS
#   frame-mutation-reserved             /
#   partial-masked-uppercase-only       -> weak-maskflags-single-case-marker  PORTED
#   partial-masked-no-and-NO-only       -> weak-maskflags-first-char-fold     PORTED
#   partial-command-uppercase-only      -> weak-linetype-single-case-         PORTED
#                                          recognition
#   partial-reserved-exact-spelling     -> weak-linetype-directive-only-fold  RE-AIMED
#   partial-reserved-drop-signed-nan    -> weak-linetype-drop-signed-nan-cell PORTED
#   (no counterpart)                    -> weak-linetype-operand-count-       ADDED
#                                          off-by-one
#   (no counterpart)                    -> weak-maskflags-drop-leading-cell   ADDED
#   (no counterpart)                    -> weak-linetype-newblock-drop-       ADDED
#                                          length-guard
#
# 6 ported, 3 merged into 1, 2 re-aimed, 3 vacuous, 3 added = 12 cases.
#
# PORTED (positives, 2): the sibling's two branch-reorder controls carry over as
#   reshapes of the two frozen impls — an explicit leading branch for the
#   classifier, and the raw case-folded comparison inlined in the row loop. Both
#   verify; both keep their `prove_correct` header and reprove honestly.
# MERGED (positives, 3 -> 1): the sibling ships one grounded-echo control per
#   decider, all three making the SAME argument (the post-image is grounded in
#   the argument, so the direct restatement is the cheapest CORRECT impl and
#   there is no ungrounded oracle to echo). That argument is about the SPEC's
#   shape, not about any one decider, and this bundle has two obligations rather
#   than three; `pos-maskflags-direct-map` carries it (and is a genuinely
#   different traversal — a forward map replacing a backward accumulator loop,
#   reproved by induction). Shipping a second copy against `lineType` would
#   restate the identical argument at the cost of another `lake` build; the
#   frozen `lineType` body is ALREADY the direct restatement, so an "echo"
#   variant of it would be the frozen impl verbatim.
# RE-AIMED (admissibility): the sibling establishes that a normal F2P-shaped
#   input satisfies the precondition. NEITHER method here carries a `require`
#   clause, so nothing could exclude a normal input and that probe is vacuous.
#   Re-aimed at the residual risk on a total domain: that the post-image is
#   unsatisfiable / degenerate at the interesting point. The case discharges a
#   live in-region assertion pinning TWO distinct non-trivial classifications.
# RE-AIMED (partial-reserved-exact-spelling): the sibling's third case-sensitive
#   rival attacks its third decider, which has no separate obligation here. Its
#   ARGUMENT — that single-case recognition of the data-row sentinel aborts the
#   read one line later than the directive failure does — survives as
#   weak-linetype-directive-only-fold, a sharper rival: rather than being
#   single-case everywhere (which the first lineType rival already covers) it
#   folds the directive correctly and leaves ONLY the data-row grammar
#   single-case, so it is refuted exactly on the sibling's sub-domain and
#   nowhere else.
# INEXPRESSIBLE (frame-mutation, 3): the sibling writes the half-permission input
#   to show the read-only frame is not vacuous. Not because velvet lacks mutation
#   (it has a `mut` parameter binder, used by other bundles here) but because
#   neither FROZEN signature declares one, and the binder sits in the method
#   signature — part of the spec view, which a variant may not touch. Machine-
#   checked both ways: adding `mut tokens` is out-of-scope (`same_spec failed`)
#   and does not elaborate (the frozen `ensures` loses its referent, `Unknown
#   identifier `tokens``); writing `tokens` from inside the impl region is in
#   scope but rejected by the compiler (`cannot be mutated, only variables
#   declared using `let mut``). No read-only input to overwrite, no substitute
#   probe. Not fabricated.
# PORTED (partial-reserved-drop-signed-nan -> weak-linetype-drop-signed-nan-cell):
#   the sibling refutes a rival that recognizes the sentinel and the
#   not-a-number word case-insensitively but drops the SIGNED not-a-number
#   alternative. That sub-behavior lives inside `isNanTok`, a `pure`-region
#   helper this bundle does not contract SEPARATELY — but it is reachable
#   through `lineType`, whose post-image pins the whole data-cell alternation,
#   and the rival is refutable there at a concrete literal row. An earlier
#   revision recorded this case as a known gap on the ground that its
#   `refinement` argument could not be made honestly, since the table in this
#   instance's failing scenario contains no signed not-a-number cell. The
#   premise is true and the conclusion did not follow: a companion scenario in
#   the same suite — one the change must not break — reads a table whose final
#   row carries exactly such a cell, so the sub-behavior IS load-bearing for the
#   suite even though the single failing scenario does not exercise it. The case
#   is therefore shipped with that scope stated exactly, which is stronger than
#   omitting a rival the carrier expresses fine.
# ADDED (3, no sibling counterpart): the sibling folds each decider's whole
#   verdict into one boolean, so it has no operand-count, no row-alignment and no
#   branch-guard sub-behavior to attack. This bundle's classifier carries an
#   operand COUNT in its data classification and an ordered alternation with
#   ARITY-guarded branches, and its row decider is an element-wise LIST, so all
#   three admit an attack independent of the case fold every other rival probes:
#   weak-linetype-operand-count-off-by-one (refuted at a letter-free row),
#   weak-maskflags-drop-leading-cell (refuted at a case-invariant two-cell row),
#   and weak-linetype-newblock-drop-length-guard (refuted at a single
#   fully-upper-case marker cell). These are what keep the battery from being
#   several spellings of one attack.
#
# COVERAGE. Both obligations are defended (>=1 verify) and attacked (>=1
# reject): `lineType` by 1 positive + 1 admissibility + 5 rivals, `maskFlags` by
# 2 positives + 3 rivals. Both input binders are varied by the reject witnesses
# across eight DISTINCT input points (five for `line`, three for `tokens`), and
# each independent sub-behavior of the two value clauses is attacked by some
# rival: the fold flag in each method, the ordered alternation between line
# shapes, the ARITY guard on the break-marker branch, the operand count, the
# data-cell alternation's optional sign, the whole-token exactness of the marker
# comparison, and the row alignment / length of the flag list. THREE of the five
# `lineType` rivals and one `maskFlags` rival are refuted on sub-domains where the
# fold flag is provably irrelevant — `"1 2"`, `"NO"`, `"1 -nan"` and `["1","NO"]`,
# each of which the folded and unfolded models classify IDENTICALLY, so the
# refutation cannot be inherited from the headline case behavior. The battery is
# therefore not several spellings of one attack. The two near-miss rivals are
# separated from their blunter counterparts in BOTH directions by real builds; see
# the WITNESS PLACEMENT note.
#
# AXIOM_TESTS: dropped. The axiom lane is G-AX's job; this bundle declares no
# `axiom` (both changed behaviors are deep models) and their soundness against
# the real callees lives in axiom_check.py.
AXIOM_TESTS = []
