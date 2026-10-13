"""properties.py — G-PBT falsification battery for sphinx-doc__sphinx-7440 (lean).

NOT a Lean file; a record of adversarial cases the G-PBT gate executes and
stamps with a recorded verdict. Each SPEC case is a full ``Solution.lean``
variant built by region surgery: only text inside an ``-- impl-start`` /
``-- impl-end`` region — and, for a case that legitimately re-proves, inside the
matching ``-- proof-start`` / ``-- proof-end`` region — is changed, so
``markers.same_spec`` holds by construction and every ``theorem correct_<name>``
STATEMENT stays byte-identical. No case introduces ``sorry`` / ``admit`` /
``native_decide`` / ``axiom`` or any new theorem/lemma. ``expect="verify"``
passes iff (in scope AND the file elaborates with the obligation closed);
``expect="reject"`` passes iff (in scope AND it does NOT verify AND the case's
refutation ``witness`` holds of the rival while FAILING on the frozen solution).

PORT NOTE — carrier narrowing vs the nagini sibling.
  The nagini battery contracts ONE procedure over a read-only ``List[int]`` term
  text held at a half fractional permission, whose postcondition pins the output
  VERBATIM to the input (whole-sequence, length, and element-wise). This Lean
  bundle models the SAME case-preservation behavior but splits it across the two
  coordinated sites the fix touches, as two total functions over ``List Char``:

    * glossaryTermEntry (termtext) : (key, indexTerm)
        the registration entry is a PAIR — the identifier under which the term
        is registered (result.1) and the term as it appears in its index entry
        (result.2). The spec pins BOTH to the term text verbatim:
            result.1 = termtext ∧ result.2 = termtext
        Two INDEPENDENT top-level clauses. result.1 is the changed value (the
        registration key); result.2 is the frame component that was already
        correct but must stay pinned so a rival cannot fold it freely.

    * termXrefTarget (target) : result
        the resolved lookup target for a cross-reference is the reference text
        verbatim:  result = target.  One clause.

  So the nagini "verbatim identity copy" postcondition becomes, on this carrier,
  three equalities-to-input across two obligations. The frozen impl is
  straight-line identity rather than a per-code-point copy LOOP, so nagini's
  loop-shaped WRONG impls (which differ from gold only in how the copy is
  driven) have no separate expression here: their observable content is an
  equality violation on the whole list, which is what the value rivals below
  attack directly.

  That is NOT true of nagini's loop-shaped POSITIVE control, and an earlier draft
  of this note wrongly implied it was. A per-element accumulator copy IS
  expressible here and is a strictly stronger soundness probe than a
  straight-line reshape, because it does not reduce to the input definitionally:
  it is shipped as `pos-xref-nondefeq-loop-rebuild` (checked — it fails under the
  frozen `rfl` proof body and verifies only once reproven by induction). See the
  omission note at the foot of this file.

ADVERSARIAL READ of the nagini classes on this carrier:

  * FRAME / PERMISSION-MUTATION rival — VACUOUS. Lean is referentially
    transparent: the input is an immutable ``List Char``, there is no read-only
    half-permission to overwrite and no aliasing to exploit. The nagini
    write-to-input rival has no expressible instance here; no substitute is
    fabricated. Its FRAME concern is answered instead by the result.2 clause:
    a rival that mishandles the unchanged index-term component is attacked
    directly (see ``fold-index-term``).

  * UNGROUNDED-ORACLE ECHO — VACUOUS. Every postcondition is GROUNDED in the
    input (an equality against ``termtext`` / ``target`` itself). The bundle
    declares no ``opaque`` / ``axiom`` (mapping.md: both values are computed by
    straight-line code from the term/reference text), so there is no answer key
    an impl could echo without doing the work; the honest substitute is the
    reshaped-copy positive control below.

  * VALUE / PARTIAL-DOMAIN rivals — the heart of the port. The nagini value
    rivals (whole-string case fold = the pre-patch bug; first-character fold;
    drop-the-last-element) all re-express directly here as equality violations
    against the verbatim postcondition, and each carries a refutation witness.

  * AXIOM_TESTS — dropped. The axiom lane is G-AX's job and this bundle ships no
    consumed axiom (meta.json axioms == []).

DEFENDED SURFACE (the clauses every rival is built to attack):
  C1  glossaryTermEntry result.1 = termtext — the registration identifier is
      the term text with its exact characters preserved (the changed value; the
      F2P feeds an upper-case term and asserts its stored key keeps that case).
  C2  glossaryTermEntry result.2 = termtext — the index-entry term is likewise
      the term text verbatim (the frame component; the F2P also pins the index
      entry to the upper-case spelling).
  C3  termXrefTarget result = target — a cross-reference resolves to the term
      spelled with the same case (previously the target was case-folded).

BINDER COVERAGE. The reject witnesses vary the two input binders across distinct
concrete points rather than probing one point repeatedly:
  * ``termtext`` (C1/C2): refuted at ['M','y','S','Q','L'] (whole-string fold of
    the key), ['A','B'] (first-character-only fold of the key — near-miss),
    ['a'] (dropped last element of the key), ['a','B'] (fold of every character
    BUT the first — the mirror near-miss), ['A'] (fold of the index term), and
    ['a','b'] (dropped last element of the index term);
  * ``target`` (C3): refuted at ['T'] (fold of the lookup target), ['a','b']
    (dropped last element of the target), and ['a','B'] (fold of every character
    of the target BUT the first — the C3 near-miss).
  The points are pairwise DISCRIMINATING, not merely distinct spellings: each
  rival was machine-checked to AGREE with the spec at the sibling rivals' points
  — e.g. the whole-fold key rival is satisfied at all-lowercase ['m','y','s','q',
  'l'] (build exit 0) and the fold-target rival is satisfied at ['a','b'] (exit
  0), which is why the truncation rivals carry those points. The first-char and
  tail-fold rivals differ observably from each other at ['A','B'] vs ['a','B']
  (the first yields ['a','B'], the second ['A','b']; exit 0 on a direct value
  check). The C3 near-miss is satisfied at ['T'] (exit 0), the very point the
  whole-fold C3 rival is refuted at, which is what makes those two distinct
  sub-domains of ``target`` rather than one point probed twice.
  ``scripts/pbt_coverage.py`` reports this as ``binders=2 pts=…``; the
  per-binder point counts are 6 on ``termtext`` and 3 on ``target``, and the
  reporter's aggregate is advisory — the discrimination evidence above is the
  claim that matters.

WITNESSES. On a tactic-proof backend "did not verify" is the DEFAULT outcome of
reshaping an implementation (the frozen script is tuned to the frozen form), so
a rejection alone attributes nothing to the spec. Every ``expect="reject"`` case
therefore carries a Lean snippet stating the spec predicate directly at a
``decide``-able concrete input; each was checked to HOLD of its rival and to
FAIL on the frozen solution (so it discriminates rather than asserting a
tautology), and each gold-side failure was read to confirm it is a SEMANTIC
refutation (``decide`` proving the negation false) rather than an unknown
identifier, a stuck reduction, or a timeout.

Where a rival's point is that it corrupts ONE clause and leaves the other
correct, the witness says so clause-precisely rather than stating the bare
``¬ (C1 ∧ C2)``: that shape is satisfied by either conjunct failing, so it
cannot attribute the refutation to the clause the case names. See
``fold-index-term`` and ``drop-last-of-index-term``.
"""
from pathlib import Path

INSTANCE = "sphinx-doc__sphinx-7440"

_BASE = (Path(__file__).parent / "Solution.lean").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# ---- region anchors (each unique inside Solution.lean; verified at load) ----
# Full impl-region body of the glossary-entry function.
_IMPL_GLOSS = (
    "def implementation_glossaryTermEntry\n"
    "    (termtext : List Char) : List Char × List Char := Id.run do\n"
    "  let key := termtext\n"
    "  let indexTerm := termtext\n"
    "  return (key, indexTerm)\n"
)
# The key binding alone (unique inside the glossary impl region).
_I_KEY = "  let key := termtext\n"
# The index-term binding alone (unique inside the glossary impl region).
_I_INDEX = "  let indexTerm := termtext\n"

# Full impl-region body of the cross-reference target function.
_IMPL_XREF = (
    "def implementation_termXrefTarget (target : List Char) : List Char := Id.run do\n"
    "  return target\n"
)

# Frozen proof body of the glossary obligation (unique in the file).
_PROOF_GLOSS = "  intro\n  exact ⟨rfl, rfl⟩\n"
# Frozen proof body of the cross-reference obligation (unique in the file).
_PROOF_XREF = "  intro\n  rfl\n"

# sanity: the frozen anchors are present exactly once
assert _BASE.count(_IMPL_GLOSS) == 1, "glossary impl region drifted"
assert _BASE.count(_IMPL_XREF) == 1, "xref impl region drifted"
assert _BASE.count(_PROOF_GLOSS) == 1, "glossary proof region drifted"
assert _BASE.count(_PROOF_XREF) == 1, "xref proof region drifted"


SPEC_TESTS = [
    # =====================================================================
    # POSITIVE CONTROLS (soundness) — structurally different but CORRECT impls
    # that MUST verify. If a faithful correct impl cannot satisfy the frozen
    # obligation the spec is SPEC-TOO-STRONG. Each keeps the
    # ``theorem correct_<name>`` STATEMENT byte-identical; the shapes reduce
    # under the frozen tactic body (``⟨rfl, rfl⟩`` / ``rfl``), so no new lemma,
    # axiom, or assumption token is introduced.
    # =====================================================================
    {
        "id": "pos-glossary-reshaped-pair",
        "kind": "soundness",
        "expect": "verify",
        # Reshape: build the pair as a single local instead of two named copies.
        # Same value on every input; proof body unchanged (both projections rfl).
        "module": _swap(
            _BASE, _IMPL_GLOSS,
            "def implementation_glossaryTermEntry\n"
            "    (termtext : List Char) : List Char × List Char := Id.run do\n"
            "  let entry := (termtext, termtext)\n"
            "  return entry\n",
        ),
        "rationale": "a correct reshape (a single pair local rather than two "
                     "named copies) still yields (termtext, termtext), so both "
                     "clauses `result.1 = termtext` and `result.2 = termtext` "
                     "hold; must verify, else SPEC-TOO-STRONG. The frozen "
                     "`⟨rfl, rfl⟩` body still closes because each projection "
                     "reduces definitionally. No new declaration or assumption.",
    },
    {
        "id": "pos-xref-reshaped",
        "kind": "soundness",
        "expect": "verify",
        # Reshape: drop the `Id.run do` wrapper and return the input directly as
        # a pure def. Same value; proof body (`intro; rfl`) still closes.
        "module": _swap(
            _BASE, _IMPL_XREF,
            "def implementation_termXrefTarget (target : List Char) : List Char :=\n"
            "  target\n",
        ),
        "rationale": "a correct reshape (a pure passthrough instead of the "
                     "`Id.run do` wrapper) still yields `target`, so "
                     "`result = target` holds; must verify, else SPEC-TOO-"
                     "STRONG. The frozen `intro; rfl` body closes because the "
                     "reshaped impl is definitionally the identity. No new "
                     "declaration or assumption.",
    },

    # ---- non-definitional positives ----
    # AUDIT NOTE (why these exist). The two reshapes above are DEFINITIONALLY
    # equal to the frozen impl: both verify under the frozen tactic body
    # unchanged, so they exercise `rfl`'s reduction and not the spec. That is a
    # weak positive control — it cannot distinguish "the spec admits correct
    # impls of a different shape" from "the spec admits impls `rfl` already
    # closes". The two cases below are correct impls that are NOT definitionally
    # the frozen one: each was machine-checked to FAIL under the frozen proof
    # body (exit 1, `Application type mismatch: rfl ... expected to have type
    # (implementation_… ).2 = termtext` / `Tactic 'rfl' failed`) and to verify
    # only once its proof region genuinely re-establishes the clause. So these
    # are the cases that actually test SPEC-TOO-STRONG: a spec that pinned the
    # impl's SYNTACTIC form rather than its value would reject them.
    {
        "id": "pos-glossary-nondefeq-reshape",
        "kind": "soundness",
        "expect": "verify",
        # Reshape: the key is rebuilt with a pointwise identity map and the index
        # term by reversing twice. Same value on every input, but neither is
        # definitionally `termtext`, so the obligation must be RE-PROVEN.
        "module": _swap(
            _swap(
                _swap(_BASE, _I_KEY, "  let key := termtext.map id\n"),
                _I_INDEX, "  let indexTerm := termtext.reverse.reverse\n"),
            _PROOF_GLOSS,
            "  intro t\n"
            "  unfold problem_spec_glossaryTermEntry "
            "implementation_glossaryTermEntry\n"
            "  refine ⟨?_, ?_⟩ <;> simp [Id.run] <;> rfl\n",
        ),
        "rationale": "a correct reshape that is NOT definitionally the frozen "
                     "impl: `termtext.map id` and `termtext.reverse.reverse` both "
                     "equal `termtext` in VALUE but not by reduction, so the "
                     "frozen `⟨rfl, rfl⟩` body does not close it (checked: exit 1, "
                     "`rfl ... expected to have type (implementation_…).2 = "
                     "termtext`). Both clauses still hold, so it must verify once "
                     "reproven, else SPEC-TOO-STRONG. This is the positive control "
                     "the definitional reshapes above cannot be: it shows the spec "
                     "constrains the VALUE, not the syntactic form. Reproven inside "
                     "the existing proof region by `simp`/`rfl` only — no new "
                     "declaration, axiom, or `sorry`, and the theorem STATEMENT is "
                     "byte-identical.",
    },
    {
        "id": "pos-xref-nondefeq-loop-rebuild",
        "kind": "soundness",
        "expect": "verify",
        # Reshape: rebuild the target one character at a time with an
        # accumulator loop — the per-element copy shape, which on this carrier
        # normalizes to a `List.map`/`flatten` and needs a real induction.
        "module": _swap(
            _swap(
                _BASE, _IMPL_XREF,
                "def implementation_termXrefTarget (target : List Char) : "
                "List Char := Id.run do\n"
                "  let mut acc : List Char := []\n"
                "  for c in target do\n"
                "    acc := acc ++ [c]\n"
                "  return acc\n"),
            _PROOF_XREF,
            "  intro t\n"
            "  unfold problem_spec_termXrefTarget implementation_termXrefTarget\n"
            "  simp [Id.run]\n"
            "  show (List.map (fun x => [x]) t).flatten = t\n"
            "  induction t with\n"
            "  | nil => rfl\n"
            "  | cons a as ih => simp [ih]\n",
        ),
        "rationale": "a correct PER-ELEMENT copy: the target is rebuilt one "
                     "character at a time through an accumulator loop. This is "
                     "the carrier's counterpart of the nagini positive control's "
                     "copy LOOP (see the omission note below), and it is the "
                     "strongest soundness probe here: the loop normalizes to "
                     "`(List.map (fun x => [x]) t).flatten`, which is NOT "
                     "definitionally `t` (the frozen `rfl` body fails, exit 1), so "
                     "the clause `result = target` has to be re-established by "
                     "induction on the input. It must verify, else SPEC-TOO-STRONG "
                     "— a spec that only admitted the straight-line identity would "
                     "be pinning the shape of the fix rather than its behavior. "
                     "Reproven with `simp`/`induction` inside the existing proof "
                     "region; no new declaration, axiom, or `sorry`.",
    },

    # =====================================================================
    # ADMISSIBILITY — a positive control confirming the obligation is
    # SATISFIABLE (non-vacuous) at the normal, F2P-shaped input rather than only
    # in the abstract. The frozen theorem carries NO precondition hypothesis
    # (the behavior is total, `∀ termtext` unguarded), so nagini's precondition-
    # admission probe has no binder to attack; the honest analogue discharges
    # the spec predicate at the exact F2P upper-case term 'TERM2' inside the
    # proof region, alongside (and before) the frozen obligation.
    # =====================================================================
    {
        "id": "admiss-F2P-TERM2-ground-instance",
        "kind": "admissibility",
        "expect": "verify",
        "module": _swap(
            _BASE, _PROOF_GLOSS,
            "  have _ground : problem_spec_glossaryTermEntry ['T','E','R','M','2']\n"
            "      (implementation_glossaryTermEntry ['T','E','R','M','2']) :=\n"
            "    ⟨rfl, rfl⟩\n"
            + _PROOF_GLOSS,
        ),
        "rationale": "the obligation is discharged at the exact F2P upper-case "
                     "term 'TERM2' (both entry components must keep the "
                     "characters verbatim) by `⟨rfl, rfl⟩`, then the frozen "
                     "obligation is closed verbatim. Verifies, else the modeled "
                     "behavior is unsatisfiable at the normal input (the analogue "
                     "of PRECOND-TOO-STRONG). Nothing is assumed: the theorem "
                     "STATEMENT is byte-identical, the ground instance is a "
                     "`have` inside the existing tactic body, no new declaration "
                     "or axiom or `sorry`.",
    },

    # =====================================================================
    # UNIQUENESS / SPEC-TOO-WEAK rivals — wrong impls sharing the frozen spec
    # that MUST be rejected. Each carries (a) the refinement argument that its
    # faithful real patch would NOT resolve the F2P, so a verifying rival would
    # be a true verify-does-not-imply-resolve break rather than an artifact, and
    # (b) a refutation witness pinning the violation at one concrete input.
    # =====================================================================

    # ---- C1: the registration KEY (result.1 — the changed value) ----
    {
        "id": "fold-key-whole",
        "kind": "uniqueness",
        "expect": "reject",
        # THE PRE-PATCH BUG, recast: case-fold the whole registration key, leave
        # the index term verbatim. Agrees with gold on all-lowercase terms;
        # diverges wherever the term has an upper-case letter.
        "module": _swap(
            _BASE, _I_KEY,
            "  let key := termtext.map Char.toLower\n",
        ),
        "refinement": "case-folding the whole key is exactly the pre-patch "
                      "behavior the fix removed: the term is registered under a "
                      "single canonical case, so a term with an upper-case letter "
                      "is stored under a folded key and the F2P assertion (which "
                      "pins the stored key to the upper-case spelling) fails => "
                      "does NOT resolve (this IS the original bug). Agrees with "
                      "gold on all-lowercase terms, so a sampler that only tried "
                      "those would miss it.",
        "rationale": "REJECT from clause C1 (`result.1 = termtext`): folding maps "
                     "an upper-case letter to a different character, so the key "
                     "differs from the term text. The spec pins the exact "
                     "characters, not merely 'some string', so any fold is "
                     "refuted.",
        "witness": (
            "-- Refuted on the registration key of a mixed-case term: the key\n"
            "-- must preserve the term's exact characters, so folding it away\n"
            "-- from the term text violates clause C1 (result.1 = termtext).\n"
            "example : ¬ problem_spec_glossaryTermEntry ['M','y','S','Q','L']\n"
            "    (implementation_glossaryTermEntry ['M','y','S','Q','L']) := by\n"
            "  unfold problem_spec_glossaryTermEntry implementation_glossaryTermEntry\n"
            "  decide\n"
        ),
    },
    {
        "id": "fold-key-first-char",
        "kind": "uniqueness",
        "expect": "reject",
        # NEAR-MISS on C1: fold ONLY the first character of the key, copy the
        # rest verbatim. Correct on every lowercase-first term; diverges only on
        # an upper-case FIRST character. Distinct sub-domain from `fold-key-whole`
        # (which also folds interior letters), so its witness sits at a point
        # where the two rivals differ.
        "module": _swap(
            _BASE, _I_KEY,
            "  let key := match termtext with\n"
            "    | []      => []\n"
            "    | c :: cs => Char.toLower c :: cs\n",
        ),
        "refinement": "folding only the first character still stores the term "
                      "under a wrong key whenever it begins with an upper-case "
                      "letter (the F2P term does), so the stored key disagrees "
                      "with the pinned upper-case spelling and the F2P assertion "
                      "fails => does NOT resolve. NEAR-MISS: it is correct on the "
                      "whole all-lowercase sub-domain AND on interior upper-case "
                      "letters, so its witness sits at ['A','B'] where it folds "
                      "only position 0 (giving ['a','B']) — a point that "
                      "distinguishes it from the whole-string fold rival "
                      "(['a','b']) and from gold (['A','B']).",
        "rationale": "REJECT from clause C1 (`result.1 = termtext`) via the FIRST "
                     "element: position 0 of an upper-case-first term diverges "
                     "(the folded first char), violating the element-wise pin "
                     "while every later position matches.",
        "witness": (
            "-- Refuted on the registration key at the first-character position:\n"
            "-- an upper-case first letter must be preserved in the key, so\n"
            "-- folding position 0 alone violates clause C1.\n"
            "example : ¬ problem_spec_glossaryTermEntry ['A','B']\n"
            "    (implementation_glossaryTermEntry ['A','B']) := by\n"
            "  unfold problem_spec_glossaryTermEntry implementation_glossaryTermEntry\n"
            "  decide\n"
        ),
    },
    {
        "id": "drop-last-of-key",
        "kind": "uniqueness",
        "expect": "reject",
        # Off-by-one on C1: drop the LAST character of the registration key, copy
        # the rest. Correct only on the empty term; wrong (shorter) on every
        # non-empty term.
        "module": _swap(
            _BASE, _I_KEY,
            "  let key := termtext.dropLast\n",
        ),
        "refinement": "truncating the final character stores the term under a "
                      "shortened key (e.g. 'TERM' for 'TERM2'), so the stored key "
                      "disagrees with the pinned full term spelling and the F2P "
                      "assertion fails => does NOT resolve. Correct only on the "
                      "empty term, so it is refuted on every realistic input.",
        "rationale": "REJECT from clause C1 (`result.1 = termtext`): the key is "
                     "one character shorter than the term text on every non-empty "
                     "term, so the length component of the verbatim pin (and "
                     "hence the equality) fails.",
        "witness": (
            "-- Refuted where the key drops the term's last character: the key\n"
            "-- must have the same length as the term text, so a truncated key\n"
            "-- violates clause C1 on any non-empty term.\n"
            "example : ¬ problem_spec_glossaryTermEntry ['a']\n"
            "    (implementation_glossaryTermEntry ['a']) := by\n"
            "  unfold problem_spec_glossaryTermEntry implementation_glossaryTermEntry\n"
            "  decide\n"
        ),
    },

    {
        "id": "fold-key-tail",
        "kind": "uniqueness",
        "expect": "reject",
        # MIRROR NEAR-MISS on C1: keep the first character, fold every LATER one.
        # Exactly complementary to `fold-key-first-char`, and observably a
        # different impl: at ['A','B'] this yields ['A','b'] where that rival
        # yields ['a','B'] (both checked directly, exit 0). Closes the interior-
        # position sub-domain, which the first-char rival is CORRECT on and the
        # whole-string rival only reaches together with position 0.
        "module": _swap(
            _BASE, _I_KEY,
            "  let key := match termtext with\n"
            "    | []      => []\n"
            "    | c :: cs => c :: cs.map Char.toLower\n",
        ),
        "refinement": "folding every character after the first still stores the "
                      "term under a wrong key whenever an INTERIOR letter is "
                      "upper-case, so the stored key disagrees with the pinned "
                      "spelling and the F2P assertion fails => does NOT resolve. "
                      "NEAR-MISS in the complementary direction to the first-char "
                      "rival: it is correct on every term whose only upper-case "
                      "letter is at position 0, so its witness sits at ['a','B'] — "
                      "a point where the first-char rival is exactly CORRECT.",
        "rationale": "REJECT from clause C1 (`result.1 = termtext`) via a "
                     "NON-first element: position 1 of the term diverges while "
                     "position 0 matches, which is the mirror image of the "
                     "first-char rival's failure and pins the element-wise reading "
                     "of the verbatim clause at an interior index rather than only "
                     "at the head.",
        "witness": (
            "-- Refuted on the registration key at an INTERIOR position: an\n"
            "-- upper-case letter after the first must be preserved in the key, so\n"
            "-- folding positions 1.. alone violates clause C1. The first-character\n"
            "-- fold rival is CORRECT at this very input, which is what makes this\n"
            "-- a distinct sub-domain rather than a second spelling of it.\n"
            "example : ¬ problem_spec_glossaryTermEntry ['a','B']\n"
            "    (implementation_glossaryTermEntry ['a','B']) := by\n"
            "  unfold problem_spec_glossaryTermEntry implementation_glossaryTermEntry\n"
            "  decide\n"
        ),
    },

    # ---- C2: the index-entry term (result.2 — the frame component) ----
    {
        "id": "fold-index-term",
        "kind": "uniqueness",
        "expect": "reject",
        # Attack the FRAME component: keep the key verbatim, but case-fold the
        # index-entry term. This is the referentially-transparent analogue of the
        # nagini FRAME-MUTATION rival — a rival that corrupts the component the
        # change leaves untouched. Without clause C2 the spec would let it verify.
        "module": _swap(
            _BASE, _I_INDEX,
            "  let indexTerm := termtext.map Char.toLower\n",
        ),
        "refinement": "case-folding the index-entry term (while leaving the "
                      "registration key correct) corrupts the component the fix "
                      "leaves untouched: the index entry would show the folded "
                      "spelling instead of the term's own case, so the F2P index-"
                      "entry assertion (which pins the entry to the upper-case "
                      "spelling) fails => does NOT resolve. This is not the "
                      "modeled change at all, so a faithful such patch would "
                      "regress the index entry the surrounding behavior "
                      "guarantees.",
        "rationale": "REJECT from clause C2 (`result.2 = termtext`): folding maps "
                     "an upper-case letter of the index term to a different "
                     "character, so result.2 differs from the term text. This is "
                     "the clause that pins the UNCHANGED frame component; a spec "
                     "leaving result.2 free would wrongly accept this rival.",
        "witness": (
            "-- Refuted on the index-entry term of a mixed-case input: the index\n"
            "-- entry must preserve the term's exact characters, so folding it\n"
            "-- violates clause C2 (result.2 = termtext).\n"
            "--\n"
            "-- Stated CLAUSE-PRECISELY. A bare `¬ (C1 ∧ C2)` would be satisfied by\n"
            "-- EITHER conjunct failing, so it could not tell a C2 violation from a\n"
            "-- C1 one — and this rival's whole point is that it leaves the key\n"
            "-- (C1) correct and corrupts only the index entry (C2). The first two\n"
            "-- conjuncts below pin exactly that split, so the refutation is\n"
            "-- attributable to C2 and this case is not a duplicate of the\n"
            "-- key-folding rivals.\n"
            "example : (implementation_glossaryTermEntry ['A']).1 = ['A']\n"
            "    ∧ (implementation_glossaryTermEntry ['A']).2 ≠ ['A']\n"
            "    ∧ ¬ problem_spec_glossaryTermEntry ['A']\n"
            "        (implementation_glossaryTermEntry ['A']) := by\n"
            "  unfold problem_spec_glossaryTermEntry implementation_glossaryTermEntry\n"
            "  decide\n"
        ),
    },
    {
        "id": "drop-last-of-index-term",
        "kind": "uniqueness",
        "expect": "reject",
        # Second attack on the FRAME clause C2, LENGTH-shaped rather than
        # character-valued, at an ALL-LOWERCASE input where `fold-index-term`
        # agrees with the spec. Without this, C2 was probed by exactly one rival
        # at exactly one point, while C1 carried three — the frame clause was the
        # least-defended part of the surface.
        "module": _swap(
            _BASE, _I_INDEX,
            "  let indexTerm := termtext.dropLast\n",
        ),
        "refinement": "truncating the index-entry term (while leaving the "
                      "registration key correct) corrupts the component the "
                      "modeled change leaves untouched: the index entry would show "
                      "a term one character shorter than the term itself, so the "
                      "F2P index-entry assertion (which pins the entry to the full "
                      "term spelling) fails => does NOT resolve. Distinct from the "
                      "index-fold rival: it diverges on ALL-LOWERCASE terms too, "
                      "where case folding is a no-op, so it is refuted at a point "
                      "that rival is satisfied at.",
        "rationale": "REJECT from clause C2 (`result.2 = termtext`): the index "
                     "term is one character shorter than the term text on every "
                     "non-empty term, so the equality fails while C1 still holds. "
                     "Gives the frame clause a SECOND, length-shaped rival at an "
                     "all-lowercase point, so C2 is no longer defended by a single "
                     "character-value attack at a single input.",
        "witness": (
            "-- Refuted on the index-entry term of an all-lowercase input, where\n"
            "-- case folding would be a no-op but truncation is not: the index\n"
            "-- entry must equal the term text, so dropping its last character\n"
            "-- violates clause C2. Clause-precise (key correct, index entry\n"
            "-- wrong), so the refutation is attributable to C2 and not to C1.\n"
            "example : (implementation_glossaryTermEntry ['a','b']).1 = ['a','b']\n"
            "    ∧ (implementation_glossaryTermEntry ['a','b']).2 ≠ ['a','b']\n"
            "    ∧ ¬ problem_spec_glossaryTermEntry ['a','b']\n"
            "        (implementation_glossaryTermEntry ['a','b']) := by\n"
            "  unfold problem_spec_glossaryTermEntry implementation_glossaryTermEntry\n"
            "  decide\n"
        ),
    },

    # ---- C3: the cross-reference lookup target ----
    {
        "id": "fold-xref-target",
        "kind": "uniqueness",
        "expect": "reject",
        # THE LOOKUP-SITE BUG, recast: case-fold the resolved lookup target.
        # This is the pre-patch behavior at the reference site (fold before
        # lookup). Agrees with gold on all-lowercase references; diverges on any
        # upper-case letter.
        "module": _swap(
            _BASE, _IMPL_XREF,
            "def implementation_termXrefTarget (target : List Char) : List Char := Id.run do\n"
            "  return target.map Char.toLower\n",
        ),
        "refinement": "case-folding the lookup target is exactly the pre-patch "
                      "reference-site behavior the fix removed: a reference to a "
                      "term with an upper-case letter would be looked up under a "
                      "folded target and fail to resolve to the same-case term, "
                      "so the case-preserving cross-reference behavior the fix "
                      "introduces is lost => does NOT resolve. Agrees with gold "
                      "on all-lowercase references.",
        "rationale": "REJECT from clause C3 (`result = target`): folding maps an "
                     "upper-case letter to a different character, so the resolved "
                     "target differs from the reference text. The spec pins the "
                     "exact characters, so any fold is refuted.",
        "witness": (
            "-- Refuted on an upper-case reference target: the resolved target\n"
            "-- must preserve the reference's exact characters, so folding it\n"
            "-- violates clause C3 (result = target).\n"
            "example : ¬ problem_spec_termXrefTarget ['T']\n"
            "    (implementation_termXrefTarget ['T']) := by\n"
            "  unfold problem_spec_termXrefTarget implementation_termXrefTarget\n"
            "  decide\n"
        ),
    },
    {
        "id": "drop-last-of-xref-target",
        "kind": "uniqueness",
        "expect": "reject",
        # Off-by-one on C3: drop the LAST character of the resolved target. A
        # second, LENGTH-shaped attack on the `target` binder at an input that
        # `fold-xref-target` (a character-value attack) leaves correct — an
        # all-lowercase target where folding is a no-op but truncation is not.
        # This exercises the spec's dependence on `target` at a distinct point.
        "module": _swap(
            _BASE, _IMPL_XREF,
            "def implementation_termXrefTarget (target : List Char) : List Char := Id.run do\n"
            "  return target.dropLast\n",
        ),
        "refinement": "truncating the final character of the lookup target makes "
                      "a reference resolve to a shortened key that no term is "
                      "registered under, so the cross-reference fails to resolve "
                      "to the intended term => does NOT resolve. It is a distinct "
                      "attack from the case-fold rival: it diverges on "
                      "all-lowercase targets (where folding is a no-op) too, so "
                      "its witness sits at an all-lowercase input the fold rival "
                      "cannot refute.",
        "rationale": "REJECT from clause C3 (`result = target`): the resolved "
                     "target is one character shorter than the reference text on "
                     "every non-empty reference, so the equality fails. Probes "
                     "the `target` binder at ['a','b'] — a point the fold rival "
                     "agrees with gold on — so the battery demonstrates the "
                     "spec's dependence on `target` beyond a single input.",
        "witness": (
            "-- Refuted on an all-lowercase reference where the target drops its\n"
            "-- last character: the resolved target must equal the reference\n"
            "-- text, so a truncated target violates clause C3 (and folding is a\n"
            "-- no-op here, distinguishing this from the case-fold rival).\n"
            "example : ¬ problem_spec_termXrefTarget ['a','b']\n"
            "    (implementation_termXrefTarget ['a','b']) := by\n"
            "  unfold problem_spec_termXrefTarget implementation_termXrefTarget\n"
            "  decide\n"
        ),
    },
    {
        "id": "fold-xref-target-tail",
        "kind": "uniqueness",
        "expect": "reject",
        # NEAR-MISS on C3: keep the FIRST character of the lookup target, fold
        # every later one. Both other C3 rivals transform EVERY position, so
        # each is wrong on essentially the whole non-empty domain; neither
        # probes a proper SUB-DOMAIN of `target`. This one is exactly CORRECT
        # on every single-character reference and on every reference whose only
        # upper-case letter is at position 0 — including ['T'], the point the
        # whole-fold rival is refuted at (checked: exit 0 there) — and wrong
        # only where an INTERIOR character is upper-case. It is the C3
        # counterpart of `fold-key-tail`, which gave C1 its interior-position
        # near-miss; without it C3 was the only clause defended by no near-miss
        # at all, so a spec that pinned `target` merely at position 0 (or only
        # on the whole-list value) would not have been distinguished here.
        "module": _swap(
            _BASE, _IMPL_XREF,
            "def implementation_termXrefTarget (target : List Char) : List Char := Id.run do\n"
            "  match target with\n"
            "  | [] => return []\n"
            "  | c :: cs => return c :: cs.map Char.toLower\n",
        ),
        "refinement": "folding every character of the lookup target after the "
                      "first still resolves a reference under a wrong target "
                      "whenever an INTERIOR letter is upper-case, so a reference "
                      "written with the term's own case does not reach the term "
                      "registered under that spelling and the case-preserving "
                      "cross-reference behavior is lost => does NOT resolve. "
                      "NEAR-MISS: it is correct on every single-character "
                      "reference and on every reference whose only upper-case "
                      "letter is at position 0, so its witness sits at ['a','B'] "
                      "— an interior-position point neither shipped C3 rival "
                      "reaches as a sub-domain.",
        "rationale": "REJECT from clause C3 (`result = target`) via a NON-first "
                     "element: position 1 of the reference diverges while position "
                     "0 matches, pinning the element-wise reading of C3 at an "
                     "interior index rather than only on the whole-list value. "
                     "Gives the `target` binder a near-miss sub-domain rival to "
                     "match the two C1 already carries; this rival is exactly "
                     "SATISFIED at ['T'], the whole-fold rival's refutation point "
                     "(checked directly, exit 0), which is what makes it a "
                     "distinct sub-domain rather than a third spelling of "
                     "`fold-xref-target`.",
        "witness": (
            "-- Refuted on the lookup target at an INTERIOR position: an\n"
            "-- upper-case letter after the first must be preserved in the\n"
            "-- resolved target, so folding positions 1.. alone violates clause\n"
            "-- C3. The whole-fold C3 rival is refuted at ['T'], where THIS rival\n"
            "-- is exactly correct, so the two attack different sub-domains of\n"
            "-- `target` rather than the same one twice.\n"
            "example : ¬ problem_spec_termXrefTarget ['a','B']\n"
            "    (implementation_termXrefTarget ['a','B']) := by\n"
            "  unfold problem_spec_termXrefTarget implementation_termXrefTarget\n"
            "  decide\n"
        ),
    },
]


# No consumed axioms and no deep-model references: both modeled values are
# computed by straight-line identity code from the term/reference text (mapping.md
# records no opaque/axiom callee), so there is no in-model axiom obligation for
# the PBT axiom lane to re-discharge. The axiom lane is G-AX's job in any case.
AXIOM_TESTS = []


# ---------------------------------------------------------------------------
# INDEPENDENT AUDIT RECORD (post-port). Every claim below was re-derived with
# real builds against the frozen artifact; the frozen files were not touched.
#
# What was CONFIRMED.
#   * Statement integrity (attack A): all variants diff against the frozen file
#     ONLY inside an impl region, or inside a proof region for the cases that
#     legitimately reprove. Every `theorem correct_*` STATEMENT is byte-identical.
#   * Witness discrimination (attack B): each reject case's witness was rebuilt
#     against the rival (exit 0) and against the frozen solution (exit 1). Every
#     gold-side failure is a SEMANTIC refutation — `Tactic 'decide' proved that
#     the proposition ¬(…) is false` — not an unknown identifier, a type error, a
#     stuck reduction, or a timeout. No case needs a `witness_reference`: nothing
#     here elaborates through `Classical.choice`, so `decide` reduces on both
#     sides. No witness binds hypotheses, so no consistency probe is required.
#   * Rivals are WRONG, not merely reshaped (attack C): each rival's divergence
#     from the frozen impl was pinned at a literal input by the `decide` witness,
#     so none is definitionally equal to gold on this carrier. Cross-checked in
#     the other direction too: each rival was shown to be SATISFIED at its
#     siblings' witness points (exit 0), which is what makes the points
#     discriminating rather than redundant.
#   * Clause C2 is LOAD-BEARING, not decorative: with `result.2 = termtext`
#     deleted from the spec, the index-term-folding rival VERIFIES (build exit 0).
#     So the frame clause is what rejects it, exactly as claimed.
#   * SPEC-TOO-WEAK probe (attack D): new wrong impls beyond the shipped set were
#     built and none verified — folding the key in the complementary direction,
#     folding both components at once, folding the target upward instead of
#     downward, duplicating the key, truncating the index term, a length-GATED
#     fold (fold only when the term has 3+ characters, to slip past short-input
#     probes), and placeholder substitution at the empty input on each binder.
#     The two that closed a real gap in the battery's coverage were promoted to
#     cases (`fold-key-tail`, `drop-last-of-index-term`); the rest are recorded
#     here because they found nothing. No spec hole was found.
#   * SPEC-TOO-STRONG probe (attack E): five correct reshapes that are NOT
#     definitionally the frozen impl were all proven against the frozen spec
#     (exit 0): pointwise `map id`, double `reverse`, `take length`, `++ []`,
#     `foldr (::) []`, and the accumulator loop. The spec constrains the value,
#     not the shape. Two of these are now shipped as positive controls.
#
# What was REPAIRED (the recorded SOUND was partly hollow).
#   1. Both original positive controls are DEFINITIONALLY equal to the frozen
#      impl — each verifies under the frozen tactic body unchanged, so neither
#      tested whether the spec admits a correct impl of a genuinely different
#      shape. Added `pos-glossary-nondefeq-reshape` and
#      `pos-xref-nondefeq-loop-rebuild`, both checked to FAIL under the frozen
#      `rfl`/`⟨rfl, rfl⟩` body and to verify only once reproven.
#   2. `fold-index-term`'s witness was `¬ (C1 ∧ C2)`, which is satisfied by
#      EITHER conjunct failing and therefore did not attribute the refutation to
#      the frame clause it names — the one thing that case exists to show.
#      Restated clause-precisely (key correct ∧ index entry wrong ∧ spec
#      violated).
#   3. Clause C2 was defended by ONE rival at ONE point, against three on C1.
#      Added `drop-last-of-index-term`, a length-shaped attack on C2 at an
#      all-lowercase input where the folding rival is satisfied.
#   4. The C1 near-miss lane probed only position 0. Added `fold-key-tail`, the
#      complementary interior-position near-miss; the two rivals are observably
#      different impls at ['A','B'] (['a','B'] vs ['A','b'], checked directly).
#   5. Two false prose claims were corrected: the port note's implication that
#      nagini's loop-shaped cases uniformly "collapse" here (the loop-shaped
#      POSITIVE is expressible and is now shipped), and the binder-coverage
#      note's bare point count, which asserted distinctness without showing the
#      points discriminate.
#
# OMISSIONS RE-DERIVED (attack F), one verdict per dropped nagini case.
#   * `frame-mutation-write-input` — INEXPRESSIBLE, and demonstrated rather than
#     asserted. The nagini rival's rejection comes from the permission system: it
#     writes to an input held at a half fractional permission. This carrier has
#     no mutable input, no aliasing and no permissions — `termtext : List Char`
#     is an immutable value, so there is no state a rival could write to and no
#     `insufficient permission` verdict to elicit. The FRAME CONCERN it exists to
#     test does survive translation, and it is not dropped: it becomes the
#     unchanged-component clause C2, now defended by two rivals
#     (`fold-index-term`, `drop-last-of-index-term`) and confirmed load-bearing
#     by the weakened-spec build above.
#   * `pos-control-reshaped-copy` — EXPRESSIBLE (this is a finding against the
#     original port, now fixed). Its content is a per-element copy loop that must
#     re-establish the verbatim postcondition, and that lands here as
#     `pos-xref-nondefeq-loop-rebuild`: an accumulator `for` loop whose result
#     normalizes to `(List.map (fun x => [x]) t).flatten`, which is NOT
#     definitionally `t`. The original port replaced it with straight-line
#     reshapes that `rfl` already closes, which is why defect 1 above existed.
#   * `admissibility-F2P-TERM2` — EXPRESSIBLE and shipped
#     (`admiss-F2P-TERM2-ground-instance`), with one narrowing that is real: the
#     nagini case tests that a PRECONDITION admits the F2P input, and the frozen
#     theorem here has no precondition (`∀ termtext`, unguarded), so there is no
#     precondition to admit. What the Lean case does instead — discharge the spec
#     predicate at the literal F2P term — is non-vacuous and was checked to
#     carry content: substituting a FALSE ground instance in the same slot makes
#     the build fail (exit 1, `Application type mismatch`), so the `have` is not
#     inert decoration.
#   * `partial-fold-first-char`, `partial-fold-all-prepatch`,
#     `partial-drop-last` — all EXPRESSIBLE and all shipped, as
#     `fold-key-first-char`, `fold-key-whole` and `drop-last-of-key`
#     respectively; each re-verified to discriminate.
#   * nagini `AXIOM_TESTS` (empty) — nothing to port; this bundle consumes no
#     axiom either (meta.json `axioms == []`).
#
# No finding was raised against the FROZEN spec: no wrong impl verified and no
# correct impl was rejected, across every probe run.
#
# ---------------------------------------------------------------------------
# SECOND, INDEPENDENT AUDIT (adversarial re-derivation; did not write the port).
# Every number below is an exit code actually observed from
# `scripts/lean_verify.sh`; the frozen artifact was not touched.
#
# CONFIRMED by re-running, not by reading.
#   * Attack A (statement integrity). All 13 shipped variants were re-extracted
#     and diffed against the frozen file: both `theorem correct_*` STATEMENTS are
#     byte-identical in every case, and every diff hunk falls inside an impl
#     region (or, for the two reproving positives and the admissibility case, a
#     proof region). No case reformats a statement.
#   * Attack B (witness discrimination, re-derived). All 8 reject witnesses were
#     rebuilt with the gate's own `witness_file` surgery: rival exit 0 / gold
#     exit 1 in all 8. Every gold-side error is `Tactic `decide` proved that the
#     proposition … is false` — a plain evaluation of the concrete claim, i.e. a
#     SEMANTIC refutation, with no unknown identifier, type error, stuck
#     reduction, or timeout anywhere.
#   * Attack B' (the FORGERY test) was run on all 8 anyway, since a cheap check
#     is worth more than a judgement call about an error's character. Each
#     witness was rebuilt with its claim FLIPPED (the `¬` dropped; for the two
#     clause-precise witnesses, `≠` swapped for `=` as well) and built on both
#     sides. Result in all 8: flipped-claim on GOLD exits 0 with an empty log,
#     flipped-claim on the RIVAL exits 1 with `decide` refuting the flipped
#     proposition. So gold's exit code inverts exactly when the claim inverts —
#     it carries full information about what is being claimed, and none of these
#     cases is hollow.
#   * Attack C (wrong vs merely reshaped). Each rival's divergence is pinned at a
#     literal input by a `decide` witness, so none is definitionally gold. The
#     port's AGREEMENT claims — the ones that make the points discriminating
#     rather than redundant — were each re-derived as a build and all came back
#     exit 0: the whole-fold key rival is satisfied at ['m','y','s','q','l'], the
#     fold-target rival at ['a','b'], the index-fold rival at ['a','b'], the
#     first-char rival at ['a','B'], the tail-fold rival at ['A']; and the two
#     C1 near-misses were confirmed to yield DIFFERENT values at ['A','B']
#     (['a','B'] vs ['A','b']). Every discrimination sentence in this file is
#     machine-backed.
#   * Both clauses of the glossary spec are LOAD-BEARING, re-derived in both
#     directions on scratch copies of the spec (never in the bundle): with
#     `result.2 = termtext` deleted the index-fold rival VERIFIES (exit 0), and
#     with `result.1 = termtext` deleted the key-fold rival VERIFIES (exit 0).
#     Neither clause is decorative.
#   * The admissibility `have` carries content, not decoration: substituting a
#     FALSE ground instance in the same slot fails (exit 1, `Application type
#     mismatch … expected to have type (['t','e','r','m','2'], …).1 =
#     ['T','E','R','M','2']`). The two non-defeq positives' central claim was
#     also re-derived: each rival impl under the FROZEN proof body fails (exit 1),
#     so they really do require reproving and are not `rfl`-closable reshapes.
#   * Attack D (SPEC-TOO-WEAK). Eight NEW wrong impls this battery did not
#     contain were built against the frozen spec and ALL were rejected (exit 1):
#     a length-GATED fold that only folds terms of 6+ characters (aimed squarely
#     past every shipped witness point, the longest of which is 5 characters);
#     an UPWARD fold (`Char.toUpper`) instead of a downward one; a fold of the
#     key's LAST character only; key duplication (`termtext ++ termtext`); a
#     placeholder returned only at the EMPTY xref target (a point no shipped
#     witness reaches); folding BOTH glossary components at once; a first-char-
#     preserving fold of the xref target; and a length-preserving character
#     blank-out (`map (fun _ => 'x')`). No spec hole. One further probe, swapping
#     the pair's two components, VERIFIES (exit 0) — correctly so: on this
#     carrier both components are `termtext`, so the swap is observationally
#     identical to gold and is a reshape, not a rival.
#   * Attack E (SPEC-TOO-STRONG). Four correct reshapes that are NOT
#     definitionally the frozen impl were proven against the frozen spec (exit
#     0): `take length`, `filter (fun _ => true)`, `++ []`, and `foldr (::) []`.
#     The spec constrains the VALUE, not the shape. A fifth — the accumulator
#     `for` loop moved onto the glossary KEY rather than the xref target — I did
#     not close (exit 1, residual `(pure (do let r ← forIn …; pure r, t)).1 = t`);
#     that is my own tactic gap on the `Id.run`-inside-`Id.run` nesting, NOT
#     evidence about the spec, and the equivalent loop IS proven on the xref
#     obligation by the shipped `pos-xref-nondefeq-loop-rebuild`. Recorded as
#     uncertain rather than claimed as a hole.
#   * Attack F' (divergence lane). VACUOUS here, for a structural reason rather
#     than a tactical one: this is the bare `lean` backend, whose Solution.lean
#     carries no `set_option loom.semantics.termination` at all (that option is a
#     velvet-bundle construct — G-HYGIENE only requires it there). Both frozen
#     impls are straight-line, total, non-recursive functions over `List Char`,
#     and a variant may not add a `partial` declaration or a new decl of any kind
#     under `variant_scope`. So there is no diverging impl to express in the one
#     region a case may edit, and no termination obligation for a rival to fail.
#   * Attack G (coverage). `pbt_coverage.py` reports `obl=2 cases=14 (+5/-9)
#     binders=2 pts=2-6 ok`. Advisory, and the per-binder variation was checked
#     to be MEANINGFUL by the agreement builds above rather than accepted on the
#     count.
#
# REPAIRED by this audit.
#   6. Clause C3 had NO near-miss rival, while C1 had two complementary ones.
#      Both shipped C3 rivals (`fold-xref-target`, `drop-last-of-xref-target`)
#      transform EVERY position of `target`, so each is wrong on essentially the
#      whole non-empty domain and neither probes a proper sub-domain — a spec
#      pinning `target` only at position 0, or only on its whole-list value,
#      would not have been distinguished. Added `fold-xref-target-tail`, the C3
#      counterpart of `fold-key-tail`: rival exit 0 / gold exit 1, flipped claim
#      on gold exit 0 (so its gold-side signal tracks the claim), and it is
#      exactly SATISFIED at ['T'] (exit 0) where the whole-fold rival is refuted,
#      which is what makes it a distinct sub-domain. The binder-coverage note was
#      corrected from 2 points on `target` to 3.
#
# The recorded SOUND is EARNED on all 13 pre-existing cases: every reject case's
# gold-side exit code was shown to invert with its claim, and every positive was
# shown to verify for a reason the spec supplies. No finding against the FROZEN
# spec — no wrong impl verified, and no correct impl was rejected that I could
# not attribute to my own proof effort.
