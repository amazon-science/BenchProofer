"""properties.py — G-PBT falsification battery for django__django-12754 (lean).

NOT a Lean file; a record of adversarial cases the G-PBT gate executes. Each
SPEC case is a full ``Solution.lean`` variant that shares the FROZEN spec
byte-for-byte (region surgery: only text inside the single ``-- impl-start`` /
``-- impl-end`` region — and, for a case that legitimately re-proves, inside the
``-- proof-start`` / ``-- proof-end`` region — is changed, so
``markers.same_spec`` holds and the ``theorem correct_createModelDeps`` STATEMENT
stays byte-identical). ``expect:"verify"`` passes iff (in scope AND the file
elaborates with the obligation closed); ``expect:"reject"`` passes iff (in scope
AND it does NOT verify AND the case's refutation ``witness`` holds of the rival
while FAILING on the frozen solution).

================================  DEFENDED SURFACE  ===========================

ONE modeled function (the dependency list emitted for one newly-created model):

  createModelDeps (appLabel modelName : String) (bases : List Base)
                  (modelFields : List String)
                  (fromLookup toLookup : String → String → Option (List String))
                  (primaryKeyRel : Option (String × String)) : List Dep

LOAD-BEARING postcondition (a single membership characterisation, BOTH
directions — no required dependency missing, no spurious one present):

    ∀ d, d ∈ result ↔
      (d = ⟨appLabel, modelName, none, false⟩)                       -- (C1) self
      ∨ (∃ ba bn, Base.dotted ba bn ∈ bases ∧ d = ⟨ba, bn, none, true⟩)  -- (C2) base-create
      ∨ (∃ ba bn fs gs f, Base.dotted ba bn ∈ bases ∧
           fromLookup ba bn = some fs ∧ toLookup ba bn = some gs ∧
           f ∈ fs ∧ f ∉ gs ∧ f ∈ modelFields ∧
           d = ⟨ba, bn, some f, false⟩)                              -- (C3) field-removal
      ∨ (∃ pa pn, primaryKeyRel = some (pa, pn) ∧ d = ⟨pa, pn, none, true⟩)  -- (C4) pk-relation

The nagini sibling models ONLY the field-removal filter (its
``removed_base_fields`` = ``set(old).difference(new).intersection(model)``); on
this carrier that is C3, and its two guards are ``f ∉ gs`` (withdrawn from the
base's current state via ``toLookup``) AND ``f ∈ modelFields`` (re-declared by the
new model). The lean bundle is WIDER: it pins the entire emitted list, so the
battery here defends four independent clauses, not one. The nagini partial-domain
rivals (drop-parent-guard, drop-child-guard, skip-first) port to C3; the extra
lean clauses (self, base-create, pk-relation) get their own attacks with no
nagini counterpart.

ADVERSARIAL READ of the nagini classes on this carrier:

  * FRAME / PERMISSION MUTATION — VACUOUS. The nagini battery MANDATES two
    frame-mutation rivals (write-permission demands on the read-only
    ``parent_after`` / ``child`` set predicates). Lean is referentially
    transparent: ``fromLookup`` / ``toLookup`` / ``modelFields`` are plain values,
    carry no heap permission, and there is no read-only half-permission to
    overwrite and no aliasing to exploit. Both frame-mutation rivals have no
    expressible instance here and NO substitute is fabricated for them.

  * UNGROUNDED-ORACLE ECHO — VACUOUS, exactly as in nagini. The postcondition is
    GROUNDED: membership is characterised by equalities against tuples built only
    from the inputs (``appLabel``, ``modelName``, ``bases``, ``modelFields``,
    ``fromLookup``/``toLookup`` results, ``primaryKeyRel``); the bundle declares no
    ``opaque``/``axiom`` callee, so there is no answer key an impl could echo. In
    its place the battery carries an honest structurally-different POSITIVE
    CONTROL (a ``foldl`` reshape of the base loop) that must verify.

  * PARTIAL-DOMAIN / VALUE — APPLIES to C3. The three nagini partial-domain rivals
    port directly: drop the withdrawn-from-base guard (``f ∉ gs``), drop the
    re-declared-by-model guard (``f ∈ modelFields``), and the off-by-one that
    skips the first candidate field. Each is correct on part of the domain and
    diverges on a sub-domain.

  * SPEC-TOO-WEAK on the UNMODELED-BY-NAGINI clauses — APPLIES. Because the lean
    spec also pins C1/C2/C4, three further rivals drop the self dependency, the
    base-creation dependency, and the primary-key-relation dependency — each a
    required-membership omission the frozen spec must reject. A fifth rival
    attacks the ``Base.other`` arm (a non-dotted base must contribute NOTHING):
    every clause quantifies over ``Base.dotted ba bn ∈ bases``, so a dependency
    emitted for a non-dotted base is supplied by no disjunct.

  * ADMISSIBILITY — APPLIES, and is CARRIED (``adm-f2p-shape``). The frozen
    obligation has no precondition hypothesis, but "no precondition" is NOT a
    reason to drop this lane: on a total carrier the analogue of
    PRECOND-TOO-STRONG is the obligation being UNSATISFIABLE at a
    regression-shaped input. A spec that no admissible dependency list can
    satisfy positively at the shape the change must handle is unusable however
    many rivals it rejects, and no ``expect="reject"`` case can detect that —
    rivals only ever show the spec refuses things. So the positive discharges
    ``problem_spec_createModelDeps`` at one concrete regression-shaped point
    (a base that withdrew a field the new model re-declares) as a ``have``,
    by evaluation, before closing the frozen obligation verbatim.

WITNESSES. On a tactic-proof backend "did not verify" is the DEFAULT outcome of
reshaping an implementation — the frozen script (which normalises the impl to a
``resultForm`` and closes a membership ``iff``) is tuned to the frozen shape — so
a rejection alone attributes nothing to the spec. Every ``expect="reject"`` case
therefore carries a Lean snippet proving the rival CONTRADICTS the spec at one
concrete input, stated directly against ``problem_spec_createModelDeps`` at
``decide``-able literals (small string / list / Option literals; the whole
membership predicate reduces by ``decide`` once the emitted list is a literal).
Two witness shapes are used: a MISSING required dependency is refuted by taking
the ``iff``'s ``mpr`` (the spec DEMANDS ``d ∈ result``) and ``decide``-ing that the
rival's list does not contain it; a SPURIOUS dependency is refuted by taking
``mp`` (``d ∈ result`` for the rival) and showing every spec disjunct fails.
Each was checked to hold of its rival and to FAIL on the frozen solution (so it
discriminates rather than asserting a tautology); ``native_decide`` is banned and
not used.

Witness inputs are spread across the modeled domain rather than fixed at one
point. Every INPUT BINDER of the spec predicate is moved by the reject set:
``appLabel`` / ``modelName`` (``"a"`` vs ``"app6"`` / ``"B"`` vs ``"Model6"``),
``bases`` (empty vs a dotted base vs a NON-dotted ``Base.other``),
``modelFields`` (empty vs ``["x"]``), ``fromLookup`` / ``toLookup`` (``none`` vs
``some``-valued, with disagreeing lists), and ``primaryKeyRel`` (``none`` vs
``some``). All four postcondition clauses are attacked, plus the ``Base.dotted``
guard the base clauses share.

AUDIT NOTE on the two directions a reject case cannot test. The reject lane shows
only that the spec REFUSES things; two failure modes need positives, and both are
carried. SPEC-TOO-STRONG is covered by ``pos-foldl-base-loop`` (a faithful correct
reshape that must verify). PRECOND-TOO-STRONG is covered by ``adm-f2p-shape``; an
earlier revision of this manifest recorded that lane as having no object here
because the frozen obligation carries no precondition hypothesis, which is not a
reason — see the ADMISSIBILITY bullet above for what the lane tests on a total
carrier and how the case was checked to discriminate.

AXIOM lane: DROPPED. The nagini AXIOM_TESTS (the containment probe re-running the
``selected`` == real set-algebra equivalence) belong to G-AX, not to this gate;
they are omitted here by design. This bundle declares no consumed axiom
(``axioms`` region is empty; every op is modeled directly over ``List`` /
``Option`` / ``String``), so there is no callee contract for this lane to fuzz.
"""
from pathlib import Path

INSTANCE = "django__django-12754"

_BASE = (Path(__file__).parent / "Solution.lean").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# ---------------------------------------------------------------------------
# Region anchors — each lies strictly inside the impl region (or, for the
# positive control, the impl + proof regions), and each is unique in the frozen
# file, so same_spec and the byte-identical obligation statement are preserved by
# construction.
# ---------------------------------------------------------------------------

# (C1) self proxy-removal dependency: initialise the accumulator WITHOUT it.
_SELF_OLD = "  let mut deps : List Dep := [⟨appLabel, modelName, none, false⟩]\n"
_SELF_NEW = "  let mut deps : List Dep := []\n"

# (C2) base-creation dependency: emit only the field-removal deps for a dotted
#      base, dropping the leading ⟨ba, bn, none, true⟩ creation dependency.
_BASECRE_OLD = (
    "      ⟨ba, bn, none, true⟩ ::\n"
    "        (match fromLookup ba bn, toLookup ba bn with"
)
_BASECRE_NEW = "      (match fromLookup ba bn, toLookup ba bn with"

# (C3) field-removal predicate. The frozen guard keeps a base field `f` iff it is
#      NO LONGER declared by the base (`!newFields.contains f`) AND re-declared by
#      the new model (`modelFields.contains f`).
_PRED = "(fun f => !(newFields.contains f) && modelFields.contains f)"
# drop the withdrawn-from-base guard: keep every field the model re-declares,
# even ones the base STILL declares.
_PRED_DROP_PARENT = "(fun f => modelFields.contains f)"
# drop the re-declared-by-model guard: keep every withdrawn base field, even ones
# the new model never declares.
_PRED_DROP_CHILD = "(fun f => !(newFields.contains f))"

# (C3) skip-first: an off-by-one that never considers the base's FIRST prior
#      field. Correct unless that first field is the withdrawn-and-re-declared one.
_FILTER_OLD = "oldFields.filter (fun f => !(newFields.contains f) && modelFields.contains f)"
_FILTER_SKIP = "(oldFields.drop 1).filter (fun f => !(newFields.contains f) && modelFields.contains f)"

# (C2/C3) the `Base.other` arm: a non-dotted base must contribute NOTHING. Every
#      spec clause quantifies over `Base.dotted ba bn ∈ bases`, so ANY dependency
#      emitted for a non-dotted base is supplied by no disjunct.
_OTHER_OLD = "  | Base.other => []\n"
_OTHER_NEW = "  | Base.other => [⟨\"\", \"\", none, true⟩]\n"

# (C4) primary-key-relation dependency: drop the whole trailing append.
_PK_OLD = (
    "  if let some (pa, pn) := primaryKeyRel then\n"
    "    deps := deps ++ [⟨pa, pn, none, true⟩]\n"
    "  return deps\n"
)
_PK_NEW = "  return deps\n"

# POSITIVE CONTROL: replace the `for … do deps := deps ++ …` base loop with the
# equivalent `List.foldl` over the same per-base contribution. Same value on
# every input; the frozen proof normalises the impl through `resultForm` (itself
# a `foldl`), so the reshape lands closer to the normal form — the deprecated
# `List.forIn_yield_eq_foldl` rewrite is no longer needed and `simp` alone closes
# `impl_eq_normalForm`. No new lemma / axiom / assumption; the obligation
# statement is byte-identical.
_FORLOOP_OLD = (
    "  for base in bases do\n"
    "    deps := deps ++ baseDeps modelFields fromLookup toLookup base\n"
)
_FORLOOP_NEW = (
    "  deps := deps ++ bases.foldl "
    "(fun acc b => acc ++ baseDeps modelFields fromLookup toLookup b) []\n"
)
_PROOF_OLD = (
    "  simp only [implementation_createModelDeps, resultForm, Id.run, bind, pure]\n"
    "  cases primaryKeyRel <;> simp [List.forIn_yield_eq_foldl]\n"
)
_PROOF_NEW = (
    "  simp only [implementation_createModelDeps, resultForm, Id.run, bind, pure]\n"
    "  cases primaryKeyRel <;> simp\n"
)

# ADMISSIBILITY: discharge the obligation at ONE concrete regression-shaped input
# before running the frozen body. The `have` applies the postcondition itself at
# that point (it is not a definitional identity), so it measures whether the spec
# is SATISFIABLE there — the total-carrier analogue of PRECOND-TOO-STRONG. The
# point: a new model `app.Child` declaring "title", inheriting the dotted base
# `base.Parent` whose prior state declared ["id","title"] and whose current state
# declares only ["id"] — so "title" is withdrawn-and-re-declared and C3 demands
# exactly one field-removal dependency alongside C1's self dep and C2's base-create
# dep. Checked to DISCRIMINATE, not restate: omitting the field-removal dep leaves
# `case mpr.inr.inr ⊢ False` unsolved, and adding a spurious dep for the still-declared
# "id" leaves `case mp.inr.inr.inr ⊢ False` unsolved — each flip fails in its own
# direction, so the `have` reads the spec's verdict at this input rather than
# asserting a tautology. Impl and proof are otherwise byte-identical to the frozen
# file, so this case can only fail on the obligation being unsatisfiable here.
_ADMISS_NEW = (
    "  have _hAdmissible : problem_spec_createModelDeps \"app\" \"Child\"\n"
    "      [Base.dotted \"base\" \"Parent\"] [\"title\"]\n"
    "      (fun _ _ => some [\"id\", \"title\"]) (fun _ _ => some [\"id\"]) none\n"
    "      [⟨\"app\", \"Child\", none, false⟩, ⟨\"base\", \"Parent\", none, true⟩,\n"
    "       ⟨\"base\", \"Parent\", some \"title\", false⟩] := by\n"
    "    unfold problem_spec_createModelDeps\n"
    "    intro d\n"
    "    simp only [List.mem_cons, List.not_mem_nil, or_false, List.mem_singleton,\n"
    "      Base.dotted.injEq, Option.some.injEq, Dep.mk.injEq]\n"
    "    aesop\n"
) + _SELF_OLD

# sanity: every anchor present exactly once in the frozen solution.
for _a in (_SELF_OLD, _BASECRE_OLD, _PRED, _FILTER_OLD, _PK_OLD, _OTHER_OLD,
           _FORLOOP_OLD, _PROOF_OLD):
    assert _BASE.count(_a) == 1, f"anchor drifted from Solution.lean: {_a!r}"


SPEC_TESTS = [
    # =====================================================================
    # POSITIVE CONTROL (soundness) — a structurally different but CORRECT
    # implementation that MUST verify. If a faithful correct impl cannot satisfy
    # the frozen obligation the spec is SPEC-TOO-STRONG. Keeps the
    # `theorem correct_createModelDeps` statement byte-identical and re-proves it
    # for the reshaped impl; introduces no helper lemma, axiom, or assumption.
    # =====================================================================
    {
        "id": "pos-foldl-base-loop",
        "kind": "soundness",
        "expect": "verify",
        "module": _swap(
            _swap(_BASE, _FORLOOP_OLD, _FORLOOP_NEW),
            _PROOF_OLD, _PROOF_NEW,
        ),
        "rationale": "The imperative `for base in bases do deps := deps ++ …` base "
                     "loop is replaced by the equivalent `bases.foldl (fun acc b => "
                     "acc ++ baseDeps … b) []`. Both accumulate the same per-base "
                     "contribution in the same order, so `result` is identical on "
                     "every input and the whole membership `iff` (C1–C4) still holds; "
                     "a faithful correct reshape must verify (else SPEC-TOO-STRONG). "
                     "Re-proved because the frozen `impl_eq_normalForm` script "
                     "rewrites the `for` loop via `List.forIn_yield_eq_foldl`; the "
                     "foldl shape already matches `resultForm`, so plain `simp` closes "
                     "it. No new declaration; the obligation statement is unchanged.",
    },

    # =====================================================================
    # ADMISSIBILITY (PRECOND-TOO-STRONG) — the obligation must be SATISFIABLE at a
    # regression-shaped input, not merely unfalsified by rivals. Landed in audit:
    # the port had recorded this lane N/A because the frozen obligation carries no
    # precondition hypothesis, which is not a reason — see the header note.
    # =====================================================================
    {
        "id": "adm-f2p-shape",
        "kind": "admissibility",
        "expect": "verify",
        "module": _swap(_BASE, _SELF_OLD, _ADMISS_NEW),
        "rationale": "The ADMISSIBILITY lane. With no precondition hypothesis on "
                     "this total carrier, PRECOND-TOO-STRONG shows up as the "
                     "obligation being UNSATISFIABLE at a regression-shaped input, so "
                     "the impl discharges `problem_spec_createModelDeps` at one "
                     "concrete such point as a `have`, by evaluation, before running "
                     "the frozen body and closing the frozen obligation verbatim: a "
                     "new model `app.Child` declaring \"title\" over the dotted base "
                     "`base.Parent`, whose prior state declared [\"id\",\"title\"] and "
                     "whose current state declares only [\"id\"]. At that point all of "
                     "C1 (self dep), C2 (base-create dep) and C3 (exactly one "
                     "field-removal dep for the withdrawn-and-re-declared \"title\", "
                     "and NONE for the still-declared \"id\") must hold together of a "
                     "single concrete list — the shape the whole modeled behaviour "
                     "exists to produce. This is the postcondition applied at that "
                     "input, NOT a definitional identity: omitting the field-removal "
                     "dependency leaves `case mpr.inr.inr ⊢ False` unsolved and adding "
                     "a spurious one for \"id\" leaves `case mp.inr.inr.inr ⊢ False` "
                     "unsolved, so each flip fails in its own direction. Impl and "
                     "proof are otherwise byte-identical to the frozen file. If it "
                     "FAILS => PRECOND-TOO-STRONG (the spec cannot be satisfied at a "
                     "shape the change must handle) or a spec-shape regression.",
    },

    # =====================================================================
    # UNIQUENESS / SPEC-TOO-WEAK rivals — wrong impls sharing the frozen spec that
    # MUST be rejected. Each carries (a) the refinement argument that its faithful
    # real patch would NOT resolve the graded suite, and (b) a refutation witness
    # pinning the violation at one concrete input.
    # =====================================================================

    # ---- C3: drop the withdrawn-from-base guard (ports nagini drop-parent) -----
    {
        "id": "weak-c3-drop-withdrawn-guard",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _PRED, _PRED_DROP_PARENT),
        "refinement": "Dropping the withdrawn-from-base guard (keeping only "
                      "`modelFields.contains f`) emits a field-removal dependency for "
                      "a name the base STILL declares in its current state whenever "
                      "the new model also declares it. In the real fix this is the set "
                      "intersection WITHOUT the difference against the base's new "
                      "state: it appends a `(base, base, field, False)` 'removed field' "
                      "ordering prerequisite for a field that is not being removed at "
                      "all, forcing the new model's create step to wait on a removal "
                      "step that never exists. That fabricated dependency cannot be "
                      "satisfied, so the detector's ordering breaks and the F2P "
                      "regression does not resolve.",
        "rationale": "REJECT from C3: `selected`/C3 keeps `f` only when `f ∉ gs` "
                     "(absent from `toLookup`'s current-state list) AND `f ∈ "
                     "modelFields`. At fromLookup=toLookup=some [\"x\"], modelFields "
                     "[\"x\"] the field \"x\" is still declared by the base (in `gs`), "
                     "so C3 does not require ⟨base, name, some \"x\", false⟩ and no "
                     "other clause supplies it, yet the rival emits it — a spurious "
                     "membership. If it verified the spec would be SPEC-TOO-WEAK on "
                     "the still-declared sub-domain.",
        "witness": (
            "-- The base's current state (toLookup) still lists \"x\", so the field is\n"
            "-- NOT withdrawn and C3 forbids a removal dependency for it; the rival\n"
            "-- emits ⟨\"a\",\"P\",some \"x\",false⟩ anyway. Refuted via `mp`: no spec\n"
            "-- disjunct can supply that spurious member.\n"
            "example : ¬ problem_spec_createModelDeps \"a\" \"B\"\n"
            "    [Base.dotted \"a\" \"P\"] [\"x\"]\n"
            "    (fun _ _ => some [\"x\"]) (fun _ _ => some [\"x\"]) none\n"
            "    (implementation_createModelDeps \"a\" \"B\"\n"
            "      [Base.dotted \"a\" \"P\"] [\"x\"]\n"
            "      (fun _ _ => some [\"x\"]) (fun _ _ => some [\"x\"]) none) := by\n"
            "  intro h\n"
            "  have hm := (h ⟨\"a\", \"P\", some \"x\", false⟩).mp (by decide)\n"
            "  rcases hm with h1 | ⟨ba, bn, hb, he⟩ | "
            "⟨ba, bn, fs, gs, f, hb, hf, hg, hfs, hgs, hfm, he⟩ | ⟨pa, pn, hpk, he⟩\n"
            "  · simp at h1\n"
            "  · simp at he\n"
            "  · simp only [Dep.mk.injEq, Option.some.injEq] at hf hg he\n"
            "    obtain ⟨rfl, rfl, rfl, -⟩ := he\n"
            "    subst hf; subst hg\n"
            "    simp_all\n"
            "  · simp at hpk\n"
        ),
    },

    # ---- C3: drop the re-declared-by-model guard (ports nagini drop-child) -----
    {
        "id": "weak-c3-drop-redeclared-guard",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _PRED, _PRED_DROP_CHILD),
        "refinement": "Dropping the re-declared-by-model guard (keeping only "
                      "`!newFields.contains f`) emits a field-removal dependency for "
                      "EVERY field the base withdrew, even ones the new model never "
                      "declares. In the real fix this is the set difference WITHOUT the "
                      "intersection against the new model's own declared field names: it "
                      "appends a removal prerequisite for unrelated base fields that were "
                      "simply removed, forcing the new model's create step to wait on "
                      "removals it has nothing to do with. This over-orders the create "
                      "step against unrelated (possibly circular) removals in the broad "
                      "inheritance-ordering suite, so the faithful patch does not "
                      "resolve.",
        "rationale": "REJECT from C3: C3 keeps `f` only when `f ∈ modelFields` also "
                     "holds. At fromLookup=some [\"x\"], toLookup=some [] (so \"x\" is "
                     "withdrawn), modelFields=[] the model does NOT re-declare \"x\", so "
                     "C3 does not require ⟨base, name, some \"x\", false⟩ and no other "
                     "clause supplies it, yet the rival emits it. If it verified the "
                     "spec would be SPEC-TOO-WEAK on the not-re-declared sub-domain.",
        "witness": (
            "-- \"x\" is withdrawn from the base (in fromLookup, not in toLookup) but\n"
            "-- the new model does NOT declare it (modelFields = []), so C3 forbids a\n"
            "-- removal dependency for it; the rival emits it anyway. Refuted via `mp`.\n"
            "example : ¬ problem_spec_createModelDeps \"a\" \"B\"\n"
            "    [Base.dotted \"a\" \"P\"] []\n"
            "    (fun _ _ => some [\"x\"]) (fun _ _ => some []) none\n"
            "    (implementation_createModelDeps \"a\" \"B\"\n"
            "      [Base.dotted \"a\" \"P\"] []\n"
            "      (fun _ _ => some [\"x\"]) (fun _ _ => some []) none) := by\n"
            "  intro h\n"
            "  have hm := (h ⟨\"a\", \"P\", some \"x\", false⟩).mp (by decide)\n"
            "  rcases hm with h1 | ⟨ba, bn, hb, he⟩ | "
            "⟨ba, bn, fs, gs, f, hb, hf, hg, hfs, hgs, hfm, he⟩ | ⟨pa, pn, hpk, he⟩\n"
            "  · simp at h1\n"
            "  · simp at he\n"
            "  · simp only [Dep.mk.injEq, Option.some.injEq] at hf hg he\n"
            "    obtain ⟨rfl, rfl, rfl, -⟩ := he\n"
            "    subst hf; subst hg\n"
            "    simp_all\n"
            "  · simp at hpk\n"
        ),
    },

    # ---- C3: off-by-one, never consider the base's first field (ports skip-first)
    {
        "id": "weak-c3-skip-first-field",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _FILTER_OLD, _FILTER_SKIP),
        "refinement": "Filtering `oldFields.drop 1` instead of `oldFields` never "
                      "considers the base's FIRST prior field. It is correct whenever "
                      "that first field does not qualify, but DROPS a "
                      "withdrawn-and-re-declared first field. In the real fix this is "
                      "iterating the base's prior field set while silently skipping the "
                      "first key: a base whose first withdrawn field is the one moved "
                      "onto the subclass gets NO `(base, base, field, False)` "
                      "dependency, the create step is not ordered after the removal, "
                      "and the exact FieldError the patch fixes recurs — the F2P still "
                      "sees the wrong operation order and does not resolve.",
        "rationale": "REJECT from C3: C3 requires ⟨base, name, some f, false⟩ for "
                     "EVERY qualifying prior field `f ∈ fs`, including the first. At "
                     "fromLookup=some [\"x\",\"y\"] (so \"x\" is first), toLookup=some "
                     "[] , modelFields=[\"x\"], the field \"x\" qualifies (withdrawn "
                     "and re-declared) so C3 demands its removal dependency, but the "
                     "rival drops the first field and omits it. Missing required "
                     "membership; SPEC-TOO-WEAK if it verified.",
        "witness": (
            "-- \"x\" is the base's FIRST prior field, is withdrawn (not in toLookup),\n"
            "-- and is re-declared by the model, so C3 DEMANDS its removal dependency;\n"
            "-- the skip-first rival omits it. Refuted via `mpr` + `decide` (the\n"
            "-- required member is absent from the rival's list).\n"
            "example : ¬ problem_spec_createModelDeps \"app6\" \"Model6\"\n"
            "    [Base.dotted \"base6\" \"Parent6\"] [\"x\"]\n"
            "    (fun _ _ => some [\"x\", \"y\"]) (fun _ _ => some []) none\n"
            "    (implementation_createModelDeps \"app6\" \"Model6\"\n"
            "      [Base.dotted \"base6\" \"Parent6\"] [\"x\"]\n"
            "      (fun _ _ => some [\"x\", \"y\"]) (fun _ _ => some []) none) := by\n"
            "  intro h\n"
            "  have hm := (h ⟨\"base6\", \"Parent6\", some \"x\", false⟩).mpr\n"
            "    (Or.inr (Or.inr (Or.inl ⟨\"base6\", \"Parent6\", [\"x\",\"y\"], [], \"x\",\n"
            "      by decide, rfl, rfl, by decide, by decide, by decide, rfl⟩)))\n"
            "  exact absurd hm (by decide)\n"
        ),
    },

    # ---- C1: drop the self proxy-removal dependency (no nagini counterpart) ----
    {
        "id": "weak-c1-drop-self-dep",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _SELF_OLD, _SELF_NEW),
        "refinement": "Initialising the accumulator empty omits the model's own "
                      "self proxy-removal dependency `(app_label, model_name, None, "
                      "False)`. In the real code this is the create step's dependency "
                      "on the removal of any prior proxy of the same model; dropping it "
                      "lets the new model be created before its old proxy is deleted, "
                      "reintroducing a name clash the detector is required to order "
                      "around. A patch that dropped it is not a faithful fix and would "
                      "regress the proxy-ordering behaviour.",
        "rationale": "REJECT from C1: the spec requires ⟨appLabel, modelName, none, "
                     "false⟩ ∈ result unconditionally (the first disjunct is a plain "
                     "equality, discharged by `Or.inl rfl`). The rival's list never "
                     "contains it, so `mpr` derives a false membership. Attacks the "
                     "self-dependency clause; SPEC-TOO-WEAK if it verified.",
        "witness": (
            "-- The self proxy-removal dependency is required for every model, even\n"
            "-- with no bases and no primary-key relation; the rival omits it.\n"
            "example : ¬ problem_spec_createModelDeps \"a\" \"B\"\n"
            "    [] [] (fun _ _ => none) (fun _ _ => none) none\n"
            "    (implementation_createModelDeps \"a\" \"B\"\n"
            "      [] [] (fun _ _ => none) (fun _ _ => none) none) := by\n"
            "  intro h\n"
            "  have hm := (h ⟨\"a\", \"B\", none, false⟩).mpr (Or.inl rfl)\n"
            "  exact absurd hm (by decide)\n"
        ),
    },

    # ---- C2: drop the base-creation dependency (no nagini counterpart) ---------
    {
        "id": "weak-c2-drop-base-create-dep",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _BASECRE_OLD, _BASECRE_NEW),
        "refinement": "Emitting only the field-removal deps for a dotted base drops "
                      "the base-CREATION dependency `(base_app_label, base_name, None, "
                      "True)`. In the real code this orders the new subclass's create "
                      "step after the creation of the dotted base it inherits from; "
                      "dropping it lets the subclass be created before its base exists, "
                      "which the detector must never allow. A patch that dropped it "
                      "would break ordinary inheritance ordering and is not a faithful "
                      "fix.",
        "rationale": "REJECT from C2: for every dotted base in `bases` the spec "
                     "requires ⟨ba, bn, none, true⟩ ∈ result (second disjunct). With "
                     "bases = [Base.dotted \"a\" \"P\"] the spec demands ⟨\"a\", \"P\", "
                     "none, true⟩, discharged by the C2 witness `⟨\"a\",\"P\",_,rfl⟩`, "
                     "but the rival's list omits it (it emits only field-removal deps, "
                     "here none). Missing required membership; SPEC-TOO-WEAK if it "
                     "verified.",
        "witness": (
            "-- The dotted base must contribute its creation dependency ⟨\"a\",\"P\",\n"
            "-- none,true⟩ regardless of field removals; the rival drops it.\n"
            "example : ¬ problem_spec_createModelDeps \"a\" \"B\"\n"
            "    [Base.dotted \"a\" \"P\"] [] (fun _ _ => none) (fun _ _ => none) none\n"
            "    (implementation_createModelDeps \"a\" \"B\"\n"
            "      [Base.dotted \"a\" \"P\"] [] (fun _ _ => none) (fun _ _ => none) none) := by\n"
            "  intro h\n"
            "  have hm := (h ⟨\"a\", \"P\", none, true⟩).mpr\n"
            "    (Or.inr (Or.inl ⟨\"a\", \"P\", by decide, rfl⟩))\n"
            "  exact absurd hm (by decide)\n"
        ),
    },

    # ---- C2/C3: a non-dotted base contributes a dependency (landed in audit) ----
    {
        "id": "weak-other-base-emits-dep",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _OTHER_OLD, _OTHER_NEW),
        "refinement": "Making the non-dotted arm emit a dependency instead of nothing "
                      "means a base that is NOT a dotted \"label.name\" reference "
                      "contributes an ordering prerequisite anyway. In the real code the "
                      "non-dotted arm is precisely the one that must contribute nothing: "
                      "a base that is not a dotted string reference names no separate "
                      "model to order against, and inventing a target for it appends a "
                      "prerequisite on a step that does not exist. That dependency can "
                      "never be satisfied, so the detector's ordering breaks on every "
                      "model with an ordinary non-dotted base — far broader than the "
                      "regression under repair, so a patch of this shape does not "
                      "resolve.",
        "rationale": "REJECT from the SHARED GUARD of C2/C3: every clause that can "
                     "supply a base-derived dependency quantifies over "
                     "`Base.dotted ba bn ∈ bases`. With bases = [Base.other] there is "
                     "no dotted base at all, so C2 and C3 are both empty, C1 supplies "
                     "only ⟨appLabel, modelName, none, false⟩ and C4 nothing "
                     "(primaryKeyRel = none) — yet the rival emits ⟨\"\",\"\",none,true⟩. "
                     "Spurious membership no disjunct can supply; SPEC-TOO-WEAK if it "
                     "verified. Attacks the `Base.other` arm, which the other rivals "
                     "leave entirely unprobed, and moves the `bases` binder to a "
                     "non-dotted value no other case reaches.",
        "witness": (
            "-- A non-dotted base sits in `bases`, but C2 and C3 both quantify over\n"
            "-- `Base.dotted ba bn ∈ bases`, so NO clause can supply a base-derived\n"
            "-- dependency here; the rival emits one anyway. Refuted via `mp`: the two\n"
            "-- base clauses die on the impossible membership hypothesis itself.\n"
            "example : ¬ problem_spec_createModelDeps \"a\" \"B\"\n"
            "    [Base.other] [] (fun _ _ => none) (fun _ _ => none) none\n"
            "    (implementation_createModelDeps \"a\" \"B\"\n"
            "      [Base.other] [] (fun _ _ => none) (fun _ _ => none) none) := by\n"
            "  intro h\n"
            "  have hm := (h ⟨\"\", \"\", none, true⟩).mp (by decide)\n"
            "  rcases hm with h1 | ⟨ba, bn, hb, he⟩ | "
            "⟨ba, bn, fs, gs, f, hb, hf, hg, hfs, hgs, hfm, he⟩ | ⟨pa, pn, hpk, he⟩\n"
            "  · simp at h1\n"
            "  · simp at hb\n"
            "  · simp at hb\n"
            "  · simp at hpk\n"
        ),
    },

    # ---- C4: drop the primary-key-relation dependency (no nagini counterpart) --
    {
        "id": "weak-c4-drop-pk-relation-dep",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _PK_OLD, _PK_NEW),
        "refinement": "Removing the trailing append omits the primary-key-relation "
                      "dependency `(pa, pn, None, True)` when a primary-key relation "
                      "target is present. In the real code this orders the new model's "
                      "create step after the creation of the far end of its primary-key "
                      "relation; dropping it lets the model be created before the "
                      "relation target exists. A patch that dropped it would break "
                      "relation ordering and is not a faithful fix.",
        "rationale": "REJECT from C4: when primaryKeyRel = some (pa, pn) the spec "
                     "requires ⟨pa, pn, none, true⟩ ∈ result (fourth disjunct). With "
                     "primaryKeyRel = some (\"p\", \"Q\") the spec demands ⟨\"p\", "
                     "\"Q\", none, true⟩ but the rival's list omits it. Missing "
                     "required membership; SPEC-TOO-WEAK if it verified.",
        "witness": (
            "-- With a primary-key relation present its creation dependency is\n"
            "-- required; the rival drops the whole trailing append.\n"
            "example : ¬ problem_spec_createModelDeps \"a\" \"B\"\n"
            "    [] [] (fun _ _ => none) (fun _ _ => none) (some (\"p\", \"Q\"))\n"
            "    (implementation_createModelDeps \"a\" \"B\"\n"
            "      [] [] (fun _ _ => none) (fun _ _ => none) (some (\"p\", \"Q\"))) := by\n"
            "  intro h\n"
            "  have hm := (h ⟨\"p\", \"Q\", none, true⟩).mpr\n"
            "    (Or.inr (Or.inr (Or.inr ⟨\"p\", \"Q\", rfl, rfl⟩)))\n"
            "  exact absurd hm (by decide)\n"
        ),
    },
]
