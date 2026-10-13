"""properties.py — PBT falsification manifest for django__django-15104 (lean).

NOT a Lean module: a record of adversarially-reasoned cases the G-PBT runner
executes over the frozen `Solution.lean`. Every case edits ONLY the
implementation region (and, for the positive controls, the proof body), so
`variant_scope.same_spec` holds by construction and every rejection is
attributable to the postcondition — never to a tampered spec. No case adds an
axiom, a helper theorem, a `sorry`/`admit`/`native_decide`, and no case rewrites
the `theorem correct_relationAgnosticFields` STATEMENT.

DEFENDED SURFACE
----------------
One modeled function, one obligation:

    implementation_relationAgnosticFields (fields : List FieldDef)
        : Option (List Decon)

pinned by the single load-bearing clause

    result = some (fields.map transformField)

with `transformField f = if f.isRelation then removeTarget f.decon else f.decon`
and `removeTarget d = { d with kwargs := d.kwargs.filter (·.1 != targetKey) }`.

The carrier is FULLY TRANSPARENT — `Decon`/`FieldDef` are `DecidableEq`
structures over `String`/`List String`/`List (String × String)`, and both
`transformField` and `removeTarget` are ordinary computable `def`s. There is no
`opaque` callee anywhere in the spec view, so every rival below is refuted by
`decide` at a CONCRETE input; no carrier conditioning is needed and consequently
no witness binds a hypothesis (there is nothing that could be inconsistent).

Although the clause is a single equation, it pins FIVE logically independent
facts, and the reject lane attacks each one separately:

  (C1) TOTALITY — the result is `some _` for EVERY input, including a
       target-agnostic-eligible field whose keyword mapping records no target at
       all. This is the clause the reported defect violates by not producing a
       result on that sub-domain. Attacked by `absent-target-undefined`.
  (C2) THE FORK, related arm — a field that points at another model must LOSE its
       target entry. Attacked by `keep-target`.
  (C3) THE FORK, unrelated arm — a field that does NOT point at another model is
       carried over UNCHANGED, so a keyword entry that happens to share the
       distinguished key SURVIVES. Attacked by `always-drop`.
  (C4) THE FRAME (spec_guide directive 5) — for every field, the path, the
       positional arguments, and every NON-target keyword entry equal their input
       values. Referential transparency collapses nagini's fractional-permission
       class, but the frame obligation itself does NOT become vacuous here: it is
       discharged STRUCTURALLY by the equation, because the whole `Decon` is an
       observable component of the result. Attacked three ways —
       `drop-trailing-kwargs` (non-target entries after the target are lost),
       `clear-args` (the positional arguments are dropped), and `blank-path`
       (the import path is dropped).
  (C5) THE TRAVERSAL — one output element per input field, in the input order,
       none dropped, duplicated or reordered. Attacked by `reverse-order` and
       `skip-unrelated`.

PORTING NOTES — which nagini cases ported, which did not
-------------------------------------------------------
The nagini sibling contracts a per-field helper taking `(kwargs, is_relation)`
and returning one mapping; this bundle models the WHOLE traversal, taking a list
of fields and returning the list of transforms. So the nagini rivals port with
their argument narrowed to one list element, and the traversal itself becomes a
new attack surface nagini's carrier did not have.

  * nagini `pos-branch-reorder`  -> `pos-fork-reorder`. Same argument (the two
    arms are mutually exclusive, so swapping them is a pure source reshape);
    reproven for the reshaped conditional.
  * nagini `pos-local-reshape`   -> `pos-functional-form`, generalized. Rather
    than merely naming the result in a local, this positive drops the imperative
    accumulation entirely for a direct `map`. That is a strictly bigger reshape
    and therefore a stronger SPEC-TOO-STRONG probe; its proof closes by `rfl`.
  * nagini `pos-guard-present`   -> `pos-guard-present`. The partial-domain TRAP
    carried over intact: removing an absent entry is a no-op, so a variant that
    removes the target only when it is present is BEHAVIOURALLY CORRECT and must
    verify. Its proof is the one real piece of new work here (it needs the
    `filter` no-op lemma inline, since a helper lemma is not admissible).
  * nagini `rival-prepatch-del`  -> `absent-target-undefined` (C1). Nagini
    rejected this at an undischarged callee precondition; here the narrow removal
    is modeled as "no result is produced", so the same rival is refuted by the
    postcondition's own totality demand instead.
  * nagini `rival-always-drop`   -> `always-drop` (C3).
  * nagini `rival-never-drop`    -> `keep-target` (C2).
  * nagini `rival-drop-extra-key` -> `drop-trailing-kwargs` (C4). Re-expressed as
    a truncating traversal of the keyword mapping rather than a second removal,
    which additionally makes the witness sensitive to the target's POSITION
    within the mapping.
  * nagini `rival-frame-mutate-input` — the fractional-permission mechanism is
    nagini-only and does not port (Lean is referentially transparent: there is no
    aliasing and no permission to under-hold). It is NOT dropped as vacuous
    though, because the OBLIGATION it defended survives as C4: the two added
    rivals `clear-args` and `blank-path` attack exactly the components a
    permission-violating write would have corrupted, and they are refuted by the
    result equation itself.
  * ADDED, no nagini counterpart (the traversal is new surface here):
    `reverse-order` and `skip-unrelated` (C5). Nagini's carrier was a single
    mapping, so element order and element count could not be attacked at all.
    `skip-unrelated` is also the rival that most cheaply varies the list LENGTH
    binder dimension.
  * DIVERGENCE / NON-TERMINATION — NOT shippable as a reject case, and the
    precise reason matters (corrected by the independent audit, which measured it
    rather than arguing it). This bundle sets no `loom.semantics.termination`; it
    is vanilla Lean 4, where a `def` is termination-checked, so a diverging impl
    cannot be written as one. It CAN be written as a `partial def` self-call, and
    that variant is scope-admissible (`variant_problems` returns clean) and IS
    rejected by the verifier — so the earlier claim that a diverging impl "cannot
    be written in the first place" was too strong. What blocks the case is the
    WITNESS half, not expressibility: a `partial def` elaborates to an opaque
    constant, so the witness build fails at
    `Tactic `unfold` failed to unfold `implementation_relationAgnosticFields``
    (measured, exit 1) — nothing can be proven about the rival's value, so no
    witness can hold of it, and a rejection with no witness attributes nothing to
    the spec. Recorded as a KNOWN HOLE of the witness carrier, not as a vacuous
    class: the class is real, it simply has no discriminating oracle here.
  * ADMISSIBILITY — PORTED as `admiss-absent-target-ground` (added by the
    independent audit; the earlier "vacuous" disposition was wrong). "The frozen
    obligation carries no precondition hypothesis" does NOT make the lane vacuous:
    the analogue on a total carrier is the obligation being UNSATISFIABLE at
    exactly an F2P-shaped input, which is a real failure mode a `∀`-only statement
    does not rule out (an inconsistent spec predicate is vacuously unprovable at
    every point, and a `∀` obligation that could never be discharged at a normal
    input would be the total-carrier PRECOND-TOO-STRONG). The added positive
    discharges the spec predicate BY EVALUATION at a concrete F2P-shaped input as
    a `have`, then closes the frozen obligation verbatim. Nagini's `admiss-reads`
    mechanism (a half-permission admitting a read) does not port; the OBLIGATION
    it defended does, in the shape sibling cells already use.
  * `AXIOM_TESTS` dropped: the axiom lane is G-AX's job and this gate ignores it.
    (This bundle declares no axiom and no `opaque` callee at all.)

INDEPENDENT AUDIT — probes run beyond the shipped cases
-------------------------------------------------------
Four FRESH wrong impls, aimed at surface the shipped rivals leave unattacked,
were built with witnesses both ways; all four were REJECTED and their witnesses
discriminated (rival exit 0, gold exit 1), so none is a spec hole:
  - emit each transform TWICE (length UP; `skip-unrelated` only moves length DOWN);
  - reverse the surviving keyword entries (internal kwargs ORDER, which no shipped
    witness moves);
  - filter the keyword mapping on the VALUE rather than the key;
  - remove the target only for fields that carry positional arguments (a
    partial-domain rival gated on a component unrelated to the fork).
Two FRESH correct reshapes were also proven, so the spec is not over-fitted
beyond what `pos-functional-form` already shows: a `foldl` accumulation (closed
by `List.reverseRecOn`) and a reverse-map-reverse round trip (closed by
`List.map_reverse`). Both VERIFY, as a faithful impl must.

WITNESSES
---------
Every reject case carries a `witness`: a Lean snippet negating the spec predicate
at one concrete input, checked in a file with the frozen obligations removed. Each
was built BOTH ways with scripts/lean_verify.sh and SEEN to discriminate — exit 0
against its rival, exit 1 against the frozen solution (`decide` proved the
proposition FALSE there, i.e. gold satisfies the spec at that point). The eight
witnesses probe eight DISTINCT inputs, and between them vary every structural
dimension of the sole binder `fields`: its length (1 and 2), `isRelation` (true,
false, and mixed within one list), `path`, `args` (empty / one / two), and
`kwargs` (empty, target-only, target-absent, and target followed by further
entries).

What is NOT claimed (corrected by the independent audit, which computed the full
8x8 rival-by-input agreement matrix): the witnesses are NOT pairwise exclusive.
17 of the 56 off-diagonal cells are refutations too — e.g. `blank-path` is wrong
at six of the eight inputs, and `keep-target` is wrong at `drop-trailing-kwargs`'s
input as well as its own. That is expected and harmless, because what a witness
must do is refute ITS OWN rival while holding of no correct impl, and each of the
eight does exactly that (verified: rival exit 0, gold exit 1, eight times). The
diagonal is what carries the attribution. Each `rationale` below therefore claims
only that its witness LIES IN the sub-domain that rival is wrong on and moves the
binder dimension it names — both of which are mechanically true — and no longer
claims minimality of the input against the other rivals.
"""
from pathlib import Path

INSTANCE = "django__django-15104"

_BASE = (Path(__file__).parent / "Solution.lean").read_text()


def _swap(src: str, old: str, new: str) -> str:
    """Replace exactly one occurrence of a substring; assert it actually matched
    so silent drift (Solution.lean edited) fails loudly at manifest load."""
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# ---------------------------------------------------------------------------
# Region landmarks. Every anchor below lies ENTIRELY inside the impl region or
# entirely inside the proof body, and each is unique across the whole file --
# note the near-duplicate conditional text inside the frozen proof, which is why
# the impl anchors carry their surrounding indentation and `let`/`acc` context.
# ---------------------------------------------------------------------------

# The per-field transform line, inside the impl's `for` body. The `let d :=`
# prefix is what makes it unique (the proof region repeats the conditional).
_FORK = "    let d := if f.isRelation then removeTarget f.decon else f.decon\n"

# The accumulation line, inside the impl's `for` body.
_APPEND = "    acc := acc ++ [d]\n"

# The whole `for` body (transform + accumulate).
_LOOP_BODY = _FORK + _APPEND

# The complete frozen impl declaration.
_IMPL = (
    "def implementation_relationAgnosticFields\n"
    "    (fields : List FieldDef) : Option (List Decon) := Id.run do\n"
    "  let mut acc : List Decon := []\n"
    "  for f in fields do\n"
    + _LOOP_BODY +
    "  return some acc\n"
)
assert _BASE.count(_IMPL) == 1, "impl region drifted from expected text"

# The frozen proof body, verbatim (everything strictly between the proof markers).
_PROOF_OPEN = "-- proof-start\n"
_PROOF = _BASE[_BASE.index(_PROOF_OPEN) + len(_PROOF_OPEN):_BASE.index("-- proof-end")]
assert "theorem correct_relationAgnosticFields" in _PROOF


def _reprove(src: str, new_proof: str) -> str:
    """Replace the proof BODY (a positive control reproves for its new impl
    shape; the `theorem correct_*` statement is re-emitted byte-identically)."""
    return _swap(src, _PROOF, new_proof)


# ===========================================================================
# ADMISSIBILITY — expect "verify". The frozen obligation is closed VERBATIM;
# a ground instance discharged by evaluation is prepended to its tactic body, so
# the case adds a demonstration and subtracts nothing. `intro fields` is the
# frozen proof's first tactic step and is unique in the file.
# ===========================================================================

_INTRO = "  intro fields\n"
assert _BASE.count(_INTRO) == 1, "proof intro anchor drifted"

# An F2P-shaped input: two fields of MIXED relatedness whose RELATED field's
# keyword mapping records NO target -- the sub-domain clause C1 (totality) is
# about, and the one the single FAIL_TO_PASS test exercises.
_F2P_GROUND = (
    '[{ isRelation := false,'
    ' decon := { path := "p0", args := [], kwargs := [("k", "v")] } },'
    ' { isRelation := true,'
    ' decon := { path := "p1", args := ["a"], kwargs := [("n", "m")] } }]'
)
_ADMISS_GROUND = (
    "  have _ground : problem_spec_relationAgnosticFields\n"
    f"      {_F2P_GROUND}\n"
    "      (implementation_relationAgnosticFields\n"
    f"        {_F2P_GROUND}) := by\n"
    "    unfold problem_spec_relationAgnosticFields"
    " implementation_relationAgnosticFields\n"
    "    decide\n"
    + _INTRO
)


# ===========================================================================
# POSITIVE CONTROLS (soundness) — expect "verify"
# ===========================================================================

# (pos-functional-form) Drop the imperative accumulation entirely: produce the
# result as a direct `map` over the fields. A much larger reshape than merely
# naming the result in a local, so a stronger over-fitting probe. Proof closes by
# `rfl` -- the impl is now definitionally the spec's right-hand side.
_POS_FUNCTIONAL_IMPL = (
    "def implementation_relationAgnosticFields\n"
    "    (fields : List FieldDef) : Option (List Decon) :=\n"
    "  some (fields.map (fun f => if f.isRelation then removeTarget f.decon else f.decon))\n"
)
_POS_FUNCTIONAL_PROOF = (
    "theorem correct_relationAgnosticFields :\n"
    "    ∀ (fields : List FieldDef),\n"
    "      problem_spec_relationAgnosticFields fields\n"
    "        (implementation_relationAgnosticFields fields) := by\n"
    "  intro fields\n"
    "  unfold problem_spec_relationAgnosticFields implementation_relationAgnosticFields\n"
    "  rfl\n"
)

# (pos-fork-reorder) The two arms of the fork are MUTUALLY EXCLUSIVE, so swapping
# them is a pure source reshape with identical behaviour. The proof is the frozen
# one with the loop lemma restated over the reshaped conditional and a case split
# on the guard supplied where the frozen `simp` had a syntactic match.
_POS_REORDER_FORK = (
    "    let d := if f.isRelation = false then f.decon else removeTarget f.decon\n"
)
_POS_REORDER_PROOF = (
    "/-- Helper: the accumulation, generalized over the accumulator, equals the\n"
    "prefix appended to the per-field transform of the remaining fields. -/\n"
    "theorem forIn_relationAgnosticFields (fields : List FieldDef) (acc : List Decon) :\n"
    "    Id.run (forIn fields acc (fun f r =>\n"
    "      (do pure PUnit.unit;\n"
    "          pure (ForInStep.yield\n"
    "            (r ++ [if f.isRelation = false then f.decon else removeTarget f.decon])))))\n"
    "      = acc ++ fields.map transformField := by\n"
    "  induction fields generalizing acc with\n"
    "  | nil => simp only [List.forIn_nil, List.map_nil, List.append_nil]; rfl\n"
    "  | cons a as ih =>\n"
    "    rw [List.forIn_cons]\n"
    "    simp only [Id.run, bind] at ih ⊢\n"
    "    rw [ih]\n"
    "    cases hb : a.isRelation <;>\n"
    "      simp [hb, List.map_cons, transformField, List.append_assoc]\n"
    "\n"
    "theorem correct_relationAgnosticFields :\n"
    "    ∀ (fields : List FieldDef),\n"
    "      problem_spec_relationAgnosticFields fields\n"
    "        (implementation_relationAgnosticFields fields) := by\n"
    "  intro fields\n"
    "  unfold problem_spec_relationAgnosticFields implementation_relationAgnosticFields\n"
    "  have h : (Id.run do\n"
    "      let r ← forIn fields ([] : List Decon) fun f r => do\n"
    "            pure PUnit.unit\n"
    "            pure (ForInStep.yield\n"
    "              (r ++ [if f.isRelation = false then f.decon else removeTarget f.decon]))\n"
    "      pure (some r))\n"
    "      = some (Id.run (forIn fields ([] : List Decon) fun f r => do\n"
    "            pure PUnit.unit\n"
    "            pure (ForInStep.yield\n"
    "              (r ++ [if f.isRelation = false then f.decon else removeTarget f.decon])))) := rfl\n"
    "  rw [h, forIn_relationAgnosticFields]\n"
    "  simp\n"
)

# (pos-guard-present) The PARTIAL-DOMAIN TRAP, kept as a positive control: remove
# the target entry only when the mapping actually records one, else carry the
# deconstruction over. Removing an absent entry is a no-op, so this is
# BEHAVIOURALLY IDENTICAL to gold on every input and MUST verify. The proof needs
# the `filter` no-op fact, which is established INLINE as a `have` inside the
# frozen loop lemma (adding a top-level helper lemma is not admissible).
_POS_GUARD_FORK = (
    "    let d := if f.isRelation then\n"
    "               (if f.decon.kwargs.any (fun kv => kv.1 == targetKey) then\n"
    "                  removeTarget f.decon\n"
    "                else f.decon)\n"
    "             else f.decon\n"
)
_POS_GUARD_COND = (
    "if f.isRelation = true then\n"
    "              (if f.decon.kwargs.any (fun kv => kv.1 == targetKey) = true then\n"
    "                 removeTarget f.decon else f.decon)\n"
    "            else f.decon"
)
_POS_GUARD_PROOF = (
    "/-- Helper: the accumulation, generalized over the accumulator, equals the\n"
    "prefix appended to the per-field transform of the remaining fields. -/\n"
    "theorem forIn_relationAgnosticFields (fields : List FieldDef) (acc : List Decon) :\n"
    "    Id.run (forIn fields acc (fun f r =>\n"
    "      (do pure PUnit.unit;\n"
    "          pure (ForInStep.yield\n"
    "            (r ++ [" + _POS_GUARD_COND + "])))))\n"
    "      = acc ++ fields.map transformField := by\n"
    "  have hkeep : ∀ (kw : List (String × String)),\n"
    "      kw.any (fun kv => kv.1 == targetKey) = false →\n"
    "      kw.filter (fun kv => kv.1 != targetKey) = kw := by\n"
    "    intro kw h\n"
    "    rw [List.filter_eq_self]\n"
    "    intro a ha\n"
    "    simp only [List.any_eq_false] at h\n"
    "    simpa using h a ha\n"
    "  induction fields generalizing acc with\n"
    "  | nil => simp only [List.forIn_nil, List.map_nil, List.append_nil]; rfl\n"
    "  | cons a as ih =>\n"
    "    rw [List.forIn_cons]\n"
    "    simp only [Id.run, bind] at ih ⊢\n"
    "    rw [ih]\n"
    "    have hstep : (if a.isRelation = true then\n"
    "        (if a.decon.kwargs.any (fun kv => kv.1 == targetKey) = true then\n"
    "           removeTarget a.decon else a.decon)\n"
    "      else a.decon) = transformField a := by\n"
    "      unfold transformField removeTarget\n"
    "      cases hb : a.isRelation\n"
    "      · simp [hb]\n"
    "      · cases ha : a.decon.kwargs.any (fun kv => kv.1 == targetKey)\n"
    "        · simp [hb, ha, hkeep _ ha]\n"
    "        · simp [hb, ha]\n"
    "    rw [hstep]\n"
    "    simp [List.map_cons, List.append_assoc]\n"
    "\n"
    "theorem correct_relationAgnosticFields :\n"
    "    ∀ (fields : List FieldDef),\n"
    "      problem_spec_relationAgnosticFields fields\n"
    "        (implementation_relationAgnosticFields fields) := by\n"
    "  intro fields\n"
    "  unfold problem_spec_relationAgnosticFields implementation_relationAgnosticFields\n"
    "  have h : (Id.run do\n"
    "      let r ← forIn fields ([] : List Decon) fun f r => do\n"
    "            pure PUnit.unit\n"
    "            pure (ForInStep.yield\n"
    "              (r ++ [" + _POS_GUARD_COND + "]))\n"
    "      pure (some r))\n"
    "      = some (Id.run (forIn fields ([] : List Decon) fun f r => do\n"
    "            pure PUnit.unit\n"
    "            pure (ForInStep.yield\n"
    "              (r ++ [" + _POS_GUARD_COND + "])))) := rfl\n"
    "  rw [h, forIn_relationAgnosticFields]\n"
    "  simp\n"
)


# ===========================================================================
# UNIQUENESS RIVALS — expect "reject". Each keeps the frozen proof body verbatim
# (a rival does not get to reprove; the witness is what attributes its rejection
# to the spec).
# ===========================================================================

# (absent-target-undefined — C1 TOTALITY) The pre-change shape: on a field that
# points at another model, produce a result only when its keyword mapping records
# a target; otherwise produce NO result at all.
_R_ABSENT = (
    "    if f.isRelation then\n"
    "      if f.decon.kwargs.any (fun kv => kv.1 == targetKey) then\n"
    "        acc := acc ++ [removeTarget f.decon]\n"
    "      else\n"
    "        return none\n"
    "    else\n"
    "      acc := acc ++ [f.decon]\n"
)

# (always-drop — C3, the unrelated arm) Remove the target entry from EVERY field,
# collapsing the fork.
_R_ALWAYS = "    let d := removeTarget f.decon\n"

# (keep-target — C2, the related arm) Never remove anything; carry every field
# over unchanged.
_R_KEEP = "    let d := f.decon\n"

# (drop-trailing-kwargs — C4 FRAME) Truncate the keyword mapping AT the target
# entry instead of removing just that entry, so every entry recorded after it is
# lost as well.
_R_TRUNCATE = (
    "    let d := if f.isRelation then\n"
    "               { f.decon with\n"
    "                 kwargs := f.decon.kwargs.takeWhile (fun kv => kv.1 != targetKey) }\n"
    "             else f.decon\n"
)

# (clear-args — C4 FRAME) Remove the target entry correctly, but discard the
# positional arguments while rebuilding the deconstruction.
_R_CLEAR_ARGS = (
    "    let d := if f.isRelation then\n"
    "               { path := f.decon.path, args := [],\n"
    "                 kwargs := f.decon.kwargs.filter (fun kv => kv.1 != targetKey) }\n"
    "             else f.decon\n"
)

# (blank-path — C4 FRAME) Remove the target entry correctly, but blank the import
# path while rebuilding the deconstruction.
_R_BLANK_PATH = (
    "    let d := if f.isRelation then\n"
    "               { path := \"\", args := f.decon.args,\n"
    "                 kwargs := f.decon.kwargs.filter (fun kv => kv.1 != targetKey) }\n"
    "             else f.decon\n"
)

# (reverse-order — C5 TRAVERSAL) Transform every field correctly but collect the
# results in the reverse of the visiting order.
_R_REVERSE = "    acc := [d] ++ acc\n"

# (skip-unrelated — C5 TRAVERSAL) Collect a result only for the fields that point
# at another model, so every other field is missing from the output entirely.
_R_SKIP = (
    "    if f.isRelation then\n"
    "      acc := acc ++ [removeTarget f.decon]\n"
)


# ===========================================================================
# Witnesses. Each negates the spec predicate at ONE concrete input; the carrier
# is transparent so `decide` settles it and no witness binds a hypothesis.
# Verified BOTH ways with scripts/lean_verify.sh (rival exit 0, gold exit 1).
# ===========================================================================

def _witness(field_lits: str) -> str:
    return (
        "example : ¬ problem_spec_relationAgnosticFields\n"
        f"    {field_lits}\n"
        "    (implementation_relationAgnosticFields\n"
        f"      {field_lits}) := by\n"
        "  unfold problem_spec_relationAgnosticFields"
        " implementation_relationAgnosticFields\n"
        "  decide\n"
    )


# One related field whose mapping records NO target -- the sub-domain C1 is about.
_W_ABSENT = _witness(
    '[{ isRelation := true,'
    ' decon := { path := "p", args := [], kwargs := [("x", "1")] } }]')

# One UNRELATED field whose mapping happens to carry the distinguished key: it
# must survive. The only witness holding `isRelation` at false on a singleton.
_W_ALWAYS = _witness(
    '[{ isRelation := false,'
    ' decon := { path := "p", args := [], kwargs := [("to", "T")] } }]')

# One related field that DOES record a target: it must be gone.
_W_KEEP = _witness(
    '[{ isRelation := true,'
    ' decon := { path := "p", args := [], kwargs := [("to", "T")] } }]')

# The target entry sits BETWEEN two others, so a truncating traversal loses the
# trailing one while a removing traversal does not. Positions the target
# mid-mapping, which no other witness does.
_W_TRUNCATE = _witness(
    '[{ isRelation := true,'
    ' decon := { path := "p", args := [],'
    ' kwargs := [("a", "1"), ("to", "T"), ("b", "2")] } }]')

# A related field with a positional argument and an EMPTY mapping: nothing to
# remove, so only the argument frame can differ.
_W_CLEAR_ARGS = _witness(
    '[{ isRelation := true,'
    ' decon := { path := "p", args := ["a1"], kwargs := [] } }]')

# A related field with a non-empty path, TWO positional arguments and a
# non-target entry: only the path frame can differ.
_W_BLANK_PATH = _witness(
    '[{ isRelation := true,'
    ' decon := { path := "q", args := ["a1", "a2"], kwargs := [("k", "v")] } }]')

# TWO fields, distinguishable and of MIXED relatedness, so order is observable
# (a palindromic or single-element input would not refute a reversal).
_W_REVERSE = _witness(
    '[{ isRelation := true,'
    ' decon := { path := "p1", args := ["z"], kwargs := [("to", "T")] } },'
    ' { isRelation := false,'
    ' decon := { path := "p2", args := [], kwargs := [("to", "K")] } }]')

# TWO fields, one related and one not, so a traversal that collects only the
# related ones returns a SHORTER list than the input.
_W_SKIP = _witness(
    '[{ isRelation := true,'
    ' decon := { path := "p1", args := [], kwargs := [("to", "T")] } },'
    ' { isRelation := false,'
    ' decon := { path := "p2", args := ["w"], kwargs := [("m", "9")] } }]')


SPEC_TESTS = [
    # ---------------- admissibility (must VERIFY) ----------------
    {
        "id": "admiss-absent-target-ground",
        "kind": "admissibility",
        "expect": "verify",
        "module": _swap(_BASE, _INTRO, _ADMISS_GROUND),
        "rationale": (
            "ADMISSIBILITY / PRECOND-TOO-STRONG, the lane the port had dropped as "
            "'vacuous because the obligation has no precondition hypothesis'. That "
            "reason does not hold: on a total carrier the analogue of an over-strong "
            "precondition is the obligation being UNSATISFIABLE at exactly an "
            "F2P-shaped input, and a `∀`-only statement does not rule that out — an "
            "inconsistent postcondition is unprovable at every point, so 'the theorem "
            "quantifies over everything' is not evidence that it is dischargeable "
            "anywhere. This case demonstrates satisfiability CONCRETELY: it discharges "
            "`problem_spec_relationAgnosticFields` at a two-field input of MIXED "
            "relatedness whose related field's keyword mapping records NO target — the "
            "shape the single FAIL_TO_PASS test exercises, and the sub-domain the whole "
            "totality clause C1 is about — by EVALUATION (`decide`) as a `have`, and "
            "only then closes the frozen obligation verbatim. So the spec is shown "
            "non-vacuous at the one input class that matters, rather than merely "
            "provable in general. Nothing is assumed: no new axiom, no new top-level "
            "lemma, `theorem correct_relationAgnosticFields` statement byte-identical, "
            "the ground instance is a `have` prepended to the existing tactic body. If "
            "this FAILS => the modeled behaviour is unsatisfiable at a normal F2P "
            "input, i.e. the spec is unmeetable exactly where the change is observed."
        ),
    },

    # ---------------- positive controls (must VERIFY) ----------------
    {
        "id": "pos-functional-form",
        "kind": "soundness",
        "expect": "verify",
        "module": _reprove(_swap(_BASE, _IMPL, _POS_FUNCTIONAL_IMPL),
                           _POS_FUNCTIONAL_PROOF),
        "rationale": (
            "SOUNDNESS: a structurally very different but behaviourally IDENTICAL "
            "implementation — the accumulating traversal is replaced by a direct "
            "elementwise map over the fields, so there is no mutable accumulator and "
            "no loop at all. Ports nagini's `pos-local-reshape` and strengthens it: "
            "instead of merely naming the result in a local, the whole imperative "
            "shape is discarded, which is a far stronger probe for a spec over-fit to "
            "one impl form. Every clause C1..C5 holds by construction and the proof "
            "closes by `rfl`. If this FAILS => SPEC-TOO-STRONG (the spec, or the "
            "obligation, is tied to the accumulation shape rather than to the "
            "behaviour)."
        ),
    },
    {
        "id": "pos-fork-reorder",
        "kind": "soundness",
        "expect": "verify",
        "module": _reprove(_swap(_BASE, _FORK, _POS_REORDER_FORK),
                           _POS_REORDER_PROOF),
        "rationale": (
            "SOUNDNESS, porting nagini's `pos-branch-reorder`: the two arms of the "
            "per-field fork are swapped in source order (test the unrelated case "
            "first). The arms are MUTUALLY EXCLUSIVE on the guard, so this is a pure "
            "source reshape with identical semantics on every input — C1..C5 hold "
            "exactly as for gold. The obligation is reproven for the reshaped "
            "conditional (statement byte-identical; the loop lemma is restated over "
            "the new conditional and the guard case-split supplied where the frozen "
            "script had a syntactic match). If this FAILS => SPEC-TOO-STRONG (the "
            "spec would be pinning the branch ORDER, which is not behaviour)."
        ),
    },
    {
        "id": "pos-guard-present",
        "kind": "soundness",
        "expect": "verify",
        "module": _reprove(_swap(_BASE, _FORK, _POS_GUARD_FORK), _POS_GUARD_PROOF),
        "rationale": (
            "SOUNDNESS — the PARTIAL-DOMAIN TRAP carried over from nagini's "
            "`pos-guard-present`, and the case most likely to be MISLABELLED as a "
            "rival. A related field's target entry is removed only when the mapping "
            "actually records one; otherwise the deconstruction is carried over as "
            "is. Because removing an absent entry is a no-op, this agrees with gold "
            "at EVERY input and MUST verify: it documents that the spec constrains "
            "the RESULT and not the mechanism by which the entry is removed, so it is "
            "the control that stops `absent-target-undefined` (below) from being read "
            "as 'the spec forbids testing for the entry'. If this FAILS => "
            "SPEC-TOO-STRONG. The proof establishes the filter-is-a-no-op fact inline "
            "as a `have` inside the loop lemma — no new top-level lemma, no assumed "
            "step."
        ),
    },

    # ---------------- uniqueness rivals (must be REJECTED) ----------------
    {
        "id": "absent-target-undefined",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _LOOP_BODY, _R_ABSENT),
        "refinement": (
            "This is the PRE-CHANGE behaviour, and it is the exact defect the report "
            "describes: a field that points at another model is normalized only when "
            "its deconstructed keyword mapping records a target, and otherwise the "
            "normalization does not produce a result at all. Its faithful real "
            "counterpart is the unchanged narrow removal, which is undefined on that "
            "sub-domain. A model can legitimately declare a related field that "
            "supplies its target itself and therefore omits it from its own "
            "deconstruction — and the single FAIL_TO_PASS test constructs precisely "
            "such a field and asserts the surrounding rename detection completes. So "
            "this rival's faithful patch is the pre-change source verbatim and does "
            "NOT resolve; a rival that VERIFIED here would be a genuine "
            "verify-does-not-imply-resolve break."
        ),
        "rationale": (
            "C1 TOTALITY. The clause demands `result = some (fields.map "
            "transformField)` for EVERY input, so a result that is not produced can "
            "never satisfy it. Rejection source: the postcondition equation, at any "
            "input containing a related field whose mapping records no target. The "
            "witness pins that sub-domain exactly — a single related field whose "
            "mapping holds one unrelated entry — which is a point NO other witness "
            "visits, and it is the point the paired `pos-guard-present` control shows "
            "a CORRECT impl handles. If it VERIFIES => SPEC-TOO-WEAK (the totality "
            "the change introduces is not being demanded)."
        ),
        "witness": _W_ABSENT,
    },
    {
        "id": "keep-target",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _FORK, _R_KEEP),
        "refinement": (
            "Carries every field over unchanged — the 'removal line is simply absent' "
            "rival. Its faithful real counterpart omits the normalization step "
            "entirely, so two related fields aimed at DIFFERENT targets no longer "
            "compare equal. The normalized lists are compared by VALUE by the sole "
            "consumer of this behaviour (it normalizes an added model's fields and a "
            "removed model's fields and tests the two for equality), so a rename of a "
            "model that is pointed at by a related field would stop being detected "
            "and the wrong migration would be produced. That breaks the "
            "renamed-model-with-relations tests in PASS_TO_PASS, so it does NOT "
            "resolve."
        ),
        "rationale": (
            "C2, the related arm of the fork. Rejection source: the equation's "
            "`transformField` on a field with `isRelation = true`, which must have its "
            "target entry removed. Witness: one related field whose mapping records a "
            "target — the rival returns it with the entry intact where the spec "
            "requires it gone. Held at `isRelation = true` against `always-drop`'s "
            "`false`, so the two together pin the fork in BOTH directions. If it "
            "VERIFIES => SPEC-TOO-WEAK (the related arm's removal is unpinned)."
        ),
        "witness": _W_KEEP,
    },
    {
        "id": "always-drop",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _FORK, _R_ALWAYS),
        "refinement": (
            "Removes the target entry from EVERY field, collapsing the fork. Its "
            "faithful real counterpart places the removal OUTSIDE the guard that tests "
            "whether the field points at another model, so an unrelated field's "
            "deconstructed keyword mapping is stripped too. An unrelated field can "
            "carry an entry under that same key — the key is an ordinary keyword name, "
            "not reserved — and the normalized lists are compared by VALUE for rename "
            "detection, so stripping it makes two unrelated fields that differ only in "
            "that keyword compare equal. Rename detection then misfires on models "
            "whose fields are not relations at all, breaking the deconstruction- "
            "equality expectations in PASS_TO_PASS. Does NOT resolve."
        ),
        "rationale": (
            "C3, the unrelated arm of the fork — the DUAL of `keep-target`. Rejection "
            "source: the equation's `transformField` on a field with `isRelation = "
            "false`, which must be carried over verbatim, distinguished entry "
            "included. Witness: a single UNRELATED field whose mapping carries the "
            "distinguished key — the one witness in the battery that holds "
            "`isRelation` at `false` on a singleton input, so without it a rival that "
            "mishandled ONLY the unrelated arm would verify unnoticed. If it VERIFIES "
            "=> SPEC-TOO-WEAK (the unrelated arm is unpinned)."
        ),
        "witness": _W_ALWAYS,
    },
    {
        "id": "drop-trailing-kwargs",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _FORK, _R_TRUNCATE),
        "refinement": (
            "Ports nagini's collateral-loss rival, re-expressed for this carrier: the "
            "keyword mapping is TRUNCATED at the target entry rather than having that "
            "entry removed, so every entry recorded after it is lost too. Its faithful "
            "real counterpart is a normalization that discards more of the "
            "deconstructed keyword mapping than the single target entry. Since the "
            "normalized lists are compared by VALUE, two related fields differing only "
            "in a discarded keyword would wrongly compare equal and a rename would be "
            "mis-detected, producing the wrong migration and breaking the "
            "relation-rename expectations in PASS_TO_PASS. Does NOT resolve."
        ),
        "rationale": (
            "C4 FRAME, the non-target keyword entries. Rejection source: the equation "
            "pins the ENTIRE resulting deconstruction, so `removeTarget`'s filter — "
            "which keeps every entry whose key differs from the distinguished one, "
            "wherever it sits — is what the rival's truncation violates. Witness: one "
            "related field whose mapping records an entry, then the target, then "
            "another entry; the rival loses the trailing one. This is the only witness "
            "that places the target MID-mapping, which is exactly the sub-domain the "
            "truncation is wrong on and where it differs from the correct filter "
            "(a rival truncating a target-last mapping would agree with gold). If it "
            "VERIFIES => SPEC-TOO-WEAK (collateral keyword loss is admitted)."
        ),
        "witness": _W_TRUNCATE,
    },
    {
        "id": "clear-args",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _FORK, _R_CLEAR_ARGS),
        "refinement": (
            "Removes the target entry correctly but discards the POSITIONAL ARGUMENTS "
            "while rebuilding a related field's deconstruction. Its faithful real "
            "counterpart rebuilds the deconstruction tuple in place of editing only "
            "its keyword component, losing the positional part. Because the sole "
            "consumer compares whole normalized deconstructions by VALUE, two related "
            "fields differing only in their positional arguments would compare equal "
            "and a rename would be mis-detected; and the comparison would also stop "
            "matching a genuinely renamed model whose fields do carry positional "
            "arguments. That breaks the rename detection PASS_TO_PASS tests, so it "
            "does NOT resolve."
        ),
        "rationale": (
            "C4 FRAME, the positional-argument component — this is where nagini's "
            "MANDATORY frame-mutation rival lands on this carrier. The fractional- "
            "permission MECHANISM does not port (Lean is referentially transparent), "
            "but the OBLIGATION does, and it is not vacuous: the deconstruction is an "
            "observable component of the result, so the spec's equation pins the "
            "components the normalization must not touch. Rejection source: that "
            "equation, via `removeTarget`'s structure-update form, which alters the "
            "keyword field ONLY. Witness: a related field with a positional argument "
            "and an EMPTY mapping — nothing to remove, so at THIS input the argument "
            "frame is the only thing that can differ, which is what isolates this "
            "clause from C1..C3 here. (Not a claim that no other rival is also wrong "
            "at this point: `absent-target-undefined` and `blank-path` are too. The "
            "attribution comes from this witness refuting THIS rival while holding of "
            "no correct impl.) If it "
            "VERIFIES => the frame is hollow and a rival may put anything in the "
            "untouched components."
        ),
        "witness": _W_CLEAR_ARGS,
    },
    {
        "id": "blank-path",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _FORK, _R_BLANK_PATH),
        "refinement": (
            "Removes the target entry correctly but blanks the IMPORT PATH while "
            "rebuilding a related field's deconstruction. Its faithful real "
            "counterpart loses the path component of the deconstruction tuple. The "
            "path is what identifies which field class was deconstructed, so with it "
            "blanked the by-VALUE comparison the consumer performs would treat "
            "structurally unrelated related fields as equal — every related field "
            "would compare equal to every other with the same arguments and keywords "
            "— and rename detection would fire on models that were not renamed at "
            "all, emitting wrong migrations. That breaks the rename PASS_TO_PASS "
            "tests, so it does NOT resolve."
        ),
        "rationale": (
            "C4 FRAME, the path component — a SECOND, independent frame component from "
            "`clear-args`, deliberately given its own witness rather than sharing "
            "one, because the two rivals agree with gold on different sub-domains "
            "(`clear-args` is correct on every field with no positional arguments; "
            "`blank-path` is correct on every field with an empty path). Rejection "
            "source: the equation, via the structure-update form that alters the "
            "keyword field only. Witness: a related field with a NON-empty path, TWO "
            "positional arguments and a non-target entry — the only witness varying "
            "both the path and an arguments list of length two, so the path binder "
            "dimension is genuinely moved rather than held fixed. If it VERIFIES => "
            "the frame leaves the path unconstrained."
        ),
        "witness": _W_BLANK_PATH,
    },
    {
        "id": "reverse-order",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _APPEND, _R_REVERSE),
        "refinement": (
            "Transforms every field correctly but collects the results in the reverse "
            "of the visiting order. Its faithful real counterpart prepends each "
            "normalized deconstruction to the accumulated list instead of appending "
            "it. The consumer compares two normalized lists by VALUE, and list "
            "equality is order-sensitive, so reversing one side while the visiting "
            "order is fixed upstream makes a genuinely renamed model's fields fail to "
            "compare equal whenever it has more than one field — rename detection "
            "silently stops working for essentially every real model. That breaks the "
            "rename PASS_TO_PASS tests, so it does NOT resolve."
        ),
        "rationale": (
            "C5 TRAVERSAL, the ORDER. No nagini counterpart: nagini's carrier was a "
            "single keyword mapping, so this bundle's list traversal is new attack "
            "surface. Rejection source: `fields.map transformField` fixes the output "
            "order to the input order elementwise. Witness: TWO distinguishable fields "
            "of MIXED relatedness — order is only observable at length >= 2 with "
            "distinct elements, so this witness is the first to move the list-LENGTH "
            "dimension of the `fields` binder, and mixing the guard values means the "
            "reversal cannot be masked by the elements happening to normalize alike. "
            "If it VERIFIES => SPEC-TOO-WEAK (the spec constrains the multiset of "
            "results, not the sequence)."
        ),
        "witness": _W_REVERSE,
    },
    {
        "id": "skip-unrelated",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _LOOP_BODY, _R_SKIP),
        "refinement": (
            "Collects a result only for the fields that point at another model, so "
            "every other field is absent from the output. Its faithful real "
            "counterpart moves the collection step INSIDE the guard that tests "
            "whether the field points at another model, so unrelated fields are never "
            "recorded. The consumer compares the normalized lists by VALUE, so two "
            "models with identical related fields but entirely different plain fields "
            "would compare equal and be reported as a rename — and the comparison "
            "would ignore plain-field differences altogether. That breaks the rename "
            "detection PASS_TO_PASS tests (which distinguish models by their plain "
            "fields), so it does NOT resolve."
        ),
        "rationale": (
            "C5 TRAVERSAL, the LENGTH / no-field-dropped half — independent of "
            "`reverse-order`, which permutes without losing anything. No nagini "
            "counterpart (nagini's carrier had no traversal). Rejection source: "
            "`fields.map transformField` has one output element per input field, so "
            "`List.length` of the result is pinned. Witness: TWO fields, one related "
            "and one not, so the rival returns a SHORTER list; distinct from "
            "`reverse-order`'s pair (different paths, arguments and keyword entries). "
            "The two rivals ARE each wrong at the other's point as well (measured), so "
            "the distinctness claimed here is of the INPUTS and the clauses, not of the "
            "refutations; each witness's attribution rests on refuting its own rival "
            "while holding of no correct impl. If it VERIFIES => "
            "SPEC-TOO-WEAK (the spec does not require every field to be represented)."
        ),
        "witness": _W_SKIP,
    },
]
