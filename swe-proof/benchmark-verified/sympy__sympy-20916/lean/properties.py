"""properties.py — G-PBT falsification battery for sympy__sympy-20916 (lean).

NOT a Lean file; a record of adversarial cases the G-PBT gate executes. Each
SPEC case is a full ``Solution.lean`` variant that shares the FROZEN spec
byte-for-byte (region surgery: only text inside the ``-- impl-start`` /
``-- impl-end`` region — and, for a case that legitimately re-proves, inside the
``-- proof-start`` / ``-- proof-end`` region — is changed, so
``markers.same_spec`` holds and the single ``theorem correct_<name>`` STATEMENT
stays byte-identical). ``expect:"verify"`` passes iff (in scope AND the file
elaborates with the obligation closed); ``expect:"reject"`` passes iff (in scope
AND it does NOT verify AND the case's refutation ``witness`` holds of the rival
while FAILING on the frozen solution).

PORT NOTE. This is a PORT of the nagini falsification battery (see
``../nagini/properties.py``) onto this backend's carrier. The nagini bundle
models the split step with fractional-permission contracts over a
``List[int]`` code-point carrier and a family of GROUNDED ``@Pure`` folds
(``splits`` / ``split_point`` / ``num_leading_letters`` / ``all_digits``) that
compute the decision from the input. This Lean bundle models the SINGLE
purely-functional core: one total function over ``name : List Char`` returning
``List Char × Option (List Char)`` — the leading letter block paired with the
trailing digit block when the name splits, or the unchanged name with ``none``
otherwise. The nagini cases carry over as attacks on the one modeled clause; the
mapping of each nagini case to its Lean counterpart (or its principled omission)
is in the module ``assessment``.

DEFENDED SURFACE (one modeled behavior, one clause). The postcondition pins
``result`` to a single grounded computation over ``name``: ``result =
splitTrailingDigits name``. That computation has these observable decisions,
each selected by the input:

  * the SPLIT decision — a name splits exactly when its leading letter block is
    non-empty, the digit block that follows is non-empty, and what remains after
    the digits is empty or the single tolerated final newline;
  * the SPLIT VALUE — on a split, the base is the leading letter run and the
    subscript is the following digit run (the tolerated newline dropped, never
    part of the subscript);
  * the NO-SPLIT VALUE — otherwise the WHOLE name is returned unchanged with no
    subscript.

The BEHAVIOURAL DISCRIMINATOR (the fix): "letter" and "digit" are the FULL
character repertoire (any script — Greek, mathematical digits, …), not merely
the ASCII ranges. The pre-fix routine recognised only ASCII letters and ASCII
digits, so a Greek base or a non-ASCII decimal digit was left unsplit. The two
class-narrowing rivals below ARE that pre-fix behavior.

ADVERSARIAL READ of the case classes on this carrier:

  * FRAME / PERMISSION MUTATION — VACUOUS. Lean is referentially transparent: an
    input carries no heap permission, there is no read-only half-permission to
    overwrite and no aliasing to exploit. The nagini frame-mutation rival (a
    write into the read-only input under 1/2 permission) has no expressible
    instance here; no substitute is fabricated. (nagini case
    ``frame-mutation-write-name0``.)

  * UNGROUNDED-ORACLE ECHO — VACUOUS. Just as in nagini, the postcondition is
    GROUNDED: ``result`` is pinned equal to a term (``splitTrailingDigits
    name``) built only from the input. There is no opaque answer key an
    implementation could echo — the two character classes are ``opaque`` but the
    impl still has to select the branch and assemble the split from the input.
    In its place the battery carries honest POSITIVE CONTROLS that must verify
    (mirroring nagini's honest positive control) — two proof-neutral reshapes
    plus one genuinely different ALGORITHM whose proof the frozen `rfl` does
    NOT close, so the positive lane tests the obligation and not just the
    frozen definitional form.

  * PARTIAL-DOMAIN / VALUE — APPLIES. Rivals correct on part of the domain but
    diverging where the fix bites: recognising only ASCII letters, only ASCII
    digits, never splitting at all, splitting ALWAYS (the opposite error),
    cutting the base/subscript boundary one code point late, and corrupting the
    no-split value.

CONDITIONING ON THE CARRIER (why the witnesses take hypotheses). The two
character classes are ``opaque`` — ``isUnicodeLetter 'w'`` has no value ``decide``
can compute. So each reject witness states its refutation at a point DESCRIBED BY
HYPOTHESIS: it assumes only the classification facts it needs to separate the
rival from gold (e.g. ``isUnicodeLetter 'ω' = true`` — Greek is a letter — with
``isUnicodeDigit '1' = true``), then the split reduces concretely and the
divergence is ``decide``-able. Each hypothesis set was checked to be jointly
SATISFIABLE (the gate derives ``False`` from the binders alone and must fail):
every assumption is about a DISTINCT character, so none contradict. The
assumptions are exactly the real Unicode facts G-AX validates the opaque
signatures against, so they describe a real sub-domain, not a fictional one.

WITNESSES. On a tactic-proof backend "did not verify" is the DEFAULT outcome of
reshaping an implementation — the frozen ``rfl`` is tuned to the frozen form — so
a rejection alone attributes nothing to the spec. Every ``expect="reject"`` case
therefore carries a Lean snippet stating the spec predicate directly at one
concrete (conditioned) input and refuting it. Each was checked with two real
builds to HOLD of its rival and to FAIL on the frozen solution, so it
discriminates rather than asserting a tautology. Re-derived independently at
audit: for all six reject cases the gold-side build fails as a SEMANTIC
refutation (`decide` proving `¬ pure v = v` false for the concrete value v),
not as an unknown identifier, a type error or a stuck reduction, and each
hypothesis set's consistency probe fails as required.

BINDER / POINT SPREAD. The one spec input binder is ``name``. The reject
witnesses move it across genuinely distinct shapes rather than fixing one
convenient point: a two-char ASCII letters-then-digits name (``['w','1']``), a
Greek-letter base (``['ω','1']``), a mathematical-double-struck-digit subscript
(``['w','𝟙']``), a bare single-letter no-split name (``['w']``), a TWO-digit
subscript (``['w','1','1']`` — the shortest input at which the base/subscript CUT
POSITION is observable at all), and a letter-then-non-digit-tail name
(``['w','.']``). No two rivals share a refutation point; the six reject
witnesses probe six distinct inputs, and each probes a different facet of the
modeled computation (the ASCII letter class, the ASCII digit class, the
split-vs-no-split decision, the no-split value, the split VALUE's cut position,
and the post-digit trailer guard).

PORTED nagini cases that an earlier revision of this file recorded as folded in
(corrected — they are expressible here, and each was landed with two real
builds):

  * ``partial-domain-off-by-one`` (peel one extra code point) → the
    ``weak-off-by-one-boundary`` rival. NOT covered by the never-split /
    no-split-value rivals: both of those agree with the spec at every point
    where the CUT POSITION inside a splitting name is the only thing that
    differs, so before this rival the SPLIT VALUE clause had no attacker at all.
    Its refutation needs a two-digit subscript (a one-digit name cannot
    distinguish "cut after the letters" from "cut one code point later" when the
    off-by-one leaves an empty subscript that the guard still admits — see the
    witness comment).

  * ``partial-domain-greedy-overmatch`` (cut at the letter boundary even when
    the tail is not an all-digit run) → the ``weak-greedy-overmatch`` rival,
    refuted at a letter-then-non-digit-tail name. Also NOT covered by the
    never-split rival, which errs in the OPPOSITE direction (it under-splits;
    this one over-splits).

  * ``partial-domain-empty`` (always return empty base): ported as the
    ``weak-empty-base-on-nosplit`` rival, which corrupts the no-split value.

Two candidate rivals were considered and DROPPED as NOT verify-not-resolve on
this carrier: a rival that folds the tolerated final newline into the returned
subscript, and one that weakens the post-digit trailer test to "empty or ANY
single character". Every F2P input has an EMPTY post-digit trailer, so a rival
that changes ONLY what happens for a non-empty trailer agrees with gold on every
F2P case and WOULD resolve — such a rival tests spec strength beyond the F2P
surface, not verify-not-resolve, so shipping it as a uniqueness break would
misreport. (Both were nevertheless built and both are REJECTED by the spec, so
the drop costs no strength claim; they are simply out of this gate's remit.)

That reasoning does NOT cover dropping the guard, which is why
``weak-greedy-overmatch`` below is retained: removing the digit-run and trailer
requirements outright changes behavior on names with an EMPTY digit run, and
those ARE in the F2P set (every plain all-letter name token), so it diverges on
the F2P surface and is a true verify-not-resolve rival.

AXIOM lane: EMPTY here. The bundle declares two ``opaque`` classification leaves
(the unchanged, library-provided Unicode letter/digit predicates) validated
executably by G-AX (A-reference), and consumes no ``axiom``. The axiom lane
belongs to G-AX; this gate ignores it, and the nagini ``AXIOM_TESTS`` are
dropped.
"""
from pathlib import Path

INSTANCE = "sympy__sympy-20916"

_BASE = (Path(__file__).parent / "Solution.lean").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# ---- region anchors (each unique inside Solution.lean; verified at load) ----
# The whole impl body (inside the impl region). Editing it as one unit keeps the
# swap strictly inside the impl region so same_spec stays byte-identical.
_I_BODY = (
    "  let base := name.takeWhile isUnicodeLetter\n"
    "  let rest := name.dropWhile isUnicodeLetter\n"
    "  let digits := rest.takeWhile isUnicodeDigit\n"
    "  let trailer := rest.dropWhile isUnicodeDigit\n"
    "  if !base.isEmpty && !digits.isEmpty && (trailer.isEmpty || trailer == ['\\n']) then\n"
    "    return (base, some digits)\n"
    "  return (name, none)"
)

# The frozen proof body (inside the proof region).
_P_FROZEN = "  intro name\n  rfl"


SPEC_TESTS = [
    # =====================================================================
    # POSITIVE CONTROLS (soundness) — structurally different but CORRECT
    # implementations that MUST verify. If a faithful correct implementation
    # cannot satisfy the frozen obligation the spec is SPEC-TOO-STRONG. Each
    # keeps the theorem statement byte-identical and preserves the definitional
    # form so the frozen `intro name; rfl` still closes (no helper lemma, no
    # axiom, no assumption token introduced). Ports nagini's
    # `pos-control-reorder` (a proof-neutral control-flow reorder of the branch
    # selection) to the single modeled function.
    # =====================================================================
    {
        "id": "pos-explicit-else",
        "kind": "soundness",
        "expect": "verify",
        # Make the fall-through no-split return an explicit `else` branch instead
        # of a post-`if` statement. Same value on every input; the definitional
        # unfolding is identical, so the frozen `rfl` closes.
        "module": _swap(
            _BASE, _I_BODY,
            "  let base := name.takeWhile isUnicodeLetter\n"
            "  let rest := name.dropWhile isUnicodeLetter\n"
            "  let digits := rest.takeWhile isUnicodeDigit\n"
            "  let trailer := rest.dropWhile isUnicodeDigit\n"
            "  if !base.isEmpty && !digits.isEmpty && (trailer.isEmpty || trailer == ['\\n']) then\n"
            "    return (base, some digits)\n"
            "  else\n"
            "    return (name, none)",
        ),
        "rationale": "the branch selection is reshaped from an early `return` "
                     "with a post-`if` fall-through to an explicit `if/else`; the "
                     "returned value is identical on every input, so `result = "
                     "splitTrailingDigits name` still holds and the frozen `intro "
                     "name; rfl` closes (both forms `Id.run`-reduce to the same "
                     "`ite`). Must verify, else the modeled clause is "
                     "SPEC-TOO-STRONG. Ports nagini's control-flow-reorder "
                     "positive control to the single modeled function.",
    },
    {
        "id": "pos-default-then-override",
        "kind": "soundness",
        "expect": "verify",
        # Default the result to the no-split value, then override to the split on
        # a successful match (the imperative default-then-override shape). Same
        # value on every input; the frozen `rfl` closes.
        "module": _swap(
            _BASE, _I_BODY,
            "  let base := name.takeWhile isUnicodeLetter\n"
            "  let rest := name.dropWhile isUnicodeLetter\n"
            "  let digits := rest.takeWhile isUnicodeDigit\n"
            "  let trailer := rest.dropWhile isUnicodeDigit\n"
            "  let mut result := (name, none)\n"
            "  if !base.isEmpty && !digits.isEmpty && (trailer.isEmpty || trailer == ['\\n']) then\n"
            "    result := (base, some digits)\n"
            "  return result",
        ),
        "rationale": "the branch selection is reshaped to default-then-override "
                     "(initialise to the no-split value, overwrite on a match); "
                     "the returned value is identical on every input, so `result "
                     "= splitTrailingDigits name` still holds and the frozen "
                     "`intro name; rfl` closes after the `mut` local reduces. "
                     "Must verify. Defends the modeled clause with a second "
                     "correct reshape (a different imperative shape than the "
                     "explicit-else positive), mirroring nagini's "
                     "default-then-override reorder.",
    },
    {
        "id": "pos-recursive-span",
        "kind": "soundness",
        "expect": "verify",
        # A genuinely DIFFERENT ALGORITHM, not a reshape: instead of two
        # takeWhile/dropWhile pairs (four traversals), one recursive `span` pass
        # per class returns the prefix and the remainder together. The frozen
        # `rfl` does NOT close this — the two spans have to be proven equal to
        # takeWhile/dropWhile by induction — so unlike the two positives above
        # this one exercises the obligation rather than riding the frozen
        # definitional form. Added by audit: both pre-existing positives were
        # `rfl`-identical to the frozen impl, so a spec that only ever admitted
        # its own syntactic shape would have passed them.
        "module": _swap(
            _swap(
                _BASE, _I_BODY,
                "  let rec spanL : List Char → List Char × List Char\n"
                "    | [] => ([], [])\n"
                "    | c :: cs => if isUnicodeLetter c then\n"
                "        let (a, b) := spanL cs; (c :: a, b) else ([], c :: cs)\n"
                "  let rec spanD : List Char → List Char × List Char\n"
                "    | [] => ([], [])\n"
                "    | c :: cs => if isUnicodeDigit c then\n"
                "        let (a, b) := spanD cs; (c :: a, b) else ([], c :: cs)\n"
                "  let (base, rest) := spanL name\n"
                "  let (digits, trailer) := spanD rest\n"
                "  if !base.isEmpty && !digits.isEmpty && (trailer.isEmpty || trailer == ['\\n']) then\n"
                "    return (base, some digits)\n"
                "  return (name, none)",
            ),
            _P_FROZEN,
            "  intro name\n"
            "  have hL : ∀ (l : List Char),\n"
            "      implementation_splitTrailingDigits.spanL l\n"
            "        = (l.takeWhile isUnicodeLetter, l.dropWhile isUnicodeLetter) := by\n"
            "    intro l; induction l with\n"
            "    | nil => rfl\n"
            "    | cons c cs ih =>\n"
            "      by_cases h : isUnicodeLetter c = true <;>\n"
            "        simp [implementation_splitTrailingDigits.spanL, List.takeWhile_cons,\n"
            "          List.dropWhile_cons, h, ih]\n"
            "  have hD : ∀ (l : List Char),\n"
            "      implementation_splitTrailingDigits.spanD l\n"
            "        = (l.takeWhile isUnicodeDigit, l.dropWhile isUnicodeDigit) := by\n"
            "    intro l; induction l with\n"
            "    | nil => rfl\n"
            "    | cons c cs ih =>\n"
            "      by_cases h : isUnicodeDigit c = true <;>\n"
            "        simp [implementation_splitTrailingDigits.spanD, List.takeWhile_cons,\n"
            "          List.dropWhile_cons, h, ih]\n"
            "  simp only [problem_spec_splitTrailingDigits,\n"
            "    implementation_splitTrailingDigits, splitTrailingDigits, Id.run, hL, hD]\n"
            "  rfl",
        ),
        "rationale": "a correct implementation with a DIFFERENT ALGORITHM, not a "
                     "different spelling: one recursive single-pass `span` per "
                     "character class (returning prefix and remainder together) "
                     "replaces the four takeWhile/dropWhile traversals. The frozen "
                     "`rfl` does NOT close it; the proof re-establishes each span "
                     "equals its takeWhile/dropWhile pair by induction and then "
                     "closes the obligation. Must verify, else the modeled clause "
                     "is SPEC-TOO-STRONG — pinning the frozen definitional form "
                     "rather than the behavior. This is the positive that actually "
                     "tests that: the other two are `rfl`-identical to the frozen "
                     "impl by construction. Only the impl and proof regions change; "
                     "the theorem statement is byte-identical and no axiom, `sorry` "
                     "or new top-level declaration is introduced (`spanL`/`spanD` "
                     "are `let rec`s inside the impl).",
    },

    # =====================================================================
    # ADMISSIBILITY — a positive control confirming the obligation is
    # SATISFIABLE (non-vacuous) at the normal, F2P-shaped input rather than only
    # in the abstract. The frozen theorem carries NO precondition hypothesis
    # (the modeled behavior is total, so `∀` is unguarded), so the nagini
    # precondition-admission probe (`admiss-w1`) has no binder to attack here;
    # the honest analogue discharges the modeled result at the ground F2P input
    # "w1" (the code points ['w','1']) to its expected split value, alongside the
    # frozen obligation. Because the classes are opaque, the ground fact is
    # stated under the real Unicode hypotheses G-AX validates. Ports nagini's
    # `admiss-w1`.
    # =====================================================================
    {
        "id": "admiss-w1-split",
        "kind": "admissibility",
        "expect": "verify",
        # Establish, as a `have` inside the frozen tactic body, that the modeled
        # function maps the F2P input ['w','1'] to its expected split value
        # (['w'], some ['1']) under the real Unicode classification facts, then
        # close the frozen obligation verbatim. Nothing is assumed at top level:
        # no new declaration, statement byte-identical, the ground instance is a
        # local `have` inside the existing tactic body.
        "module": _swap(
            _BASE, _P_FROZEN,
            "  have _admiss_w1 : ∀ (_hw : isUnicodeLetter 'w' = true)\n"
            "      (_h1 : isUnicodeLetter '1' = false) (_hd : isUnicodeDigit '1' = true),\n"
            "      implementation_splitTrailingDigits ['w', '1'] = (['w'], some ['1']) := by\n"
            "    intro _hw _h1 _hd\n"
            "    simp [implementation_splitTrailingDigits, Id.run, _hw, _h1, _hd]\n"
            "    decide\n"
            + _P_FROZEN,
        ),
        "rationale": "the modeled result is discharged at the ground F2P input "
                     "(the code points of \"w1\") to its expected split value "
                     "(['w'], some ['1']) under the real Unicode classification "
                     "facts, then the frozen obligation is closed verbatim. "
                     "Verifies (else the modeled behavior is unsatisfiable at "
                     "exactly the input the F2P exercises — the analogue of "
                     "PRECOND-TOO-STRONG). Nothing is assumed: no new "
                     "declaration, the theorem statement is byte-identical, and "
                     "the ground instance is a local `have` inside the existing "
                     "tactic body. Ports nagini's admissibility probe.",
    },

    # =====================================================================
    # UNIQUENESS / SPEC-TOO-WEAK rivals — wrong implementations sharing the
    # frozen spec that MUST be rejected. Each carries (a) the refinement
    # argument that its faithful real patch would NOT resolve the F2P, so a
    # verifying rival would be a true verify-does-not-imply-resolve break rather
    # than an artifact, and (b) a refutation witness pinning the violation at one
    # concrete (conditioned) input, checked to hold of the rival and fail on gold.
    # =====================================================================

    # ---- the fix itself, letter side: recognise only ASCII letters --------
    {
        "id": "weak-ascii-letters-only",
        "kind": "uniqueness",
        "expect": "reject",
        # Pre-fix behavior on the LETTER class: use the ASCII-only letter
        # predicate for the leading block, so a non-ASCII (e.g. Greek) letter is
        # not recognised as a letter and the name is left unsplit.
        "module": _swap(
            _BASE, _I_BODY,
            "  let base := name.takeWhile Char.isAlpha\n"
            "  let rest := name.dropWhile Char.isAlpha\n"
            "  let digits := rest.takeWhile isUnicodeDigit\n"
            "  let trailer := rest.dropWhile isUnicodeDigit\n"
            "  if !base.isEmpty && !digits.isEmpty && (trailer.isEmpty || trailer == ['\\n']) then\n"
            "    return (base, some digits)\n"
            "  return (name, none)",
        ),
        "refinement": "this IS one half of the pre-fix behavior: recognising only "
                      "ASCII letters `a`–`z`/`A`–`Z` for the base. On a Greek-base "
                      "name like \"ω1\" the leading block is empty, so no split "
                      "happens and it returns (\"ω1\", none). The F2P test asserts "
                      "a Greek-base name peels its trailing digit run as a "
                      "subscript, so the faithful real patch would NOT resolve — "
                      "this is exactly the unformatted-Greek-subscript symptom "
                      "the issue reports.",
        "rationale": "REJECT from the split-decision clause on the letter class: "
                     "the spec uses the full-repertoire letter predicate (Greek is "
                     "a letter → split) while the rival uses the ASCII-only "
                     "predicate (Greek not a letter → no split), so at a "
                     "Greek-base input `result` differs. Binder: name = ['ω','1']. "
                     "Witness conditions on the real facts isUnicodeLetter 'ω' = "
                     "true, isUnicodeDigit '1' = true.",
        "witness": (
            "-- Refuted at a Greek-base name. Conditioned on the real Unicode\n"
            "-- classification: 'ω' IS a letter and '1' IS a digit, so gold splits\n"
            "-- to (['ω'], some ['1']) while the ASCII-only rival leaves it\n"
            "-- unsplit as (['ω','1'], none). The hypotheses are about distinct\n"
            "-- characters, so they are jointly satisfiable (no False derivable).\n"
            "example (hw : isUnicodeLetter 'ω' = true) (h1 : isUnicodeLetter '1' = false)\n"
            "        (hd1 : isUnicodeDigit '1' = true) :\n"
            "    ¬ problem_spec_splitTrailingDigits ['ω','1']\n"
            "        (implementation_splitTrailingDigits ['ω','1']) := by\n"
            "  simp [problem_spec_splitTrailingDigits, implementation_splitTrailingDigits,\n"
            "    Id.run, splitTrailingDigits, hw, h1, hd1]\n"
            "  decide\n"
        ),
    },

    # ---- the fix itself, digit side: recognise only ASCII digits ----------
    {
        "id": "weak-ascii-digits-only",
        "kind": "uniqueness",
        "expect": "reject",
        # Pre-fix behavior on the DIGIT class: use the ASCII-only digit predicate
        # for the trailing block, so a non-ASCII decimal digit (e.g. a
        # mathematical double-struck digit) is not recognised and the name is
        # left unsplit.
        "module": _swap(
            _BASE, _I_BODY,
            "  let base := name.takeWhile isUnicodeLetter\n"
            "  let rest := name.dropWhile isUnicodeLetter\n"
            "  let digits := rest.takeWhile Char.isDigit\n"
            "  let trailer := rest.dropWhile Char.isDigit\n"
            "  if !base.isEmpty && !digits.isEmpty && (trailer.isEmpty || trailer == ['\\n']) then\n"
            "    return (base, some digits)\n"
            "  return (name, none)",
        ),
        "refinement": "this IS the other half of the pre-fix behavior: recognising "
                      "only ASCII digits `0`–`9` for the trailing block. On a name "
                      "whose subscript is a non-ASCII decimal digit like \"w𝟙\" "
                      "(𝟙 = U+1D7D9 MATHEMATICAL DOUBLE-STRUCK DIGIT ONE) the digit "
                      "block is empty, so no split happens and it returns "
                      "(\"w𝟙\", none). The F2P test asserts that such a name peels "
                      "\"𝟙\" as its subscript, so the faithful real patch would "
                      "NOT resolve.",
        "rationale": "REJECT from the split-decision clause on the digit class: "
                     "the spec uses the full-repertoire digit predicate (𝟙 is a "
                     "digit → split) while the rival uses the ASCII-only predicate "
                     "(𝟙 not a digit → no split), so at a non-ASCII-digit input "
                     "`result` differs. Binder: name = ['w','𝟙'], moving the "
                     "subscript to a non-ASCII decimal digit. Witness conditions "
                     "on isUnicodeLetter 'w' = true, isUnicodeDigit '𝟙' = true.",
        "witness": (
            "-- Refuted at a mathematical-double-struck-digit subscript. Conditioned\n"
            "-- on the real classification: 'w' IS a letter and '𝟙' (U+1D7D9) IS a\n"
            "-- decimal digit, so gold splits to (['w'], some ['𝟙']) while the\n"
            "-- ASCII-only-digit rival leaves it unsplit as (['w','𝟙'], none).\n"
            "-- Distinct characters → jointly satisfiable.\n"
            "example (hw : isUnicodeLetter 'w' = true) (hL2 : isUnicodeLetter '𝟙' = false)\n"
            "        (hd : isUnicodeDigit '𝟙' = true) :\n"
            "    ¬ problem_spec_splitTrailingDigits ['w','𝟙']\n"
            "        (implementation_splitTrailingDigits ['w','𝟙']) := by\n"
            "  simp [problem_spec_splitTrailingDigits, implementation_splitTrailingDigits,\n"
            "    Id.run, splitTrailingDigits, hw, hL2, hd]\n"
            "  decide\n"
        ),
    },

    # ---- the split decision itself: never split (nagini partial-domain B) ----
    {
        "id": "weak-never-split",
        "kind": "uniqueness",
        "expect": "reject",
        # Ignore the trailing-digit exception entirely: always return the whole
        # name unchanged with no subscript.
        "module": _swap(
            _BASE, _I_BODY,
            "  return (name, none)",
        ),
        "refinement": "a faithful real patch that dropped the trailing-digit "
                      "exception entirely would leave every name unsplit, so "
                      "\"w1\" would keep its whole name and peel nothing. The F2P "
                      "test asserts a peeled subscript on every splitting case "
                      "(\"w1\", \"w11\", \"ω1\", …), so the faithful patch would "
                      "NOT resolve.",
        "rationale": "REJECT from the split-decision / split-value clause: on an "
                     "input that DOES split (non-empty letter run, non-empty digit "
                     "run, empty trailer) the spec peels (['w'], some ['1']) while "
                     "the rival returns the whole name (['w','1'], none), so "
                     "`result` differs. Binder: name = ['w','1'] (the canonical "
                     "ASCII splitting case). Witness conditions on isUnicodeLetter "
                     "'w' = true, isUnicodeDigit '1' = true.",
        "witness": (
            "-- Refuted at the canonical ASCII splitting name. Conditioned on the\n"
            "-- real classification: 'w' IS a letter, '1' IS a digit and not a\n"
            "-- letter, so gold splits to (['w'], some ['1']) while the never-split\n"
            "-- rival returns (['w','1'], none). Distinct characters → satisfiable.\n"
            "example (hw : isUnicodeLetter 'w' = true) (h1 : isUnicodeLetter '1' = false)\n"
            "        (hd1 : isUnicodeDigit '1' = true) :\n"
            "    ¬ problem_spec_splitTrailingDigits ['w','1']\n"
            "        (implementation_splitTrailingDigits ['w','1']) := by\n"
            "  simp [problem_spec_splitTrailingDigits, implementation_splitTrailingDigits,\n"
            "    Id.run, splitTrailingDigits, hw, h1, hd1]\n"
            "  decide\n"
        ),
    },

    # ---- the no-split value: corrupt to empty (nagini partial-domain C/empty) ----
    {
        "id": "weak-empty-base-on-nosplit",
        "kind": "uniqueness",
        "expect": "reject",
        # Corrupt the no-split value: return an EMPTY name (not the unchanged
        # input) when the name does not split. Split cases are unchanged, so this
        # is a partial-domain miss on exactly the no-split branch.
        "module": _swap(
            _BASE, _I_BODY,
            "  let base := name.takeWhile isUnicodeLetter\n"
            "  let rest := name.dropWhile isUnicodeLetter\n"
            "  let digits := rest.takeWhile isUnicodeDigit\n"
            "  let trailer := rest.dropWhile isUnicodeDigit\n"
            "  if !base.isEmpty && !digits.isEmpty && (trailer.isEmpty || trailer == ['\\n']) then\n"
            "    return (base, some digits)\n"
            "  return ([], none)",
        ),
        "refinement": "a faithful real patch that emptied the base on the no-split "
                      "path would corrupt the parsed name token for every name "
                      "that is NOT a clean letters-then-digits shape — e.g. a bare "
                      "letter name \"w\" → (\"\", …) instead of (\"w\", …). The "
                      "test asserts the unchanged name on the no-split cases "
                      "(the empty name stays empty, and so does the surrounding "
                      "parse of every non-splitting token), so the faithful "
                      "patch would NOT resolve.",
        "rationale": "REJECT from the no-split-value clause: on a name that does "
                     "NOT split the spec returns the WHOLE name unchanged (['w'], "
                     "none) while the rival returns ([], none), so `result` "
                     "differs. Binder: name = ['w'] (a bare single-letter name, "
                     "no digit run → no split), a distinct input from every other "
                     "rival. Witness conditions on isUnicodeLetter 'w' = true.",
        "witness": (
            "-- Refuted at a bare single-letter no-split name. Conditioned on the\n"
            "-- real classification: 'w' IS a letter, so gold leaves it unchanged\n"
            "-- as (['w'], none) (no digit run follows) while the rival empties the\n"
            "-- base to ([], none). One hypothesis about one character → satisfiable.\n"
            "example (hw : isUnicodeLetter 'w' = true) :\n"
            "    ¬ problem_spec_splitTrailingDigits ['w']\n"
            "        (implementation_splitTrailingDigits ['w']) := by\n"
            "  simp [problem_spec_splitTrailingDigits, implementation_splitTrailingDigits,\n"
            "    Id.run, splitTrailingDigits, hw]\n"
            "  decide\n"
        ),
    },

    # ---- the split VALUE's cut position (nagini partial-domain A/off-by-one) ----
    # Added by audit: before this rival the SPLIT VALUE clause had no attacker.
    # Every other reject case above differs from the spec in WHICH BRANCH it
    # takes or in what it returns on the no-split branch; none of them moves the
    # boundary INSIDE a name that does split, so "the base is the leading letter
    # run and the subscript is exactly the digit run that follows" was asserted
    # in the docstring and demonstrated by nothing.
    {
        "id": "weak-off-by-one-boundary",
        "kind": "uniqueness",
        "expect": "reject",
        # Take the split decision exactly as the spec does, but cut ONE CODE
        # POINT LATE: the first digit is folded into the base and the subscript
        # is the remaining digits. Identical to the spec on every non-splitting
        # name, so this is a partial-domain miss on exactly the split value.
        "module": _swap(
            _BASE, _I_BODY,
            "  let base := name.takeWhile isUnicodeLetter\n"
            "  let rest := name.dropWhile isUnicodeLetter\n"
            "  let digits := rest.takeWhile isUnicodeDigit\n"
            "  let trailer := rest.dropWhile isUnicodeDigit\n"
            "  if !base.isEmpty && !digits.isEmpty && (trailer.isEmpty || trailer == ['\\n']) then\n"
            "    return (base ++ digits.take 1, some (digits.drop 1))\n"
            "  return (name, none)",
        ),
        "refinement": "a faithful real patch whose base group greedily ate one "
                      "digit too many would return the wrong pair on EVERY "
                      "splitting name: \"w11\" → base \"w1\" with subscript "
                      "\"1\" instead of base \"w\" with subscript \"11\". The "
                      "F2P test asserts the base is the letters ALONE on every "
                      "splitting case (\"w1\", \"w11\", \"w𝟙2𝟙\", \"ω1\", "
                      "\"ω𝟙2^3α\", …) — checked: the rival's value differs from "
                      "the spec's on every one of those name tokens — so the "
                      "faithful patch would NOT resolve.",
        "rationale": "REJECT from the SPLIT VALUE clause (`base` = the leading "
                     "letter run, subscript = the digit run that follows): the "
                     "split DECISION is identical to the spec's, so this rival "
                     "isolates the cut position and nothing else. Binder: name = "
                     "['w','1','1'] — a TWO-digit subscript, which is the "
                     "shortest input that observes the cut at all (with a "
                     "one-digit subscript the rival returns an empty subscript "
                     "`some []`, still a divergence, but the two-digit point "
                     "shows the digits being MISPARTITIONED rather than merely "
                     "emptied). Distinct from every other rival's input. Witness "
                     "conditions on isUnicodeLetter 'w' = true, isUnicodeLetter "
                     "'1' = false, isUnicodeDigit '1' = true.",
        "witness": (
            "-- Refuted at a TWO-digit subscript — the shortest input at which the\n"
            "-- base/subscript CUT POSITION is observable. Conditioned on the real\n"
            "-- classification: 'w' IS a letter, '1' IS a digit and not a letter, so\n"
            "-- gold peels (['w'], some ['1','1']) while the off-by-one rival folds\n"
            "-- one digit into the base: (['w','1'], some ['1']). The hypotheses are\n"
            "-- about two distinct characters, so they are jointly satisfiable.\n"
            "example (hw : isUnicodeLetter 'w' = true) (h1 : isUnicodeLetter '1' = false)\n"
            "        (hd1 : isUnicodeDigit '1' = true) :\n"
            "    ¬ problem_spec_splitTrailingDigits ['w','1','1']\n"
            "        (implementation_splitTrailingDigits ['w','1','1']) := by\n"
            "  simp [problem_spec_splitTrailingDigits, implementation_splitTrailingDigits,\n"
            "    Id.run, splitTrailingDigits, hw, h1, hd1]\n"
            "  decide\n"
        ),
    },

    # ---- the split GUARD: over-split (nagini partial-domain D/greedy) ----------
    # Added by audit: the never-split rival errs by under-splitting, so nothing
    # in the battery attacked the OPPOSITE error — peeling a "subscript" off a
    # name that has no digit run at all, i.e. dropping the digit-run and trailer
    # requirements from the guard.
    {
        "id": "weak-greedy-overmatch",
        "kind": "uniqueness",
        "expect": "reject",
        # Split whenever the leading letter block is non-empty, ignoring both the
        # non-empty-digit-run requirement and the post-digit trailer test. Cuts
        # at the letter/non-letter boundary even when what follows is not a digit
        # run at all.
        "module": _swap(
            _BASE, _I_BODY,
            "  let base := name.takeWhile isUnicodeLetter\n"
            "  let rest := name.dropWhile isUnicodeLetter\n"
            "  let digits := rest.takeWhile isUnicodeDigit\n"
            "  let trailer := rest.dropWhile isUnicodeDigit\n"
            "  if !base.isEmpty then\n"
            "    return (base, some digits)\n"
            "  return (name, none)",
        ),
        "refinement": "a faithful real patch that cut at the letter/non-letter "
                      "boundary unconditionally would peel a subscript off names "
                      "that have no trailing digit run at all: a plain letters-only "
                      "token like \"beta\" would come back with an (empty) "
                      "subscript attached instead of untouched, and a "
                      "letter-then-punctuation token would lose its tail. Plain "
                      "letters-only tokens ARE in the F2P set (\"beta\", \"x\", "
                      "\"alpha\", …) — checked: the rival's value differs from the "
                      "spec's on every one of them — so the faithful patch would "
                      "NOT resolve. This is the case the newline/trailer-tolerance "
                      "rivals are dropped for and this one is not: its divergence "
                      "is on the F2P surface, not only beyond it.",
        "rationale": "REJECT from the SPLIT DECISION clause, in the OVER-split "
                     "direction (the never-split rival covers only the under-split "
                     "direction): the spec requires a non-empty digit run AND an "
                     "empty-or-single-newline trailer before it peels anything, "
                     "while the rival peels on a non-empty letter block alone. "
                     "Binder: name = ['w','.'] — a letter followed by a character "
                     "that is neither a letter nor a digit, so the spec does NOT "
                     "split (empty digit run) and returns the whole name, while "
                     "the rival returns (['w'], some []). A distinct input from "
                     "every other rival's, and the only one whose witness "
                     "conditions on a character that is in NEITHER class. Witness "
                     "conditions on isUnicodeLetter 'w' = true, isUnicodeLetter "
                     "'.' = false, isUnicodeDigit '.' = false.",
        "witness": (
            "-- Refuted at a letter followed by a NON-digit, NON-letter character —\n"
            "-- the shape the spec's digit-run/trailer guard exists to exclude.\n"
            "-- Conditioned on the real classification: 'w' IS a letter while '.' is\n"
            "-- neither a letter nor a digit, so gold leaves the name unchanged as\n"
            "-- (['w','.'], none) while the greedy rival peels (['w'], some []).\n"
            "-- The hypotheses are about two distinct characters and assign each\n"
            "-- character a single class, so they are jointly satisfiable.\n"
            "example (hw : isUnicodeLetter 'w' = true) (hl2 : isUnicodeLetter '.' = false)\n"
            "        (hd2 : isUnicodeDigit '.' = false) :\n"
            "    ¬ problem_spec_splitTrailingDigits ['w','.']\n"
            "        (implementation_splitTrailingDigits ['w','.']) := by\n"
            "  simp [problem_spec_splitTrailingDigits, implementation_splitTrailingDigits,\n"
            "    Id.run, splitTrailingDigits, hw, hl2, hd2]\n"
            "  decide\n"
        ),
    },
]

# No AXIOM lane here: the bundle consumes no `axiom` (two `opaque` classification
# leaves — the unchanged, library-provided Unicode letter/digit predicates — are
# A-references validated by G-AX, not consumed contracts). The nagini
# AXIOM_TESTS belong to the axiom lane (G-AX); dropped.
AXIOM_TESTS = []
