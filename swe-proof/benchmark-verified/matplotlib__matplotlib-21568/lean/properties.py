"""properties.py — G-PBT falsification battery for matplotlib__matplotlib-21568 (lean).

NOT a Lean file; a record of adversarial cases the G-PBT gate executes. Each
SPEC case is a full ``Solution.lean`` variant that shares the FROZEN spec
byte-for-byte (region surgery: only text inside the ``-- impl-start`` /
``-- impl-end`` region — and, for the soundness positive that legitimately
re-proves, inside the ``-- proof-start`` / ``-- proof-end`` region — is changed,
so ``markers.same_spec`` holds and the ``theorem correct_<name>`` STATEMENT
stays byte-identical). ``expect:"verify"`` passes iff (in scope AND the file
elaborates with the obligation closed); ``expect:"reject"`` passes iff (in scope
AND it does NOT verify AND the case's refutation ``witness`` holds of the rival
while FAILING on the frozen solution).

DEFENDED SURFACE (one total function over a single input binder):

  texLabel (text : List Char) : List Char
      result = texLabel text

  where ``texLabel`` is the fully-grounded four-stage label transform:
    1. lift each maximal run of ASCII letters out of the math-default group
       (``bracketLetterRuns``);
    2. rewrite each remaining symbol per a fixed table (``escapeMathSym``):
       hyphen ↦ ``{-}``, colon ↦ ``{:}``, space ↦ ``\\;``, everything else
       verbatim;
    3. wrap the whole thing in one outer math-default group;
    4. delete any resulting empty math-default group (``dropToken``).

  The single top-level clause ``result = texLabel text`` pins the WHOLE output to
  a total function of the one input binder — there is no opaque callee and no
  answer-key: ``texLabel`` computes. Every input character's contribution is
  fixed, so each of the three symbol-rewrite decisions (hyphen, colon, space) is
  independently observable, as is the ORDER of the two code points a space
  rewrites to.

ADVERSARIAL READ of the nagini classes on this carrier:

  * FRAME / PERMISSION MUTATION — VACUOUS. The nagini sibling makes an
    input-write attack MANDATORY because the modeled input is held at fractional
    (read-only) permission, so a rival that stores through it is rejected for
    insufficient permission. Lean is referentially transparent: ``text`` is a
    plain immutable ``List Char``, there is no half-permission to violate and no
    aliasing to exploit, so this class has NO expressible instance here. No
    substitute is fabricated for it (mirrors nagini case #1).

  * UNGROUNDED-ORACLE ECHO — VACUOUS, exactly as the nagini sibling records: the
    postcondition equates the result to ``texLabel text``, a GROUNDED total fold
    of the input (no opaque answer-key to echo), so any echo of it IS the correct
    answer. The bundle declares no ``opaque``/``axiom`` (the one nontrivial
    callee, the run-lifting substitution, is modeled DEEPLY as
    ``bracketLetterRuns`` and validated by G-AX, not axiomatized). The honest
    analogue is the cheapest-correct POSITIVE CONTROL below (mirrors nagini
    case #6).

  * PARTIAL-DOMAIN (drop one of the three symbol rewrites) — APPLIES, and is the
    load-bearing rival family. A rival that omits the space rewrite, the colon
    rewrite, or the hyphen rewrite is correct on every label lacking that symbol
    but diverges on any label containing it. (Nagini cases #2, #3; the hyphen
    variant is the prepatch-class defect that G-DIFF already owns, added here for
    per-decision binder coverage.)

  * STAGE-OMISSION (drop the run-lifting stage) — APPLIES, and is the only rival
    family that attacks a stage OTHER than the symbol table. All five rivals
    above reshape stage 2 only; stage 1 (``bracketLetterRuns``, the one
    nontrivial deeply-modeled operation, the A-reference G-AX validates) was
    left entirely unprobed by the reject lane, so the battery attested nothing
    about the spec's dependence on it. ``weak-skip-letter-lift`` closes that: it
    keeps the whole symbol table and drops only the lift, which is observable at
    any label bearing an alphabetic run. Added by audit.

  * WRONG-TOKEN (space code points swapped) — APPLIES. Emitting the space token
    with its two code points in the wrong order is correct on space-free labels
    and wrong at any space (mirrors nagini case #4).

  * POSITIONAL / ONLY-FIRST-OCCURRENCE — APPLIES. A rival that bounds the symbol
    rewrite to ONE hit (the first protected symbol is rewritten, later ones pass
    through bare) is correct on every label bearing at most one protected symbol
    and wrong on any label bearing two or more. This is the positional analogue
    of nagini case #5, but deliberately NOT a transliteration of it: nagini's
    rival exempts one distinguished POSITION (the tail element of its backward
    loop), and on this behavior no exercised label has a protected symbol at the
    distinguished position — so a faithful patch with that off-by-one still
    produces every expected label and WOULD resolve, which a reject case may not
    claim. Bounding the rewrite by COUNT rather than by position keeps the
    positional character while changing three separate exercised label groups
    (two-hyphen dates, hyphen-plus-space, space-plus-colon), each of which bears
    two protected symbols. See the AUDIT NOTE at ``_ONLY_FIRST_OCCURRENCE``.

  * ADMISSIBILITY — APPLIES as a satisfiability control at an F2P-shaped input
    (mirrors nagini case #7).

WITNESSES. On a tactic-proof backend "did not verify" is the DEFAULT outcome of
reshaping an implementation — the frozen script (``rw [escape_loop_eq]``) is
tuned to the frozen ``for``-loop over ``escapeMathSym`` and stops matching the
moment the branch table is reshaped — so a rejection alone attributes nothing to
the spec. Every ``expect="reject"`` case therefore carries a Lean snippet stating
the spec predicate directly at a concrete input; each was checked to HOLD of its
rival and to FAIL on the frozen solution (so it discriminates rather than
asserting a tautology). The carrier computes: ``texLabel`` and the impl both
reduce under ``simp`` with the four defining equations, so no conditioning on an
opaque term is needed.

BINDER COVERAGE. The behavior has a single input binder, ``text``. It is varied
across the reject witnesses so the battery exercises the spec's dependence on
each independent symbol decision rather than probing one point repeatedly:
  * ``[' ']``            — drop-space and the token-order rival (space decision);
  * ``[':']``            — drop-colon (colon decision);
  * ``['-']``            — drop-hyphen (hyphen decision);
  * ``['1', ' ', '0']``  — token-order rival at a multi-char, digit-flanked label;
  * ``['-', '-']``       — only-first-occurrence, the first point in the battery
                           bearing TWO protected symbols, so it is the only one
                           that separates "rewrite every occurrence" from
                           "rewrite one occurrence": all four single-symbol
                           points above are satisfied by the bounded rewrite.
  * ``['J']``            — skip-letter-lift, the only point that is an ALPHABETIC
                           character rather than a protected symbol, so it is the
                           only one on which stage 1 is observable at all: every
                           one of the five points above is letter-free, and on a
                           letter-free label the run-lifting stage is the
                           identity, so all five are satisfied by a rival that
                           drops it entirely.
The admissibility positive additionally exercises a letter-bearing, F2P-shaped
label (``"Jan 01"``) that drives the run-lifting stage. ``pts`` = 6 distinct
reject input points, and the variation is verdict-changing rather than
cosmetic: each point is a label on which its own rival's output differs from
``texLabel``'s and on which at least one OTHER rival in the battery agrees with
``texLabel``, so no two points stand in for the same discrimination. Tabulated
rival x point, every rival has at least one point where it alone (or with one
near-miss partner) diverges, and no point refutes every rival — the two
space-decision rivals share ``[' ']`` and ``['1', ' ', '0']`` by design (they
are near-misses of each other) and are separated from the rest.

AXIOM lane: EMPTY. No ``opaque``/``axiom`` callee contract is consumed (the
run-lifting substitution is a deep-model A-reference validated by G-AX, not a
proof-consumed axiom), so there is no axiom-soundness / axiom-containment
obligation for this gate to probe. AXIOM_TESTS is empty.
"""
from pathlib import Path

INSTANCE = "matplotlib__matplotlib-21568"

_BASE = (Path(__file__).parent / "Solution.lean").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# ---- region anchors (each unique inside Solution.lean; verified at load) ----
# The FULL impl-region body (def line through the final return), so a replacement
# lands entirely inside the impl region and the frozen spec is never touched.
_IMPL_GOLD = (
    "def implementation_texLabel (text : List Char) : List Char := Id.run do\n"
    "  let lifted := bracketLetterRuns text\n"
    "  let mut escaped : List Char := []\n"
    "  for c in lifted do\n"
    "    escaped := escaped ++ escapeMathSym c\n"
    "  let wrapped := \"$\\\\mathdefault{\".toList ++ escaped ++ \"}$\".toList\n"
    "  return dropToken '$' \"\\\\mathdefault{}$\".toList wrapped\n"
)

# The FROZEN tactic body of `correct_texLabel` (the `escape_loop_eq` helper above
# it is part of the frozen set and stays put). Unique in the file.
_PROOF_BODY = (
    "  intro text\n"
    "  unfold problem_spec_texLabel implementation_texLabel texLabel\n"
    "  simp only [Id.run, bind, pure]\n"
    "  rw [escape_loop_eq]\n"
    "  simp [escapeMathSyms]\n"
)

assert _BASE.count(_IMPL_GOLD) == 1, "impl region drifted; update _IMPL_GOLD"
assert _BASE.count(_PROOF_BODY) == 1, "proof region drifted; update _PROOF_BODY"


def _impl(body):
    """Build a full Solution.lean variant by replacing the gold impl body only.

    ``body`` must be a complete ``def implementation_texLabel … := Id.run do …``
    block so region surgery stays inside ``-- impl-start`` / ``-- impl-end``."""
    assert body.startswith("def implementation_texLabel")
    return _swap(_BASE, _IMPL_GOLD, body)


# ---------------------------------------------------------------------------
# Rival impl bodies. Each inlines the symbol-rewrite table into the loop (the
# frozen impl calls `escapeMathSym c`); only the impl changes, so the spec and
# the theorem STATEMENT stay byte-identical. The frozen proof no longer closes
# against the reshaped loop — that IS the expected "does not verify" for a reject
# case — so each carries a discriminating witness below.
# ---------------------------------------------------------------------------

# PARTIAL-DOMAIN: drop the SPACE rewrite (space passes through bare).
_DROP_SPACE = (
    "def implementation_texLabel (text : List Char) : List Char := Id.run do\n"
    "  let lifted := bracketLetterRuns text\n"
    "  let mut escaped : List Char := []\n"
    "  for c in lifted do\n"
    "    escaped := escaped ++ (if c = '-' then ['{', '-', '}'] "
    "else if c = ':' then ['{', ':', '}'] else [c])\n"
    "  let wrapped := \"$\\\\mathdefault{\".toList ++ escaped ++ \"}$\".toList\n"
    "  return dropToken '$' \"\\\\mathdefault{}$\".toList wrapped\n"
)

# PARTIAL-DOMAIN: drop the COLON rewrite (colon passes through bare).
_DROP_COLON = (
    "def implementation_texLabel (text : List Char) : List Char := Id.run do\n"
    "  let lifted := bracketLetterRuns text\n"
    "  let mut escaped : List Char := []\n"
    "  for c in lifted do\n"
    "    escaped := escaped ++ (if c = '-' then ['{', '-', '}'] "
    "else if c = ' ' then ['\\\\', ';'] else [c])\n"
    "  let wrapped := \"$\\\\mathdefault{\".toList ++ escaped ++ \"}$\".toList\n"
    "  return dropToken '$' \"\\\\mathdefault{}$\".toList wrapped\n"
)

# PARTIAL-DOMAIN: drop the HYPHEN rewrite (hyphen passes through bare) — the
# prepatch-class defect, kept here for per-decision binder coverage.
_DROP_HYPHEN = (
    "def implementation_texLabel (text : List Char) : List Char := Id.run do\n"
    "  let lifted := bracketLetterRuns text\n"
    "  let mut escaped : List Char := []\n"
    "  for c in lifted do\n"
    "    escaped := escaped ++ (if c = ':' then ['{', ':', '}'] "
    "else if c = ' ' then ['\\\\', ';'] else [c])\n"
    "  let wrapped := \"$\\\\mathdefault{\".toList ++ escaped ++ \"}$\".toList\n"
    "  return dropToken '$' \"\\\\mathdefault{}$\".toList wrapped\n"
)

# WRONG-TOKEN: rewrite space but with its two code points SWAPPED (';' then '\\'
# instead of '\\' then ';'). Correct on space-free labels, wrong at any space.
_WRONG_SPACE_TOKEN = (
    "def implementation_texLabel (text : List Char) : List Char := Id.run do\n"
    "  let lifted := bracketLetterRuns text\n"
    "  let mut escaped : List Char := []\n"
    "  for c in lifted do\n"
    "    escaped := escaped ++ (if c = '-' then ['{', '-', '}'] "
    "else if c = ':' then ['{', ':', '}'] "
    "else if c = ' ' then [';', '\\\\'] else [c])\n"
    "  let wrapped := \"$\\\\mathdefault{\".toList ++ escaped ++ \"}$\".toList\n"
    "  return dropToken '$' \"\\\\mathdefault{}$\".toList wrapped\n"
)

# POSITIONAL / ONLY-FIRST-OCCURRENCE: rewrites only the FIRST protected symbol
# it meets and lets every LATER protected symbol pass through bare — a
# rewrite-once defect (the per-symbol rewrite is bounded to one hit instead of
# being applied to every occurrence).
# Correct on labels bearing at most one protected symbol, wrong on any label
# bearing two or more.
#
# AUDIT NOTE (positional class, rival replaced). This case previously used a
# HEAD-IDENTITY rival (skip the first character, rewrite the rest). That rival
# is observably wrong on the carrier and its witness discriminated, but its
# `refinement` claim did not hold: the leading position it attacks is never a
# protected symbol in any observable this behavior is exercised on. Every label
# in the exercised set starts with a digit or, when it starts with a letter run,
# with the `}` that stage 1 emits — so a faithful real patch with that
# off-by-one would still produce every expected label and WOULD resolve, which
# is exactly what a reject case may not claim. Re-derived independently: the
# same hedge is present in the nagini sibling's own positional rival (#5,
# last-element identity), whose refinement admits it can only point at a
# hypothetical trailing-symbol label rather than an exercised one.
#
# The only-first-occurrence defect keeps the positional class (it is still a
# position-dependent rewrite, not an omission or a token error) while being
# genuinely refinement-bearing: it changes three separate exercised label
# groups — the date-shaped labels with two hyphens, the labels pairing a hyphen
# with a space, and the labels pairing a space with a colon — because each of
# those bears two protected symbols and only the first would be rewritten.
_ONLY_FIRST_OCCURRENCE = (
    "def implementation_texLabel (text : List Char) : List Char := Id.run do\n"
    "  let lifted := bracketLetterRuns text\n"
    "  let mut escaped : List Char := []\n"
    "  let mut done := false\n"
    "  for c in lifted do\n"
    "    if !done && (c = '-' || c = ':' || c = ' ') then\n"
    "      escaped := escaped ++ escapeMathSym c\n"
    "      done := true\n"
    "    else\n"
    "      escaped := escaped ++ [c]\n"
    "  let wrapped := \"$\\\\mathdefault{\".toList ++ escaped ++ \"}$\".toList\n"
    "  return dropToken '$' \"\\\\mathdefault{}$\".toList wrapped\n"
)

# STAGE-OMISSION: keep the FULL symbol table but drop stage 1 — the alphabetic
# runs are never lifted out of the math-default group (`lifted := text`). Correct
# on every letter-free label, wrong at any label bearing an alphabetic run.
# Added by audit: the five rivals above all reshape stage 2, leaving stage 1
# (the deeply-modeled run scanner) unattacked by the reject lane.
_SKIP_LETTER_LIFT = (
    "def implementation_texLabel (text : List Char) : List Char := Id.run do\n"
    "  let lifted := text\n"
    "  let mut escaped : List Char := []\n"
    "  for c in lifted do\n"
    "    escaped := escaped ++ escapeMathSym c\n"
    "  let wrapped := \"$\\\\mathdefault{\".toList ++ escaped ++ \"}$\".toList\n"
    "  return dropToken '$' \"\\\\mathdefault{}$\".toList wrapped\n"
)

# POSITIVE CONTROL (soundness): a structurally different but CORRECT impl — the
# accumulator `for`-loop is replaced by the direct functional `flatMap` (exactly
# the spec's own `escapeMathSyms`). Same value on every input; the frozen script
# (`rw [escape_loop_eq]`, tuned to the loop) no longer applies, so the obligation
# is re-proved for the new shape. Statement byte-identical; no new lemma/axiom
# (the frozen `escape_loop_eq` helper is left in place, unused).
_POS_CONTROL = (
    "def implementation_texLabel (text : List Char) : List Char :=\n"
    "  let lifted := bracketLetterRuns text\n"
    "  let escaped := lifted.flatMap escapeMathSym\n"
    "  let wrapped := \"$\\\\mathdefault{\".toList ++ escaped ++ \"}$\".toList\n"
    "  dropToken '$' \"\\\\mathdefault{}$\".toList wrapped\n"
)
_POS_PROOF = (
    "  intro text\n"
    "  unfold problem_spec_texLabel implementation_texLabel texLabel escapeMathSyms\n"
    "  rfl\n"
)

# POSITIVE CONTROL #2 (soundness): the faithful analogue of the nagini sibling's
# own positive (#6, branch REORDER). The three guards are disjoint, so testing
# them in the order space, colon, hyphen is semantically identical to the frozen
# table's hyphen, colon, space — but, unlike `_POS_CONTROL`, it is NOT
# definitionally equal to the spec's `escapeMathSyms`: the reordered `if`-chain
# and `escapeMathSym` are distinct terms that agree only after case analysis on
# the character, so the obligation is genuinely RE-PROVEN (a `funext` plus a
# three-way split, each concrete branch closed by `decide`) rather than closed by
# `rfl` on a syntactic match. Added by audit: the port carried only the
# `flatMap` reshape, whose proof is `rfl`, so no positive in the battery
# exercised the spec against an impl that needs real reasoning to line up.
_POS_REORDER = (
    "def implementation_texLabel (text : List Char) : List Char :=\n"
    "  let lifted := bracketLetterRuns text\n"
    "  let escaped := lifted.flatMap (fun c =>\n"
    "    if c = ' ' then ['\\\\', ';']\n"
    "    else if c = ':' then ['{', ':', '}']\n"
    "    else if c = '-' then ['{', '-', '}']\n"
    "    else [c])\n"
    "  let wrapped := \"$\\\\mathdefault{\".toList ++ escaped ++ \"}$\".toList\n"
    "  dropToken '$' \"\\\\mathdefault{}$\".toList wrapped\n"
)
_POS_REORDER_PROOF = (
    "  intro text\n"
    "  unfold problem_spec_texLabel implementation_texLabel texLabel escapeMathSyms\n"
    "  have hfun : (fun c => if c = ' ' then ['\\\\', ';']\n"
    "      else if c = ':' then ['{', ':', '}']\n"
    "      else if c = '-' then ['{', '-', '}'] else [c]) = escapeMathSym := by\n"
    "    funext c\n"
    "    unfold escapeMathSym\n"
    "    by_cases h1 : c = '-'\n"
    "    · subst h1; decide\n"
    "    · by_cases h2 : c = ':'\n"
    "      · subst h2; decide\n"
    "      · by_cases h3 : c = ' '\n"
    "        · subst h3; decide\n"
    "        · simp [h1, h2, h3]\n"
    "  rw [hfun]\n"
)

# ADMISSIBILITY: gold impl unchanged; discharge the spec at an F2P-shaped ground
# input (a label bearing a letter run AND a space, driving BOTH the run-lifting
# and the symbol-rewrite stages) inside the proof region, alongside the frozen
# obligation. If that ground instance could not be discharged the modeled
# behavior would be unsatisfiable at the normal input the F2P exercises.
_ADMISS_PROOF = (
    "  have _ground : problem_spec_texLabel \"Jan 01\".toList\n"
    "      (implementation_texLabel \"Jan 01\".toList) := by\n"
    "    unfold problem_spec_texLabel implementation_texLabel texLabel\n"
    "    simp [bracketLetterRuns, escapeMathSyms, escapeMathSym, dropToken,"
    " List.isPrefixOf]\n"
    + _PROOF_BODY
)


# A single witness shape works for every reject case: unfold the spec predicate
# and the rival impl, then evaluate both sides with the four defining equations.
# It ELABORATES against the rival (the two sides differ at the chosen point) and
# FAILS on the frozen solution (there the two sides are equal, so `¬ (… = …)`
# is unprovable) — both halves confirmed by direct build.
def _witness(comment, text_lit):
    return (
        comment
        + "example : ¬ problem_spec_texLabel " + text_lit + "\n"
        + "    (implementation_texLabel " + text_lit + ") := by\n"
        + "  unfold problem_spec_texLabel implementation_texLabel texLabel\n"
        + "  simp [bracketLetterRuns, escapeMathSyms, escapeMathSym, dropToken,"
        + " List.isPrefixOf]\n"
    )


SPEC_TESTS = [
    # =====================================================================
    # POSITIVE CONTROL (soundness) — a structurally different but CORRECT impl
    # that MUST verify, else the spec is SPEC-TOO-STRONG. The theorem STATEMENT
    # is byte-identical; the tactic body is re-proved for the functional shape.
    # =====================================================================
    {
        "id": "pos-functional-flatmap",
        "kind": "soundness",
        "expect": "verify",
        "module": _swap(_impl(_POS_CONTROL), _PROOF_BODY, _POS_PROOF),
        "rationale": (
            "a correct reshape that drops the mutable-accumulator `Id.run do` "
            "`for`-loop and expresses the symbol-rewrite stage as the direct "
            "functional `lifted.flatMap escapeMathSym` (definitionally the spec's "
            "own `escapeMathSyms`) must satisfy `result = texLabel text`; if it "
            "cannot, the spec is SPEC-TOO-STRONG. Proof: after unfolding the spec, "
            "the impl and `escapeMathSyms`, both sides are the same "
            "`dropToken … (… ++ lifted.flatMap escapeMathSym ++ …)` term, so the "
            "goal closes by `rfl` — no new declaration, axiom, or assumption "
            "token. The frozen `escape_loop_eq` helper is left in place, unused."
        ),
    },

    # =====================================================================
    # POSITIVE CONTROL #2 (soundness) — the nagini sibling's own branch-REORDER
    # positive, faithfully. Unlike the `flatMap` reshape above, this one is NOT
    # definitionally equal to the spec, so the obligation is re-proven by real
    # case analysis rather than closed by `rfl`.
    # =====================================================================
    {
        "id": "pos-branch-reorder",
        "kind": "soundness",
        "expect": "verify",
        "module": _swap(_impl(_POS_REORDER), _PROOF_BODY, _POS_REORDER_PROOF),
        "rationale": (
            "the three symbol guards are pairwise disjoint, so testing them in "
            "the order space, colon, hyphen computes the same list as the frozen "
            "table's hyphen, colon, space order; a correct impl of "
            "`result = texLabel text` must therefore verify, else the spec is "
            "SPEC-TOO-STRONG against a mere branch permutation. This is the "
            "load-bearing positive of the two: the reordered `if`-chain is a "
            "DIFFERENT term from `escapeMathSym`, definitionally distinct (they "
            "agree only after splitting on the character), so `rfl` does NOT "
            "close it — the proof supplies `funext` and a three-way `by_cases` "
            "whose concrete branches go by `decide`, then rewrites. No new "
            "declaration, axiom, or assumption token; the theorem STATEMENT is "
            "byte-identical and the frozen `escape_loop_eq` helper is left in "
            "place, unused."
        ),
    },

    # =====================================================================
    # ADMISSIBILITY — a satisfiability control at a normal, F2P-shaped input.
    # The frozen theorem carries NO precondition hypothesis (the behavior is
    # total), so nagini's precondition-admission probe has no binder to attack;
    # the honest analogue discharges the spec predicate at the F2P ground input
    # inside the proof region, alongside the frozen obligation.
    # =====================================================================
    {
        "id": "admiss-letter-and-space-ground",
        "kind": "admissibility",
        "expect": "verify",
        "module": _swap(_BASE, _PROOF_BODY, _ADMISS_PROOF),
        "rationale": (
            "the obligation is discharged at an F2P-shaped ground input — a label "
            "bearing a maximal ASCII-letter run AND a space (\"Jan 01\"), which "
            "drives BOTH the run-lifting stage and the symbol-rewrite stage — by "
            "unfolding and evaluating with the four defining equations; then the "
            "frozen obligation is closed verbatim. Verifies (else the spec is "
            "unsatisfiable at the normal input, the analogue of PRECOND-TOO-STRONG). "
            "Nothing is assumed: the theorem STATEMENT is byte-identical, the "
            "ground instance is a `have` inside the existing tactic body, and no "
            "new declaration/axiom/`sorry` is introduced."
        ),
    },

    # =====================================================================
    # UNIQUENESS / SPEC-TOO-WEAK rivals — wrong impls sharing the frozen spec
    # that MUST be rejected. Each carries (a) the refinement argument that its
    # faithful real patch would NOT resolve the F2P, and (b) a discriminating
    # witness pinning the violation at one concrete input.
    # =====================================================================
    {
        "id": "weak-drop-space",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(_DROP_SPACE),
        "refinement": (
            "this is the fix MISSING the space rewrite: a space passes through "
            "bare. Its faithful real patch omits the space-protection step, so a "
            "label containing a space renders with the numbers run together rather "
            "than thin-space-separated. The F2P observables that exercise a space "
            "(a label of the shape `01<space>00:00`) expect the thin-space form and "
            "differ from the bare form, so the real patch fails those cases — it "
            "does NOT resolve."
        ),
        "rationale": (
            "REJECT from the clause `result = texLabel text` at the space decision: "
            "`escapeMathSym ' ' = ['\\\\', ';']`, so the spec demands the space be "
            "rewritten, but this impl emits the bare space. Refuted at `[' ']`, "
            "isolating the space binder value."
        ),
        "witness": _witness(
            "-- Refuted at a bare space: the spec rewrites ' ' to the thin-space\n"
            "-- command, this rival leaves it bare.\n",
            "[' ']",
        ),
    },
    {
        "id": "weak-drop-colon",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(_DROP_COLON),
        "refinement": (
            "this is the fix MISSING the colon rewrite: a colon passes through "
            "bare. Its faithful real patch omits the colon-bracing step, so a "
            "time-like label renders its colon spaced like a binary operator "
            "rather than braced. The F2P observables that exercise a colon (labels "
            "of the shape `04:00`, expected braced as `04{:}00`) differ from the "
            "bare-colon form, so the real patch fails those cases — it does NOT "
            "resolve."
        ),
        "rationale": (
            "REJECT from the clause `result = texLabel text` at the colon decision: "
            "`escapeMathSym ':' = ['{', ':', '}']`, so the spec demands the colon "
            "be braced, but this impl emits the bare colon. Refuted at `[':']`, "
            "varying the input binder to the colon value."
        ),
        "witness": _witness(
            "-- Refuted at a bare colon: the spec braces ':' as {:}, this rival\n"
            "-- leaves it bare.\n",
            "[':']",
        ),
    },
    {
        "id": "weak-drop-hyphen",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(_DROP_HYPHEN),
        "refinement": (
            "this is the fix MISSING the hyphen rewrite (the prepatch-class "
            "defect): a hyphen passes through bare. Its faithful real patch omits "
            "the hyphen-bracing step, so a date-like label renders its hyphen "
            "spaced like a binary operator. The pre-existing observables that "
            "exercise a hyphen (labels of the shape `1990-01-03`, expected braced "
            "as `1990{-}01{-}03`) differ from the bare-hyphen form, so the real "
            "patch fails those cases — it does NOT resolve."
        ),
        "rationale": (
            "REJECT from the clause `result = texLabel text` at the hyphen "
            "decision: `escapeMathSym '-' = ['{', '-', '}']`, so the spec demands "
            "the hyphen be braced, but this impl emits the bare hyphen. Refuted at "
            "`['-']`, varying the input binder to the hyphen value."
        ),
        "witness": _witness(
            "-- Refuted at a bare hyphen: the spec braces '-' as {-}, this rival\n"
            "-- leaves it bare.\n",
            "['-']",
        ),
    },
    {
        "id": "weak-wrong-space-token",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(_WRONG_SPACE_TOKEN),
        "refinement": (
            "this emits the space token with its two code points in the WRONG "
            "order (`;` then the escape char, instead of the escape char then `;`). "
            "Its faithful real patch rewrites a space to a malformed command, so a "
            "label containing a space renders incorrectly. The F2P observables that "
            "exercise a space expect the correctly-ordered thin-space form and "
            "differ from the swapped form, so the real patch fails those cases — it "
            "does NOT resolve. This is a NEAR-MISS of the drop-space rival (both "
            "wrong only at a space) but wrong for a different reason (order, not "
            "omission), so it is given its OWN witness at a distinct multi-char "
            "point."
        ),
        "rationale": (
            "REJECT from the clause `result = texLabel text` at the space decision: "
            "`escapeMathSym ' ' = ['\\\\', ';']` (escape char then `;`), but this "
            "impl emits `[';', '\\\\']`, so the two code points are transposed at "
            "any space. Refuted at `['1', ' ', '0']` — a multi-char, digit-flanked "
            "label distinct from the drop-space rival's `[' ']` point."
        ),
        "witness": _witness(
            "-- Refuted at a digit-flanked space: the spec's space token has a\n"
            "-- fixed code-point ORDER; this rival transposes the two code points.\n",
            "['1', ' ', '0']",
        ),
    },
    {
        "id": "weak-only-first-occurrence",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(_ONLY_FIRST_OCCURRENCE),
        "refinement": (
            "this bounds the symbol rewrite to ONE hit: the first protected symbol "
            "is rewritten, every later one passes through bare (a rewrite-once "
            "defect — the per-symbol rewrite stops after its first match instead "
            "of applying to every occurrence). Its faithful real patch therefore "
            "mis-renders every label bearing two or more protected symbols, and "
            "the exercised label set is full of them: the date-shaped labels carry "
            "two hyphens, one group pairs a hyphen with a space, and another pairs "
            "a space with a colon. In each of those the second protected symbol "
            "would render bare — spaced like a binary operator, or with the numbers "
            "run together — so the produced label differs from the expected one and "
            "the real patch fails those cases: it does NOT resolve. (Checked "
            "against the exercised label set rather than asserted: three separate "
            "observable groups change, and the single-protected-symbol labels are "
            "left untouched, which is what makes this a near-miss rather than a "
            "coarse break.)"
        ),
        "rationale": (
            "REJECT from the clause `result = texLabel text`: the spec applies "
            "`escapeMathSym` to EVERY element of `lifted` (`texLabel` maps the "
            "rewrite over the whole list), but this impl applies it to at most one "
            "element and copies the rest verbatim. Refuted at `['-', '-']` — a "
            "label bearing TWO protected symbols, the structural point (count "
            "dependence of the rewrite, not the identity of one symbol) that none "
            "of the single-character rivals reaches: each of those is refuted at a "
            "one-symbol label, where this rival is still correct."
        ),
        "witness": _witness(
            "-- Refuted at a label bearing TWO protected symbols: the spec rewrites\n"
            "-- EVERY occurrence, this rival rewrites only the first and leaves the\n"
            "-- second bare.\n",
            "['-', '-']",
        ),
    },
    {
        "id": "weak-skip-letter-lift",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(_SKIP_LETTER_LIFT),
        "refinement": (
            "this keeps the whole symbol-rewrite table and drops the RUN-LIFTING "
            "stage: alphabetic runs are left inside the math-default group "
            "instead of being lifted out to render as upright text. Its faithful "
            "real patch therefore mis-renders every label bearing letters — the "
            "month-abbreviation labels. Two exercised groups change: a "
            "letters-only label, which the spec renders as the bare run with no "
            "math group at all (the outer group collapses to empty and is "
            "removed at stage 4) but which this rival wraps in a math-default "
            "group; and a label pairing a month abbreviation with a hyphen, "
            "where the spec closes the group before the run and reopens it after "
            "while this rival emits one group around the whole thing. Both "
            "produced labels differ from the expected ones, so the real patch "
            "fails those cases — it does NOT resolve. (Checked against the "
            "exercised label set, not asserted; the digit-only labels are left "
            "untouched, which is what makes this a near-miss.)"
        ),
        "rationale": (
            "REJECT from the clause `result = texLabel text` at the run-lifting "
            "stage: `texLabel` applies `bracketLetterRuns` to the input before "
            "the symbol rewrite, but this impl passes the input through "
            "unchanged, so the two differ on any label containing an ASCII "
            "letter. Refuted at `['J']` — the only witness point in the battery "
            "that is a LETTER rather than a protected symbol, and hence the only "
            "one at which stage 1 is observable: on the five letter-free points "
            "the other rivals use, `bracketLetterRuns` is the identity and this "
            "rival agrees with the spec exactly."
        ),
        "witness": _witness(
            "-- Refuted at a single-letter label: the spec lifts the alphabetic run\n"
            "-- OUT of the math-default group (leaving the bare run, the empty group\n"
            "-- having been removed), this rival leaves it wrapped inside.\n",
            "['J']",
        ),
    },
]


# No consumed axioms and no deep-model references drive an in-model axiom
# obligation for this gate: the run-lifting substitution is modeled deeply and
# validated == the real callee by G-AX (not proof-consumed), and the
# symbol-rewrite / token-deletion stages compute directly. AXIOM_TESTS is empty.
AXIOM_TESTS = []
