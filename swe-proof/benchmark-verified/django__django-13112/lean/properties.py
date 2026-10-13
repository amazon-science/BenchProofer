"""properties.py — G-PBT falsification battery for django__django-13112 (lean).

NOT a Lean file; a record of adversarial cases the G-PBT gate executes. Each
SPEC case is a full ``Solution.lean`` variant that shares the FROZEN spec
byte-for-byte (region surgery: only text inside an ``-- impl-start`` /
``-- impl-end`` region — and, for a case that legitimately re-proves, inside a
``-- proof-start`` / ``-- proof-end`` region — is changed, so
``markers.same_spec`` holds and the ``theorem correct_modelRef`` STATEMENT stays
byte-identical). ``expect:"verify"`` passes iff (in scope AND the file
elaborates with the obligation closed); ``expect:"reject"`` passes iff (in scope
AND it does NOT verify AND the case's refutation ``witness`` holds of the rival
while FAILING on the frozen solution).

DEFENDED SURFACE (one modeled behavior over an ASCII reference-token carrier).
A reference token is a character list carrying two in-domain proofs (at most one
separator ``'.'`` and all-ASCII). Its normalized form is pinned by shape:

  modelRef (t) : List Char
    '.' ∈ t.chars  →  result = prefixSeg t.chars ++ '.' :: (nameSeg t.chars).map toLower
    '.' ∉ t.chars  →  result = t.chars.map toLower

i.e. a QUALIFIED token keeps the segment before the separator EXACTLY as written
(case preserved) and lowercases only the trailing segment; a BARE token is
lowercased in full. Both clauses are grounded in the input carrier (equalities
against terms built solely from ``t.chars``), so there is no answer key to echo.

ADVERSARIAL READ of the nagini classes on this carrier:

  * FRAME / PERMISSION MUTATION — VACUOUS. Lean is referentially transparent:
    the input carries no heap permission, there is no read-only half-permission
    to overwrite and no aliasing to exploit. The nagini ``frame-mut-text`` rival
    (write to the read-only input, then return it) has no expressible instance
    here and no substitute is fabricated for it.

  * UNGROUNDED-ORACLE ECHO — the nagini ``weak-echo-input-verbatim`` surrogate
    ports directly: return the token UNCHANGED. It satisfies no oracle (there is
    none) and violates the bare-name clause on any upper-case token.

  * PARTIAL-DOMAIN / VALUE — the two nagini F2P discriminators port directly:
    lower-case EVERYTHING (drops the preserved-prefix distinction on qualified
    tokens) and keep EVERYTHING verbatim on qualified tokens (drops the
    trailing-segment lowercasing).

WITNESSES. On a tactic-proof backend "did not verify" is the DEFAULT outcome of
reshaping an implementation — the frozen ``simp only [...]`` script is tuned to
the frozen form — so a rejection alone attributes nothing to the spec. Every
``expect="reject"`` case therefore carries a Lean snippet proving the rival
CONTRADICTS the spec at one concrete in-domain token. Each is stated directly
against ``problem_spec_modelRef`` at ``decide``-able literals, and each was
checked to hold of its rival and to FAIL on the frozen solution (so it
discriminates rather than asserting a tautology). The tokens are spread across
the domain so each spec CLAUSE and both settings of the separator binder move:

  * echo-input      is refuted on a BARE token ``A`` (no separator), the only
    place it diverges from gold (bare-name clause).
  * lower-all       is refuted on a QUALIFIED token ``A.b`` — gold keeps the
    prefix ``A``; the rival lowers it (prefix-preservation, qualified clause).
  * keep-verbatim   is refuted on a QUALIFIED token ``a.B`` — gold lowercases
    the trailing ``B``; the rival keeps it (trailing-fold, qualified clause).

No two rivals share a refutation point: echo is refuted where no separator is
present, and the two qualified rivals attack the two DIFFERENT halves of the
qualified clause (prefix verbatim vs. trailing lowercased) at different tokens.

AXIOM lane: EMPTY. meta.json axioms == [] and deep_model_references relate only
to the G-CONF/G-AX character-fold binding; the modeled behavior is a total
computation over the token's own characters, so there is no
axiom-soundness / axiom-containment obligation to probe here (that lane belongs
to G-AX in any case). See ``assessment`` in the submitted payload for the
nagini cases omitted (frame-mutation) and why.
"""
from pathlib import Path

INSTANCE = "django__django-13112"

_BASE = (Path(__file__).parent / "Solution.lean").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# ---- region anchors (each unique inside Solution.lean; verified at load) ----
# The FULL impl body (strictly between the impl markers) and the FULL tactic
# body of the proof region (after the byte-identical theorem STATEMENT). Every
# replacement lands entirely inside the region it edits.
_I_IMPL = (
    "def implementation_modelRef (t : RefToken) : List Char := Id.run do\n"
    "  if '.' ∈ t.chars then\n"
    "    -- qualified `prefix.name`: keep the prefix verbatim, lowercase only the name\n"
    "    let prefixPart := prefixSeg t.chars\n"
    "    let namePart := nameSeg t.chars\n"
    "    return prefixPart ++ '.' :: namePart.map Char.toLower\n"
    "  else\n"
    "    -- bare name: lowercase the whole token\n"
    "    return t.chars.map Char.toLower"
)

_P_TAC = (
    "  intro t\n"
    "  unfold problem_spec_modelRef implementation_modelRef\n"
    "  by_cases h : '.' ∈ t.chars\n"
    "  · refine ⟨fun _ => ?_, fun hcon => absurd h hcon⟩\n"
    "    simp only [Id.run, h, if_true, pure]\n"
    "  · refine ⟨fun hcon => absurd hcon h, fun _ => ?_⟩\n"
    "    simp only [Id.run, h, if_false, pure]"
)

# The proof of a RefToken's `ascii` field at a concrete literal token. Reused by
# every witness / ground instance; keeps the domain proofs decidable without a
# raw `decide` on the (recursion-blowing) `asciiToken` predicate.
_ASCII = ("by unfold asciiToken isAsciiChar; intro c hc; "
          "fin_cases hc <;> decide")


SPEC_TESTS = [
    # =====================================================================
    # POSITIVE CONTROLS (soundness) — structurally different but CORRECT
    # implementations that MUST verify. If a faithful correct implementation
    # cannot satisfy the frozen obligation the spec is SPEC-TOO-STRONG. Each
    # keeps the `theorem correct_modelRef` statement byte-identical; where the
    # frozen tactic no longer applies it is re-proved with core/Mathlib lemmas
    # only — no helper lemma, no axiom, no assumption token.
    # =====================================================================
    {
        "id": "pos-inline-let-bindings",
        "kind": "soundness",
        "expect": "verify",
        # Structural reshape: inline the two `let` bindings that name the two
        # segments. The value flowing into each branch's return is unchanged, so
        # the result is byte-for-byte the frozen one and the frozen tactic body
        # (the `let`s were zeta-reduced by `simp only` anyway) still closes.
        "module": _swap(
            _BASE, _I_IMPL,
            "def implementation_modelRef (t : RefToken) : List Char := Id.run do\n"
            "  if '.' ∈ t.chars then\n"
            "    return prefixSeg t.chars ++ '.' :: (nameSeg t.chars).map Char.toLower\n"
            "  else\n"
            "    return t.chars.map Char.toLower",
        ),
        "rationale": "a correct reshape that inlines the two local segment "
                     "bindings computes the same result on every token, so both "
                     "clauses of the postcondition still hold; if it cannot "
                     "verify the modelRef spec is SPEC-TOO-STRONG. Proof: the "
                     "frozen tactic body is retained verbatim (the inlined lets "
                     "were already reduced by the frozen `simp only`).",
    },
    {
        "id": "pos-negated-separator-guard",
        "kind": "soundness",
        "expect": "verify",
        # Branch reorder of the shape decision: test the ABSENCE of a separator
        # first (bare case) and fall through to the qualified case in the else.
        # Same shape decision, same value in each branch; the frozen `simp only`
        # is tuned to the `'.' ∈` guard order, so the obligation is re-proved for
        # the negated-guard shape with the matching core simp lemmas.
        "module": _swap(
            _swap(
                _BASE, _I_IMPL,
                "def implementation_modelRef (t : RefToken) : List Char := Id.run do\n"
                "  if '.' ∉ t.chars then\n"
                "    return t.chars.map Char.toLower\n"
                "  else\n"
                "    return prefixSeg t.chars ++ '.' :: (nameSeg t.chars).map Char.toLower",
            ),
            _P_TAC,
            "  intro t\n"
            "  unfold problem_spec_modelRef implementation_modelRef\n"
            "  by_cases h : '.' ∈ t.chars\n"
            "  · refine ⟨fun _ => ?_, fun hcon => absurd h hcon⟩\n"
            "    simp only [Id.run, h, not_true, if_false, pure]\n"
            "  · refine ⟨fun hcon => absurd hcon h, fun _ => ?_⟩\n"
            "    simp only [Id.run, h, not_false_iff, if_true, pure]",
        ),
        "rationale": "reordering the two shape branches behind a negated "
                     "separator guard preserves the exact qualified/bare "
                     "decision and the value returned in each, so both clauses "
                     "still hold; must verify (else SPEC-TOO-STRONG). Re-proved "
                     "because the frozen `simp only` is tuned to the `'.' ∈` "
                     "guard order: the negated shape discharges with the "
                     "corresponding core lemmas (`not_true`/`not_false_iff`), no "
                     "new declaration.",
    },

    # =====================================================================
    # ADMISSIBILITY — a positive control confirming the obligation is
    # SATISFIABLE (non-vacuous) at a normal, F2P-shaped input rather than only
    # provable in the abstract. The frozen theorem carries NO precondition
    # hypothesis (the modeled behavior is total, so `∀` is unguarded), which
    # means the nagini precondition-admission probe has no binder to attack; the
    # honest analogue is to discharge the spec predicate at a ground qualified
    # mixed-case token (the F2P shape: a mixed-case prefix and a mixed-case
    # trailing name) by evaluation, inside the proof region, alongside the
    # frozen obligation. If that ground instance could not be discharged, the
    # modeled behavior would be unsatisfiable at exactly the input the F2P
    # exercises.
    # =====================================================================
    {
        "id": "admiss-f2p-shaped-token",
        "kind": "admissibility",
        "expect": "verify",
        "module": _swap(
            _BASE, _P_TAC,
            "  have _ground : problem_spec_modelRef\n"
            "      ⟨['M', '.', 'A'], by decide, " + _ASCII + "⟩\n"
            "      (implementation_modelRef ⟨['M', '.', 'A'], by decide, "
            + _ASCII + "⟩) := by\n"
            "    unfold problem_spec_modelRef implementation_modelRef\n"
            "    decide\n"
            + _P_TAC,
        ),
        "rationale": "the modelRef obligation is discharged at a ground "
                     "F2P-shaped token (a qualified reference with a mixed-case "
                     "prefix and a mixed-case trailing name) by `decide`, then "
                     "the frozen obligation is closed verbatim. Verifies (else "
                     "the spec is unsatisfiable at the normal input, the "
                     "analogue of PRECOND-TOO-STRONG). Nothing is assumed: no new "
                     "declaration, the theorem statement is byte-identical, and "
                     "the ground instance is a `have` inside the existing tactic "
                     "body.",
    },

    # =====================================================================
    # UNIQUENESS / SPEC-TOO-WEAK rivals — wrong implementations sharing the
    # frozen spec that MUST be rejected. Each carries (a) the refinement
    # argument that its faithful real patch would NOT resolve the F2P, so a
    # verifying rival would be a true verify-does-not-imply-resolve break rather
    # than an artifact, and (b) a refutation witness pinning the violation at
    # one concrete in-domain token, checked to hold of the rival and FAIL on
    # gold.
    # =====================================================================
    {
        "id": "weak-echo-input-verbatim",
        "kind": "uniqueness",
        "expect": "reject",
        # Return the token UNCHANGED: no normalization at all. Satisfies neither
        # clause the moment any character would fold.
        "module": _swap(
            _BASE, _I_IMPL,
            "def implementation_modelRef (t : RefToken) : List Char := Id.run do\n"
            "  return t.chars",
        ),
        "refinement": "returning the reference unchanged corresponds to a change "
                      "that drops normalization entirely — weaker than even the "
                      "pre-existing behavior. A bare mixed-case reference would "
                      "be left as written instead of being folded to the "
                      "lower-cased label the downstream registry looks up, so "
                      "the case-folding the resolving change depends on "
                      "regresses and the F2P is not resolved.",
        "rationale": "REJECT from the bare-name clause `'.' ∉ t.chars → result = "
                     "t.chars.map toLower`: on a bare upper-case token the rival "
                     "returns it verbatim where the spec requires the lowercased "
                     "form. Refuted on a BARE token (no separator): the only "
                     "sub-domain on which echo diverges from gold, distinct from "
                     "the qualified tokens the other two rivals are refuted at.",
        "witness": (
            "-- Bare token `A` (no separator): the bare-name clause requires the\n"
            "-- lowercased form `a`; echoing the input returns `A`.\n"
            "example : ¬ problem_spec_modelRef\n"
            "    ⟨['A'], by decide, " + _ASCII + "⟩\n"
            "    (implementation_modelRef ⟨['A'], by decide, " + _ASCII + "⟩) := by\n"
            "  unfold problem_spec_modelRef implementation_modelRef\n"
            "  decide\n"
        ),
    },
    {
        "id": "weak-lowercase-everything",
        "kind": "uniqueness",
        "expect": "reject",
        # Lowercase EVERY character, ignoring the shape: exactly the pre-existing
        # whole-string fold. Drops the prefix-preservation the fix introduces.
        "module": _swap(
            _BASE, _I_IMPL,
            "def implementation_modelRef (t : RefToken) : List Char := Id.run do\n"
            "  return t.chars.map Char.toLower",
        ),
        "refinement": "lowercasing the whole reference is the pre-existing "
                      "behavior the issue reports: for a qualified reference "
                      "with a mixed-case prefix the prefix is folded too, so the "
                      "deconstructed value names a namespace that is not "
                      "installed and the mixed-case-app-label F2P fails with the "
                      "reported lazy-reference error. It would NOT resolve — this "
                      "is the prepatch fold.",
        "rationale": "REJECT from the qualified clause `'.' ∈ t.chars → result = "
                     "prefixSeg ++ '.' :: (nameSeg).map toLower`: on a qualified "
                     "token whose prefix has an upper-case letter the spec keeps "
                     "the prefix verbatim while the rival lowers it. Refuted at "
                     "`A.b` — the prefix-preservation half of the qualified "
                     "clause, a sub-domain neither of the other rivals probes.",
        "witness": (
            "-- Qualified token `A.b`: the qualified clause keeps the prefix `A`\n"
            "-- verbatim (result `A.b`); folding everything gives `a.b`.\n"
            "example : ¬ problem_spec_modelRef\n"
            "    ⟨['A', '.', 'b'], by decide, " + _ASCII + "⟩\n"
            "    (implementation_modelRef ⟨['A', '.', 'b'], by decide, "
            + _ASCII + "⟩) := by\n"
            "  unfold problem_spec_modelRef implementation_modelRef\n"
            "  decide\n"
        ),
    },
    {
        "id": "weak-keep-qualified-verbatim",
        "kind": "uniqueness",
        "expect": "reject",
        # On a qualified token keep the WHOLE string verbatim (prefix AND
        # trailing name): the trailing segment is never folded. Correct on bare
        # tokens (same lowercasing as gold), so a strict PARTIAL-DOMAIN rival.
        "module": _swap(
            _BASE, _I_IMPL,
            "def implementation_modelRef (t : RefToken) : List Char := Id.run do\n"
            "  if '.' ∈ t.chars then\n"
            "    return t.chars\n"
            "  else\n"
            "    return t.chars.map Char.toLower",
        ),
        "refinement": "splitting on the separator but keeping the WHOLE token "
                      "verbatim forgets to fold the trailing name segment: a "
                      "qualified reference with a mixed-case trailing name "
                      "resolves to that name un-folded instead of its lowercased "
                      "label, so the lazy reference dangles (the registry looks "
                      "up the mixed-case name, not its lower-cased form) — a "
                      "wrong resolution on the qualified sub-domain that does not "
                      "faithfully reproduce the resolving change.",
        "rationale": "REJECT from the qualified clause `'.' ∈ t.chars → result = "
                     "prefixSeg ++ '.' :: (nameSeg).map toLower`: on a qualified "
                     "token whose trailing name has an upper-case letter the "
                     "spec lowercases it while the rival keeps it. Correct on "
                     "bare tokens (keep=whole-lower, same as gold), so a strict "
                     "PARTIAL-DOMAIN attack the lowercase-everything rival does "
                     "not subsume. Refuted at `a.B` — the trailing-fold half of "
                     "the qualified clause, distinct from `A.b`.",
        "witness": (
            "-- Qualified token `a.B`: the qualified clause lowercases the\n"
            "-- trailing `B` (result `a.b`); keeping it verbatim gives `a.B`.\n"
            "example : ¬ problem_spec_modelRef\n"
            "    ⟨['a', '.', 'B'], by decide, " + _ASCII + "⟩\n"
            "    (implementation_modelRef ⟨['a', '.', 'B'], by decide, "
            + _ASCII + "⟩) := by\n"
            "  unfold problem_spec_modelRef implementation_modelRef\n"
            "  decide\n"
        ),
    },
]
