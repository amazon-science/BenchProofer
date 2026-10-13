"""properties.py — G-PBT falsification battery for django__django-15128 (lean).

NOT a Lean file; a record of adversarial cases the G-PBT gate executes. Each
SPEC case is a full ``Solution.lean`` variant that shares the FROZEN spec
byte-for-byte (region surgery: only text inside the ``-- impl-start`` /
``-- impl-end`` region — and, for a case that legitimately re-proves or adds a
ground instance, inside the ``-- proof-start`` / ``-- proof-end`` region — is
changed, so ``markers.same_spec`` holds and the ``theorem
correct_renumberAliases`` STATEMENT stays byte-identical). ``expect:"verify"``
passes iff (in scope AND the file elaborates with the obligation closed, no
``sorry``/``admit``/``native_decide`` and no new ``axiom``/``theorem``);
``expect:"reject"`` passes iff (in scope AND it does NOT verify AND the case's
refutation ``witness`` holds of the rival while FAILING on the frozen solution).

DEFENDED SURFACE (one modeled function; a single top-level equality clause over
three input binders):

  problem_spec_renumberAliases
      (pfx : String) (reserved : List Nat) (aliases : List Nat)
      (result : List (Nat × String)) : Prop
      result =
        (aliases.zipIdx).filterMap (fun p =>
          if isReserved reserved p.1 then none
          else some (p.1, freshName pfx p.2))

  The result is the renaming plan: an ordered association list pairing each
  NON-preserved identifier with a fresh name built from ``pfx`` and the
  identifier's 0-based POSITION in the FULL ordered collection (a preserved
  identifier still consumes its position). ``isReserved`` is membership in
  ``reserved``; ``freshName pfx pos = pfx ++ toString pos``. There is NO opaque
  answer key to echo — the result is grounded in the three inputs
  (spec_guide directive 8); the ``axioms`` region declares no ``opaque``/
  ``axiom``.

  The single clause folds three inseparable sub-decisions, each pinned to a
  distinct binder:

    * WHICH identifiers appear — exactly the non-preserved ones. Pinned by the
      ``isReserved reserved p.1`` membership test, i.e. by ``reserved`` (and by
      each element identity ``p.1`` of ``aliases``).
    * WHAT POSITION NUMBER each receives — its index in the FULL enumeration
      (``p.2`` of ``aliases.zipIdx``), so preserving an identifier does NOT
      renumber the identifiers after it. Pinned by ``aliases`` (its length /
      ordering) through the ``freshName pfx p.2`` value.
    * WHAT PREFIX the fresh name carries — ``pfx``, reused for every produced
      name. Pinned by ``pfx``.

ADVERSARIAL READ of the nagini classes on this carrier:

  * FRAME / PERMISSION MUTATION — VACUOUS. The nagini sibling holds ``aliases``
    at a half-permission (``Acc(.,1/2)``) and makes its MANDATORY frame-mutation
    rival WRITE to it (``aliases[pos] = -1``) to trivialise the postcondition,
    which Viper rejects for insufficient permission. Lean is referentially
    transparent: ``aliases``/``reserved``/``pfx`` are immutable values with no
    heap footprint, no aliasing, and no ``mut`` binder over an input — there is
    no read-only cell to overwrite and no permission to violate. This class has
    NO expressible instance here; no substitute is fabricated (porting map:
    vacuous on this backend).

  * UNGROUNDED-ORACLE ECHO — VACUOUS. The post-image is a ``filterMap`` over a
    term built only from the three inputs (``isReserved`` membership plus a
    ``freshName`` string concatenation of ``pfx`` and the enumeration index),
    fully unfolded. No axiomatized oracle exists to echo; the honest analogue is
    the cheapest-correct POSITIVE CONTROL below.

  * PARTIAL-DOMAIN (the pre-patch behaviour) — APPLIES, and is the load-bearing
    rival. The pre-fix construction had NO preservation guard: it renamed every
    identifier, including the one that must stay put. It agrees with gold on
    every input in which nothing is preserved, and diverges precisely when a
    preserved identifier is present — the F2P sub-domain.

  * VALUE / NON-INJECTIVE / WRONG-PREFIX / INVERTED — APPLY. Rivals that ignore
    the enumeration index (all names collapse onto one), drop the prefix, invert
    the preservation test, or special-case the first position each violate the
    one clause on a distinct sub-domain and are refuted with witnesses at
    distinct inputs.

WITNESSES. On a tactic-proof backend "did not verify" is the DEFAULT outcome of
reshaping an implementation — the frozen script is tuned to the frozen
``Id.run do`` / ``for`` / ``continue`` form via ``helper_renum`` — so a rejection
alone attributes nothing to the spec. Every ``expect="reject"`` case therefore
carries a Lean snippet stating the spec predicate directly at a ``decide``-able
concrete input; each was checked with two real ``lake env lean`` builds to HOLD
of its rival and to FAIL on the frozen solution (so it discriminates rather than
asserting a tautology). ``Nat``/``String`` literals are ground and the plan is a
concrete ``List (Nat × String)``, so the snippets ``unfold`` the spec + impl and
``decide`` a list (in)equality; against gold the same ``decide`` faces
``xs = xs`` and fails.

BINDER COVERAGE. All three input binders are varied across the reject witnesses,
and every fold of the single clause is attacked:
  * ``reserved`` — attacked by no-guard (renames the preserved id), inverted
    (renames only the preserved id), and first-position (renames position 0
    regardless of preservation). Witnesses take ``{[1], [7], [], [3], []}``.
  * ``aliases`` (position / element identity) — attacked by collapse (ignores
    the enumeration index) and by first-position; witnesses take
    ``{[1], [7,5], [5,6], [3,5], [5]}``, spanning single- and multi-element
    lists and a preserved-first list.
  * ``pfx`` — attacked by drop-prefix (produces the bare index, dropping the
    prefix). Witnesses take ``{"T", "T", "B", "A", "Z"}`` so it is not pinned to
    one value across the lane.
``pts`` = 5 distinct input points.

AXIOM lane: EMPTY. meta.json axioms == [] and deep_model_references == []; the
renaming plan is modeled deeply as a total function of the three inputs, so
there is no axiom-soundness / axiom-containment obligation to probe here (that
lane belongs to G-AX). AXIOM_TESTS is empty.
"""
from pathlib import Path

INSTANCE = "django__django-15128"
BACKEND = "lean"

_BASE = (Path(__file__).parent / "Solution.lean").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# ---- region anchors (each unique inside Solution.lean; verified at load) ----
# The FULL impl-region def, and the FULL frozen tactic body of
# `correct_renumberAliases`, so every replacement lands entirely inside the
# region it means to edit. `helper_renum` (also in the proof region) is never
# touched — it is left intact so the frozen obligation's proof stays available.
_IMPL_GOLD = (
    "def implementation_renumberAliases\n"
    "    (pfx : String) (reserved : List Nat) (aliases : List Nat) :\n"
    "    List (Nat × String) := Id.run do\n"
    "  let mut changeMap : List (Nat × String) := []\n"
    "  for p in aliases.zipIdx do\n"
    "    if isReserved reserved p.1 then\n"
    "      continue\n"
    "    changeMap := changeMap ++ [(p.1, freshName pfx p.2)]\n"
    "  return changeMap"
)

# The tactic body of `correct_renumberAliases` ONLY (from the first `intro` to
# the closing `rfl`). Lies wholly inside `-- proof-start`/`-- proof-end` and is
# unique in the file.
_PROOF_BODY = (
    "  intro pfx reserved aliases\n"
    "  unfold problem_spec_renumberAliases implementation_renumberAliases\n"
    "  simp only [Id.run]\n"
    "  have hbody :\n"
    "      (forIn aliases.zipIdx ([] : List (Nat × String)) fun p r =>\n"
    "          if isReserved reserved p.1 = true then pure (ForInStep.yield r)\n"
    "          else do\n"
    "            pure PUnit.unit\n"
    "            pure PUnit.unit\n"
    "            pure (ForInStep.yield (r ++ [(p.1, freshName pfx p.2)]))) =\n"
    "      (forIn aliases.zipIdx ([] : List (Nat × String)) fun p r =>\n"
    "          (if isReserved reserved p.1 = true then ForInStep.yield r\n"
    "           else ForInStep.yield (r ++ [(p.1, freshName pfx p.2)]) : Id (ForInStep (List (Nat × String))))) := rfl\n"
    "  rw [hbody]\n"
    "  have := helper_renum aliases.zipIdx pfx reserved []\n"
    "  simp only [Id.run] at this\n"
    "  rw [this, List.nil_append]\n"
    "  rfl"
)

# sanity: the frozen anchors are present exactly once
assert _BASE.count(_IMPL_GOLD) == 1, "impl region drifted; update _IMPL_GOLD"
assert _BASE.count(_PROOF_BODY) == 1, "proof region drifted; update _PROOF_BODY"


def _impl(body):
    """Full Solution.lean variant with only the gold impl body replaced (spec +
    proof view stay byte-identical; the frozen proof no longer matches the
    reshaped impl, which is the expected reject signal — the case is judged by
    its witness, not by whether this script happens to break)."""
    return _swap(_BASE, _IMPL_GOLD, body)


# ---------------------------------------------------------------------------
# POSITIVE-CONTROL impl + proof (soundness).
# ---------------------------------------------------------------------------
# Structurally different but CORRECT: drop the `Id.run do` / `let mut` / `for`
# accumulator entirely and spell the plan as the spec's own `filterMap`. Same
# value on every input; the frozen `helper_renum` route no longer applies to the
# new shape, so the obligation is re-proved — after `unfold` both sides are the
# same `filterMap` term, closed by `rfl`. No new lemma/axiom; statement identical.
_POS_IMPL = (
    "def implementation_renumberAliases\n"
    "    (pfx : String) (reserved : List Nat) (aliases : List Nat) :\n"
    "    List (Nat × String) :=\n"
    "  (aliases.zipIdx).filterMap (fun p =>\n"
    "    if isReserved reserved p.1 then none\n"
    "    else some (p.1, freshName pfx p.2))"
)
_POS_PROOF = (
    "  intro pfx reserved aliases\n"
    "  rfl"
)


# ---------------------------------------------------------------------------
# ADMISSIBILITY ground instance (prepended to the frozen proof body).
# ---------------------------------------------------------------------------
# Discharge the spec predicate at an F2P-shaped ground input inside the proof
# region, then close the frozen obligation verbatim. The input reserves the base
# identifier (present first, at position 0) while two others are renumbered under
# their FULL-enumeration positions — exactly the "preserve the base alias, bump
# the rest" configuration the F2P combine() exercises. If this could not be
# discharged the modeled behavior would be unsatisfiable at the normal input
# (the analogue of PRECOND-TOO-STRONG). Nothing is assumed: the theorem statement
# is byte-identical, the instance is a `have` inside the existing tactic body,
# and no new declaration/axiom/`sorry` is introduced.
_ADMISS_GROUND = (
    "  have _ground : problem_spec_renumberAliases \"T\" [0] [0, 4, 7]\n"
    "      (implementation_renumberAliases \"T\" [0] [0, 4, 7]) := by\n"
    "    unfold problem_spec_renumberAliases implementation_renumberAliases\n"
    "    decide\n"
)


# ---------------------------------------------------------------------------
# Rival impl bodies (each a full impl region; only the impl changes, so the spec
# and the theorem STATEMENT stay byte-identical; the frozen proof breaks against
# the reshaped body — the expected reject signal — and the witness attributes the
# rejection to the spec).
# ---------------------------------------------------------------------------

# PARTIAL-DOMAIN (= the pre-fix bug): NO preservation guard — every identifier is
# renamed, including the one that must stay put.
_RIVAL_NOGUARD = (
    "def implementation_renumberAliases\n"
    "    (pfx : String) (reserved : List Nat) (aliases : List Nat) :\n"
    "    List (Nat × String) := Id.run do\n"
    "  let mut changeMap : List (Nat × String) := []\n"
    "  for p in aliases.zipIdx do\n"
    "    changeMap := changeMap ++ [(p.1, freshName pfx p.2)]\n"
    "  return changeMap"
)

# FIRST-POSITION: preserve correctly for every position >= 1 but ALWAYS emit the
# position-0 identifier, even when it is the one that must be preserved.
_RIVAL_FIRSTPOS = (
    "def implementation_renumberAliases\n"
    "    (pfx : String) (reserved : List Nat) (aliases : List Nat) :\n"
    "    List (Nat × String) := Id.run do\n"
    "  let mut changeMap : List (Nat × String) := []\n"
    "  for p in aliases.zipIdx do\n"
    "    if p.2 = 0 then\n"
    "      changeMap := changeMap ++ [(p.1, freshName pfx p.2)]\n"
    "    else if isReserved reserved p.1 then\n"
    "      continue\n"
    "    else\n"
    "      changeMap := changeMap ++ [(p.1, freshName pfx p.2)]\n"
    "  return changeMap"
)

# NON-INJECTIVE COLLAPSE: the value ignores the enumeration index and always uses
# position 0, so distinct identifiers collapse onto ONE fresh name.
_RIVAL_COLLAPSE = (
    "def implementation_renumberAliases\n"
    "    (pfx : String) (reserved : List Nat) (aliases : List Nat) :\n"
    "    List (Nat × String) := Id.run do\n"
    "  let mut changeMap : List (Nat × String) := []\n"
    "  for p in aliases.zipIdx do\n"
    "    if isReserved reserved p.1 then\n"
    "      continue\n"
    "    changeMap := changeMap ++ [(p.1, freshName pfx 0)]\n"
    "  return changeMap"
)

# INVERTED preservation test: emit ONLY the preserved identifiers, drop the rest.
_RIVAL_INVERTED = (
    "def implementation_renumberAliases\n"
    "    (pfx : String) (reserved : List Nat) (aliases : List Nat) :\n"
    "    List (Nat × String) := Id.run do\n"
    "  let mut changeMap : List (Nat × String) := []\n"
    "  for p in aliases.zipIdx do\n"
    "    if isReserved reserved p.1 then\n"
    "      changeMap := changeMap ++ [(p.1, freshName pfx p.2)]\n"
    "  return changeMap"
)

# DROP-PREFIX: build the fresh name from the empty prefix, dropping `pfx`.
_RIVAL_DROPPREFIX = (
    "def implementation_renumberAliases\n"
    "    (pfx : String) (reserved : List Nat) (aliases : List Nat) :\n"
    "    List (Nat × String) := Id.run do\n"
    "  let mut changeMap : List (Nat × String) := []\n"
    "  for p in aliases.zipIdx do\n"
    "    if isReserved reserved p.1 then\n"
    "      continue\n"
    "    changeMap := changeMap ++ [(p.1, freshName \"\" p.2)]\n"
    "  return changeMap"
)


def _witness(pfx, reserved, aliases):
    """A refutation snippet: the spec predicate is FALSE of the rival's output at
    a concrete ground input. Checked in a file whose frozen obligation is elided
    by the gate, so no tactic script can mask the verdict; `decide` settles the
    ground `List (Nat × String)` (in)equality after unfolding. Against gold the
    same `decide` faces `xs = xs` and fails, proving the witness discriminates."""
    return (
        f"example : ¬ problem_spec_renumberAliases {pfx} {reserved} {aliases}\n"
        f"    (implementation_renumberAliases {pfx} {reserved} {aliases}) := by\n"
        "  unfold problem_spec_renumberAliases implementation_renumberAliases\n"
        "  decide\n"
    )


SPEC_TESTS = [
    # =====================================================================
    # POSITIVE CONTROL (soundness) — structurally different but CORRECT impl
    # that MUST verify; else SPEC-TOO-STRONG. The `theorem correct_renumberAliases`
    # STATEMENT is byte-identical; the tactic body is re-proved for the new
    # (functional) shape. No helper lemma, axiom, or assumption token.
    # =====================================================================
    {
        "id": "pos-functional-filtermap",
        "kind": "soundness",
        "expect": "verify",
        "module": _swap(_impl(_POS_IMPL), _PROOF_BODY, _POS_PROOF),
        "rationale": (
            "a correct reshape that drops the mutable-accumulator `Id.run do` / "
            "`for` / `continue` loop and expresses the plan directly as the "
            "spec's own `(aliases.zipIdx).filterMap (fun p => if isReserved "
            "reserved p.1 then none else some (p.1, freshName pfx p.2))`. It "
            "produces the same plan on every input, so it must satisfy the clause "
            "`result = (aliases.zipIdx).filterMap …`; if it cannot, the spec is "
            "SPEC-TOO-STRONG. Proof: after `intro`, both sides are the same "
            "`filterMap` term, so the goal closes by `rfl` — no new declaration, "
            "axiom, or assumption token."
        ),
    },

    # =====================================================================
    # ADMISSIBILITY — a positive control confirming the obligation is
    # SATISFIABLE (non-vacuous) at the normal, F2P-shaped input. The frozen
    # theorem carries NO precondition hypothesis (the behavior is total, so the
    # `∀` is unguarded), so nagini's precondition-admission probe has no binder to
    # attack here; the honest analogue discharges the spec predicate at the F2P
    # ground input inside the proof region, alongside the frozen obligation.
    # =====================================================================
    {
        "id": "admiss-preserve-base-ground",
        "kind": "admissibility",
        "expect": "verify",
        "module": _swap(_BASE, _PROOF_BODY, _ADMISS_GROUND + _PROOF_BODY),
        "rationale": (
            "the obligation is discharged at the F2P ground input `pfx=\"T\", "
            "reserved=[0], aliases=[0,4,7]` — the base identifier `0` is present "
            "first (position 0) and preserved, while `4` and `7` are renamed to "
            "their FULL-enumeration positions (`\"T1\"`, `\"T2\"`), so the plan is "
            "`[(4,\"T1\"), (7,\"T2\")]` — by `decide`; then the frozen obligation "
            "closes verbatim. Verifies (else the spec is unsatisfiable at the "
            "normal input, the analogue of PRECOND-TOO-STRONG). Nothing is "
            "assumed: the theorem STATEMENT is byte-identical, the ground instance "
            "is a `have` inside the existing tactic body, and no new "
            "declaration/axiom/`sorry` is introduced."
        ),
    },

    # =====================================================================
    # UNIQUENESS / SPEC-TOO-WEAK rivals — wrong impls sharing the frozen spec
    # that MUST be rejected. Each carries (a) the refinement argument that its
    # faithful real patch would NOT resolve the F2P (so a verifying rival would be
    # a true verify-does-not-imply-resolve break, not an artifact) and (b) a
    # machine-checked refutation witness pinning the violation at one concrete
    # input. The five witnesses probe five DISTINCT input points; across them the
    # binders vary (see BINDER COVERAGE in the module docstring).
    # =====================================================================
    {
        "id": "weak-no-preservation-guard",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(_RIVAL_NOGUARD),
        "refinement": (
            "this is the pre-fix behavior: the plan has NO preservation guard, so "
            "EVERY identifier is renamed — including the base identifier that must "
            "stay put because it has to be present identically on both sides of a "
            "collection combination. Its faithful real patch is exactly the "
            "pre-patch construction, which re-introduces the conflicting renaming "
            "the issue reports (an identifier that is both renamed and the target "
            "of another rename), tripping the downstream disjointness assertion "
            "when the two collections are combined. The F2P observable — combining "
            "the two collections in the order that trips the bug — would FAIL; it "
            "does NOT resolve."
        ),
        "rationale": (
            "REJECT from the clause `result = (aliases.zipIdx).filterMap (…if "
            "isReserved reserved p.1 then none else …)`: the rival drops the "
            "`isReserved` filter, so it emits an entry for a preserved identifier "
            "the spec omits. Refuted at `pfx=\"T\", reserved=[1], aliases=[1]`, "
            "where the sole identifier IS preserved: the spec demands the empty "
            "plan `[]`, but the rival returns `[(1,\"T0\")]`. Attacks the "
            "`reserved` binder (a single preserved id)."
        ),
        "witness": _witness('"T"', "[1]", "[1]"),
    },
    {
        "id": "weak-first-position-always-renamed",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(_RIVAL_FIRSTPOS),
        "refinement": (
            "correct for every position >= 1 but special-cases position 0 to "
            "ALWAYS be renamed, regardless of preservation. The identifier that "
            "must be preserved is the base one, which is FIRST in the ordered "
            "collection. A faithful real patch whose preservation guard skipped "
            "the first enumerated position would rename the base identifier, "
            "re-creating the conflicting-rename intersection the fix removes — the "
            "F2P observable FAILS. Diverges on the exact sub-domain the bug lives "
            "in."
        ),
        "rationale": (
            "REJECT from the same clause at position 0: when the position-0 "
            "identifier is preserved, the spec omits it but the rival emits it. "
            "Refuted at `pfx=\"T\", reserved=[7], aliases=[7, 5]` where identifier "
            "`7` is preserved and sits first: the spec demands `[(5,\"T1\")]` "
            "(only the non-preserved `5`, keeping its FULL-enumeration position "
            "`1`), but the rival returns `[(7,\"T0\"), (5,\"T1\")]`. Attacks the "
            "`reserved` binder at position 0 and, via the retained index `1`, the "
            "enumeration numbering of `aliases`."
        ),
        "witness": _witness('"T"', "[7]", "[7, 5]"),
    },
    {
        "id": "weak-noninjective-collapse",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(_RIVAL_COLLAPSE),
        "refinement": (
            "the fresh name IGNORES the enumeration index and always uses position "
            "0, so distinct identifiers collapse onto ONE fresh name. A faithful "
            "real patch whose produced name did not depend on the position (e.g. a "
            "constant `<prefix>0`) maps every identifier to the SAME new name, "
            "silently merging distinct joins; combining the two collections in "
            "either order then no longer yields the same rows — the F2P's exact "
            "observation FAILS. This is the load-bearing injective-numbering "
            "clause; it does NOT resolve."
        ),
        "rationale": (
            "REJECT from the clause's `freshName pfx p.2` value at position >= 1: "
            "the rival emits `freshName pfx 0` for every entry. Refuted at "
            "`pfx=\"B\", reserved=[], aliases=[5, 6]`: the spec demands "
            "`[(5,\"B0\"), (6,\"B1\")]`, but the rival returns `[(5,\"B0\"), "
            "(6,\"B0\")]`, collapsing the two onto one name. Attacks the "
            "position-numbering fold of the clause over a multi-element "
            "`aliases`; no identifier is preserved here, so the divergence is "
            "purely in the numbering, not the filter."
        ),
        "witness": _witness('"B"', "[]", "[5, 6]"),
    },
    {
        "id": "weak-inverted-preservation",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(_RIVAL_INVERTED),
        "refinement": (
            "the preservation test is INVERTED: only the preserved identifiers are "
            "renamed and every other identifier is left out. A faithful real patch "
            "with an inverted membership guard would rename ONLY the base "
            "identifier (which must be preserved) and leave every conflicting "
            "identifier unchanged, so the combination never disambiguates them — "
            "the F2P observable trips the disjointness assertion / drops joins. It "
            "does NOT resolve."
        ),
        "rationale": (
            "REJECT from the clause's filter: the rival emits exactly the "
            "identifiers the spec omits and omits exactly those the spec emits. "
            "Refuted at `pfx=\"A\", reserved=[3], aliases=[3, 5]`: the spec demands "
            "`[(5,\"A1\")]` (rename the non-preserved `5`), but the rival returns "
            "`[(3,\"A0\")]` (renames the preserved `3`, drops `5`). Attacks the "
            "`reserved` binder in the opposite direction to the no-guard rival — "
            "wrong on BOTH the emitted-preserved id and the dropped-renamable id."
        ),
        "witness": _witness('"A"', "[3]", "[3, 5]"),
    },
    {
        "id": "weak-drop-prefix",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(_RIVAL_DROPPREFIX),
        "refinement": (
            "the fresh name is built from the EMPTY prefix, dropping `pfx`. A "
            "faithful real patch that omitted the freshly chosen, conflict-free "
            "prefix would produce names that no longer live in the fresh "
            "namespace, so a renamed identifier could collide with an existing one "
            "on the other side of the combination — the F2P observable FAILS. It "
            "does NOT resolve. (No nagini counterpart: nagini's fresh value was a "
            "single arithmetic function of the namespace and ordinal with no "
            "separable prefix component; on this carrier the prefix is a distinct "
            "input binder, so it gets its own rival.)"
        ),
        "rationale": (
            "REJECT from the clause's `freshName pfx p.2` value: the rival uses "
            "`freshName \"\" p.2`, dropping the prefix. Refuted at `pfx=\"Z\", "
            "reserved=[], aliases=[5]`: the spec demands `[(5,\"Z0\")]`, but the "
            "rival returns `[(5,\"0\")]`. This is the ONLY rival that attacks the "
            "`pfx` binder, so it is the reason `pfx` is not pinned across the "
            "lane; a rival mishandling only the prefix would otherwise verify."
        ),
        "witness": _witness('"Z"', "[]", "[5]"),
    },
]


# ---------------------------------------------------------------------------
# Nagini -> lean accounting. The sibling battery has 7 SPEC cases (1 soundness
# positive, 1 admissibility, 1 MANDATORY frame-mutation, 4 value/uniqueness
# rivals) plus an EMPTY AXIOM lane. This bundle models the SAME single behavior
# (the renaming-plan construction) but over a referentially-transparent carrier,
# so the frame class is vacuous and the value rivals re-express over the one
# `result = filterMap` clause. Every sibling case is recorded below.
#
#   sibling case                         -> here
#   ---------------------------------------------------------------------
#   pos-control-branch-reorder           -> pos-functional-filtermap   RE-EXPRESSED
#   admiss-read-input                    -> admiss-preserve-base-ground RE-EXPRESSED
#   frame-mutation-overwrite-input       -> (none)                     VACUOUS
#   partial-domain-prepatch-no-exclude   -> weak-no-preservation-guard PORTED
#   partial-domain-firstpos-flag         -> weak-first-position-...    PORTED
#   partial-domain-noninjective-collapse -> weak-noninjective-collapse PORTED
#   support-inverted-flag                -> weak-inverted-preservation PORTED
#   (no counterpart)                     -> weak-drop-prefix           ADDED
#   AXIOM_TESTS (empty)                  -> (none)                     DROPPED (G-AX)
#
# RE-EXPRESSED (positive control): the sibling reorders the two branches of the
#   is_source decision INSIDE the imperative loop. On this carrier a branch
#   reorder inside the `Id.run do` loop desugars to a `forIn` whose body no
#   longer matches the frozen `helper_renum` lemma, so a faithful proof would
#   need a fresh `funext`/`congr` bridge over the do-block — a genuinely new lemma
#   the spec_guide says to avoid in favor of a cheaper shape (a reorder proof was
#   attempted and did not close within the frozen lemma's reach). The ARGUMENT
#   ("a structurally different but faithful impl must verify") is carried instead
#   by the cheapest expressible reshape: drop the imperative scaffold and express
#   the plan as the spec's own `filterMap`, closed by `rfl`. This is a strictly
#   larger structural departure than a branch reorder, so it defends the
#   soundness direction at least as strongly.
# RE-EXPRESSED (admissibility): the sibling asserts the read-only permission grant
#   and well-formedness facts are usable for an F2P-shaped input. This backend has
#   no permission grant and no precondition hypothesis (the `∀` is unguarded — the
#   behavior is total), so there is nothing to admit in the nagini sense. The
#   honest analogue is a ground instance of the spec at the exact F2P
#   configuration (preserve the base id, renumber the rest over the full
#   enumeration), discharged by `decide` alongside the frozen obligation.
# VACUOUS (frame-mutation): the sibling carries this MANDATORY because `aliases`
#   is held at Acc(.,1/2) and a rival can illegally write to it (aliases[pos]=-1)
#   to trivialise the postcondition. Lean is referentially transparent and
#   declares no `mut` binder over an input — every input is an immutable value
#   with no heap footprint — so there is no read-only cell to overwrite and no
#   permission to violate. Not fabricated (porting map: vacuous here).
# PORTED (value rivals): the four partial-domain / near-miss rivals port directly
#   over the single clause. no-preservation-guard IS the pre-patch (drop the
#   isReserved filter). first-position special-cases the base id (position 0).
#   noninjective-collapse ignores the enumeration index (constant position value).
#   inverted flips the membership test. Each carries a machine-checked witness
#   that ELABORATES against the rival and FAILS against the frozen solution.
# ADDED (drop-prefix): on this carrier the fresh name has a separable prefix
#   component (`pfx`, a distinct input binder) that nagini's single-arithmetic
#   fresh_alias did not expose. A rival mishandling only the prefix would verify
#   against a spec that never varied it, so a dedicated rival attacks `pfx`; it is
#   why `pfx` is not pinned to one value across the reject lane.
# AXIOM_TESTS: dropped. The axiom lane is G-AX's job; this bundle declares no
#   axiom (the plan is modeled deeply as a total function of the inputs), so there
#   is nothing to probe and the gate ignores AXIOM_TESTS regardless.
AXIOM_TESTS = []
