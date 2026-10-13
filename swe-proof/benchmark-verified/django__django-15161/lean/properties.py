"""properties.py — G-PBT falsification battery for django__django-15161 (lean).

NOT a Lean file; a record of adversarial cases the G-PBT gate executes. Each
SPEC case is a full ``Solution.lean`` variant that shares the FROZEN spec
byte-for-byte (region surgery: only text inside the ``-- impl-start`` /
``-- impl-end`` region — and, for a case that legitimately re-proves, inside the
``-- proof-start`` / ``-- proof-end`` region — is changed, so
``markers.same_spec`` holds and the single ``theorem correct_deconstructedPath``
STATEMENT stays byte-identical). ``expect:"verify"`` passes iff (in scope AND the
file elaborates with the obligation closed); ``expect:"reject"`` passes iff (in
scope AND it does NOT verify AND the case's refutation ``witness`` holds of the
rival while FAILING on the frozen solution).

DEFENDED SURFACE (one modeled behavior over four inputs):

  deconstructedPath (simplifiedPath : Option String) (isExactType : Bool)
                    (objModule objClassName : String) : String

The chosen canonical path is pinned to the inputs by TWO top-level clauses:

  clause 1  ∀ p, simplifiedPath = some p → isExactType = true → result = p
            (a configured short path is reported VERBATIM, but only for an
             object of exactly the configured class)
  clause 2  (simplifiedPath = none ∨ isExactType = false) →
              result = qualifiedName objModule objClassName
            (otherwise the fully-qualified location — module joined to class
             name with a dot — is reported)

``qualifiedName objModule objClassName = objModule ++ "." ++ objClassName``.

ADVERSARIAL READ of the nagini classes on this carrier:

  * FRAME / PERMISSION MUTATION — VACUOUS. The nagini sibling's #1 class writes
    to a read-only half-permission input (``name.append(DOT())`` against
    ``Requires(Acc(list_pred(name), 1/2))``). Lean is referentially transparent:
    the four inputs are plain values, there is no heap permission to overwrite
    and no aliasing to exploit. The class has no expressible instance here and
    NO substitute is fabricated for it.

  * UNGROUNDED-ORACLE ECHO — VACUOUS. Both clauses are GROUNDED in the arguments
    (clause 1 pins the result to the configured input ``p``; clause 2 to a term
    built only from ``objModule``/``objClassName``); the bundle declares no
    ``opaque``/``axiom``, so there is no answer key an implementation could echo
    without doing the work. In its place the battery carries honest positive
    controls (``pos-*``, ``admiss-*``) that must verify.

  * BRANCH-MISSELECTION (nagini "prepatch echo") — APPLIES to clause 1. A rival
    that always takes the fallback ignores a configured public short path and
    reports the internal-submodule location instead.

  * PARTIAL-DOMAIN / VALUE — APPLIES to both clauses: a rival correct on part of
    the input domain but diverging on a sub-domain (a configured path reported
    with its last code point dropped; the exact-type guard ignored so a subclass
    still gets the short path; the fallback join with the dot dropped or the two
    components joined in the wrong order).

WITNESSES. On a tactic-proof backend "did not verify" is the DEFAULT outcome of
reshaping an implementation — the frozen script is tuned to the frozen match/if
form — so a rejection alone attributes nothing to the spec. Every
``expect="reject"`` case therefore carries a Lean snippet proving the rival
CONTRADICTS the spec at one concrete input. Each is stated directly against the
spec predicate at ``decide``-able literals (the ``∀ p`` of clause 1 is
instantiated at the configured value; the disjunctive hypothesis of clause 2 is
supplied by ``Or.inl``/``Or.inr``), and each was checked to hold of its rival
and to FAIL on the frozen solution (so it discriminates rather than asserting a
tautology).

BINDER + POINT SPREAD. The reject witnesses move all four inputs rather than
fixing them at one convenient tuple:
  * ``simplifiedPath`` over ``some``/``none`` and over two distinct configured
    values;
  * ``isExactType`` over ``true``/``false``;
  * ``objModule`` / ``objClassName`` over distinct literals (the fully-qualified
    location must be produced from THEM, so the two fallback rivals — dropped
    dot and swapped join — pin the dependence on each).
Both clauses are attacked: clause 1 by the always-fallback rival and the
last-code-point-truncation rival (at two different configured-path points),
clause 2 by the exact-guard-ignored, dropped-dot, and swapped-join rivals.

REFINEMENT (verify-does-not-imply-resolve). Each reject case records why its
faithful real patch would NOT resolve the F2P tests, so a verifying rival would
be a true break rather than an artifact: the F2P suite pins the reported path to
an EXACT string for a direct instance of a class with a configured short path
(``django.db.models.Value``) and for a composed serialization, so any rival that
reports the wrong branch, a truncated path, or a malformed fully-qualified
location emits a path the tests reject.

AXIOM lane: EMPTY. meta.json axioms == [] and deep_model_references == []; the
modeled behavior is a total computation over the object's own data, so there is
no axiom-soundness / axiom-containment obligation to probe here (that lane
belongs to G-AX in any case).
"""
from pathlib import Path

INSTANCE = "django__django-15161"

_BASE = (Path(__file__).parent / "Solution.lean").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# ---- region anchors (each unique inside Solution.lean; verified at load) ----
# The full body of the impl region's decision (the `match`), so a replacement
# lands entirely inside the impl region it means to edit.
_I_MATCH = (
    "  match simplifiedPath with\n"
    "  | some p =>\n"
    "    if isExactType then\n"
    "      return p\n"
    "    else\n"
    "      return qualifiedName objModule objClassName\n"
    "  | none =>\n"
    "    return qualifiedName objModule objClassName\n"
)
# The single exact-branch return (unique: the fallback return appears twice, this
# once) — used by the truncation rival to reshape only clause 1's output.
_I_EXACT_RETURN = "      return p\n"
# The FULL frozen tactic body (verbatim, comments included), so a soundness
# positive can re-prove its reshaped impl in place with the statement untouched.
_P_BODY = (
    "  intro simplifiedPath isExactType objModule objClassName\n"
    "  unfold problem_spec_deconstructedPath implementation_deconstructedPath\n"
    "  constructor\n"
    "  · -- short path configured AND exact type ⇒ result = p\n"
    "    intro p hp hexact\n"
    "    subst hp\n"
    "    simp only [Id.run, hexact, if_true]\n"
    "    rfl\n"
    "  · -- otherwise ⇒ fully-qualified location\n"
    "    intro h\n"
    "    cases simplifiedPath with\n"
    "    | none => rfl\n"
    "    | some p =>\n"
    "      cases hexact : isExactType with\n"
    "      | true =>\n"
    "        rcases h with h | h\n"
    "        · exact absurd h (by simp)\n"
    "        · exact absurd h (by simp [hexact])\n"
    "      | false => rfl\n"
)
# The proof's first line, unique inside the proof region — the admissibility
# case threads a ground-instance `have` in front of it, leaving the frozen
# obligation body untouched below.
_P_FIRST = "  intro simplifiedPath isExactType objModule objClassName\n"


# ===========================================================================
# POSITIVE CONTROL (soundness) — structurally different but CORRECT.
# ===========================================================================
# Fuse the nested match/if into a single two-key match (the nagini positive
# control reorders the two top-level branches). Same value on every input, so
# both clauses still hold; the frozen `simp only [..., if_true]` no longer
# applies to the fused shape, so the obligation is re-proved (statement
# byte-identical, no new declaration/axiom/assumption token).
_POS = _swap(
    _swap(
        _BASE, _I_MATCH,
        "  match simplifiedPath, isExactType with\n"
        "  | some p, true => return p\n"
        "  | _, _ => return qualifiedName objModule objClassName\n",
    ),
    _P_BODY,
    "  intro simplifiedPath isExactType objModule objClassName\n"
    "  unfold problem_spec_deconstructedPath implementation_deconstructedPath\n"
    "  constructor\n"
    "  · intro p hp hexact\n"
    "    subst hp; subst hexact\n"
    "    rfl\n"
    "  · intro h\n"
    "    cases simplifiedPath with\n"
    "    | none => rfl\n"
    "    | some p =>\n"
    "      cases hexact : isExactType with\n"
    "      | true =>\n"
    "        rcases h with h | h\n"
    "        · exact absurd h (by simp)\n"
    "        · exact absurd h (by simp [hexact])\n"
    "      | false => rfl\n",
)

# ===========================================================================
# ADMISSIBILITY (soundness) — the frozen obligation is discharged UNCHANGED, but
# a ground-instance `have` first evaluates the spec at a normal F2P-shaped input
# (a configured short path on an exact-type object). The frozen theorems carry
# NO precondition hypothesis (the behavior is total, so `∀` is unguarded), so
# the nagini precondition-admission probe has no binder to attack; the honest
# analogue is to confirm the spec is SATISFIABLE at the input the F2P exercises.
# ===========================================================================
_ADMISS = _swap(
    _BASE, _P_FIRST,
    "  have _ground : problem_spec_deconstructedPath (some \"django.db.models.Value\") true\n"
    "      \"django.db.models.expressions\" \"Value\"\n"
    "      (implementation_deconstructedPath (some \"django.db.models.Value\") true\n"
    "        \"django.db.models.expressions\" \"Value\") := by\n"
    "    unfold problem_spec_deconstructedPath implementation_deconstructedPath\n"
    "    refine ⟨?_, ?_⟩\n"
    "    · intro p hp hit; simp_all\n"
    "    · intro h; rcases h with h | h <;> simp_all\n"
    + _P_FIRST,
)

# ===========================================================================
# UNIQUENESS rivals (reject) — wrong impls sharing the frozen spec + frozen
# proof; each MUST fail to verify AND carry a discriminating witness.
# ===========================================================================

# clause 1 — always take the fallback (this IS the pre-patch behavior): a
# configured public short path is ignored and the internal-submodule location
# is reported.
_WRONG_BRANCH = _swap(_BASE, _I_MATCH, "  return qualifiedName objModule objClassName\n")

# clause 1 — near-miss: the configured branch is selected correctly, but the
# reported path drops its last code point.
_TRUNC = _swap(_BASE, _I_EXACT_RETURN, "      return p.dropRight 1\n")

# clause 2 — ignore the exact-type guard: report the configured short path for
# ANY object, including one that is not of the configured class.
_IGNORE_EXACT = _swap(
    _BASE, _I_MATCH,
    "  match simplifiedPath with\n"
    "  | some p => return p\n"
    "  | none => return qualifiedName objModule objClassName\n",
)

# clause 2 — dropped separator: the fallback concatenates module and class name
# WITHOUT the dot, emitting a malformed location.
_DROP_DOT = _swap(
    _BASE, _I_MATCH,
    "  match simplifiedPath with\n"
    "  | some p =>\n"
    "    if isExactType then\n"
    "      return p\n"
    "    else\n"
    "      return objModule ++ objClassName\n"
    "  | none =>\n"
    "    return objModule ++ objClassName\n",
)

# clause 2 — swapped join: the fallback joins the two components in the wrong
# order (class name before module), so the dependence on EACH of objModule /
# objClassName is pinned.
_SWAP_JOIN = _swap(
    _BASE, _I_MATCH,
    "  match simplifiedPath with\n"
    "  | some p =>\n"
    "    if isExactType then\n"
    "      return p\n"
    "    else\n"
    "      return qualifiedName objClassName objModule\n"
    "  | none =>\n"
    "    return qualifiedName objClassName objModule\n",
)


SPEC_TESTS = [
    # ---- POSITIVE CONTROLS (soundness) ----
    {
        "id": "pos-fused-match",
        "kind": "soundness",
        "expect": "verify",
        "module": _POS,
        "rationale": "a correct reshape (the nested match/if fused into one "
                     "two-key match) computes the same result on every input, so "
                     "both clauses of problem_spec_deconstructedPath still hold; "
                     "if it could not verify the spec would be SPEC-TOO-STRONG. "
                     "Re-proved because the fused shape no longer matches the "
                     "frozen `simp only [Id.run, hexact, if_true]` — the new "
                     "shape substitutes both scrutinees and closes by `rfl`; no "
                     "new declaration, axiom, or assumption token, statement "
                     "byte-identical.",
    },
    {
        "id": "admiss-ground-instance",
        "kind": "admissibility",
        "expect": "verify",
        "module": _ADMISS,
        "rationale": "the obligation is discharged at a ground F2P-shaped input "
                     "(a configured short path on an exact-type object) by a "
                     "`have`, then the frozen obligation is closed verbatim. "
                     "Verifies unless the modeled behavior is unsatisfiable at "
                     "exactly the input the F2P exercises (the analogue of "
                     "PRECOND-TOO-STRONG). Nothing is assumed: the `have` is "
                     "inside the existing tactic body, no new declaration, and the "
                     "theorem statement is byte-identical.",
    },

    # ---- UNIQUENESS rivals (reject) ----
    {
        "id": "weak-always-fallback",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _WRONG_BRANCH,
        "refinement": "always reporting the fully-qualified location ignores a "
                      "configured public short path — this is exactly the "
                      "pre-patch behavior, where a direct instance of a class "
                      "with a configured short path still reports its "
                      "internal-submodule location. The F2P tests pin the "
                      "reported path to the SHORT configured form for such an "
                      "instance, so this would NOT resolve.",
        "rationale": "REJECT from clause 1 (∀ p, simplifiedPath = some p → "
                     "isExactType = true → result = p): with a short path "
                     "configured on an exact-type object the spec requires the "
                     "configured value and the rival returns qualifiedName "
                     "objModule objClassName instead. Refuted at a configured "
                     "path + exact type + a distinct module/class pair.",
        "witness": (
            "example : ¬ problem_spec_deconstructedPath (some \"django.db.models.Value\") true\n"
            "    \"django.db.models.expressions\" \"Value\"\n"
            "    (implementation_deconstructedPath (some \"django.db.models.Value\") true\n"
            "      \"django.db.models.expressions\" \"Value\") := by\n"
            "  unfold problem_spec_deconstructedPath implementation_deconstructedPath\n"
            "  rintro ⟨h1, _⟩\n"
            "  have h := h1 \"django.db.models.Value\" rfl rfl\n"
            "  simp only [Id.run, qualifiedName] at h\n"
            "  exact absurd h (by decide)\n"
        ),
    },
    {
        "id": "weak-truncate-configured",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _TRUNC,
        "refinement": "selecting the configured branch but dropping its last "
                      "code point reports a path one character short of the "
                      "configured one; the F2P tests assert the reported path "
                      "equals the configured value EXACTLY, so this would NOT "
                      "resolve. It is a near-miss of the always-fallback rival: "
                      "it takes the correct branch and diverges only in the "
                      "value, at a different configured-path point.",
        "rationale": "REJECT from clause 1: the spec requires result = p (the "
                     "configured value verbatim) and the rival returns "
                     "p.dropRight 1. Refuted at a SHORT configured value distinct "
                     "from the always-fallback rival's, so the two clause-1 "
                     "rivals do not share a refutation point.",
        "witness": (
            "example : ¬ problem_spec_deconstructedPath (some \"Value\") true \"m\" \"n\"\n"
            "    (implementation_deconstructedPath (some \"Value\") true \"m\" \"n\") := by\n"
            "  unfold problem_spec_deconstructedPath implementation_deconstructedPath\n"
            "  rintro ⟨h1, _⟩\n"
            "  have h := h1 \"Value\" rfl rfl\n"
            "  simp only [Id.run] at h\n"
            "  exact absurd h (by decide)\n"
        ),
    },
    {
        "id": "weak-ignore-exact-guard",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _IGNORE_EXACT,
        "refinement": "reporting the configured short path for ANY object with a "
                      "configured path — ignoring whether the object is of "
                      "exactly the configured class — reports the short path even "
                      "for a subclass instance, which must fall back to its own "
                      "location. A real patch that dropped the exact-type guard "
                      "would emit the wrong path for such instances and would NOT "
                      "resolve.",
        "rationale": "REJECT from clause 2 ((simplifiedPath = none ∨ isExactType "
                     "= false) → result = qualifiedName objModule objClassName): "
                     "with a configured path but isExactType = false the spec "
                     "requires the fully-qualified location and the rival returns "
                     "the configured value. Refuted at some/false — the only "
                     "reject witness that pairs a configured path WITH a "
                     "non-exact type.",
        "witness": (
            "example : ¬ problem_spec_deconstructedPath (some \"django.db.models.Value\") false\n"
            "    \"django.db.models.expressions\" \"Value\"\n"
            "    (implementation_deconstructedPath (some \"django.db.models.Value\") false\n"
            "      \"django.db.models.expressions\" \"Value\") := by\n"
            "  unfold problem_spec_deconstructedPath implementation_deconstructedPath qualifiedName\n"
            "  rintro ⟨_, h2⟩\n"
            "  have h := h2 (Or.inr rfl)\n"
            "  simp only [Id.run] at h\n"
            "  exact absurd h (by decide)\n"
        ),
    },
    {
        "id": "weak-drop-dot-fallback",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _DROP_DOT,
        "refinement": "composing the fully-qualified location WITHOUT the dot "
                      "separator emits a malformed import path (module and class "
                      "name run together); the composed-serialization F2P test "
                      "pins the exact reconstruction string, so a real patch with "
                      "this bug would NOT resolve.",
        "rationale": "REJECT from clause 2: the spec requires result = "
                     "qualifiedName objModule objClassName = objModule ++ \".\" ++ "
                     "objClassName, and the rival omits the dot. Refuted at "
                     "none/true with a distinct module/class pair, pinning the "
                     "dot's presence.",
        "witness": (
            "example : ¬ problem_spec_deconstructedPath none true \"m\" \"n\"\n"
            "    (implementation_deconstructedPath none true \"m\" \"n\") := by\n"
            "  unfold problem_spec_deconstructedPath implementation_deconstructedPath qualifiedName\n"
            "  rintro ⟨_, h2⟩\n"
            "  have h := h2 (Or.inl rfl)\n"
            "  simp only [Id.run] at h\n"
            "  exact absurd h (by decide)\n"
        ),
    },
    {
        "id": "weak-swapped-join",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _SWAP_JOIN,
        "refinement": "joining the fully-qualified location in the wrong order "
                      "(class name before module) emits a path whose components "
                      "are transposed; the F2P tests pin the exact location, so a "
                      "real patch composing it backwards would NOT resolve. This "
                      "rival pins the dependence on EACH of objModule and "
                      "objClassName — swapping them changes the result.",
        "rationale": "REJECT from clause 2: the spec requires result = "
                     "qualifiedName objModule objClassName (module first), and "
                     "the rival returns qualifiedName objClassName objModule. "
                     "Refuted at none/false with two distinct components, so the "
                     "witness moves both isExactType (to false) and the "
                     "module/class values.",
        "witness": (
            "example : ¬ problem_spec_deconstructedPath none false \"a\" \"b\"\n"
            "    (implementation_deconstructedPath none false \"a\" \"b\") := by\n"
            "  unfold problem_spec_deconstructedPath implementation_deconstructedPath qualifiedName\n"
            "  rintro ⟨_, h2⟩\n"
            "  have h := h2 (Or.inl rfl)\n"
            "  simp only [Id.run] at h\n"
            "  exact absurd h (by decide)\n"
        ),
    },
]
