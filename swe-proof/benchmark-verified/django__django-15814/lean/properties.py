"""properties.py — G-PBT falsification battery for django__django-15814 (lean).

NOT a Lean file; a record of the adversarial cases the G-PBT gate executes and
stamps. Each SPEC case is a full ``Solution.lean`` variant that shares the
FROZEN spec byte-for-byte (region surgery: only text inside the ``-- impl-start``
/ ``-- impl-end`` region — and, where a case legitimately re-proves or adds a
ground instance, inside the ``-- proof-start`` / ``-- proof-end`` region — is
changed, so ``markers.same_spec`` holds and the ``theorem
correct_relationModelKeys`` STATEMENT stays byte-identical). ``expect="verify"``
passes iff (in scope AND the file elaborates with the obligation closed);
``expect="reject"`` passes iff (in scope AND it does NOT verify AND the case's
refutation ``witness`` holds of the rival while FAILING on the frozen solution).

This is a PORT of the nagini sibling's battery, re-expressed against this
backend's carrier — not a fresh invention and not a translation of its prose.

DEFENDED SURFACE (one total function over a list-of-steps domain):

  relationModelKeys (steps : List RelModel) : List Nat

    Each ``RelModel`` carries two identities: ``ident`` (the step's resolved
    model object, which may be an alias sharing another model's storage) and
    ``baseIdent`` (the base model that owns the shared storage / identifier
    column). ``baseOf m = m.baseIdent``; on a base model the two coincide.

    The postcondition ``problem_spec_relationModelKeys steps result`` has TWO
    independent top-level clauses:

      * LENGTH — ``result.length = steps.length``: exactly one key per step,
        no over- or under-production.
      * KEYING — ``∀ i m, steps[i]? = some m → result[i]? = some (baseOf m)``:
        the i-th key is the BASE identity of the i-th step (``baseIdent``),
        never the (possibly alias) resolved model ``ident``, and it is at the
        matching position (order preserved).

ADVERSARIAL READ of the nagini classes on this carrier (nagini modeled a
richer dict-of-dicts surface with a read-only fractional-permission input and a
closure/anti-scatter contract; here the modeled core is the per-step key list):

  * FRAME / PERMISSION MUTATION (nagini's mandatory #1 class) — VACUOUS. Lean is
    referentially transparent: ``steps`` is a plain immutable value, there is no
    half-permission to violate and no aliasing to exploit. The nagini
    frame-mutation rival (overwrite the read-only canonical map) has NO
    expressible instance here; no substitute is fabricated for it.

  * PRE-PATCH / RAW KEYING (nagini's ``weak-prepatch-raw-keying``) — APPLIES,
    and is the load-bearing rival. The pre-fix keyed each step under the
    resolved model AS-IS (``m.ident``) rather than its base model. On an alias
    step (``ident ≠ baseIdent``) it records the wrong identity; refuted by the
    KEYING clause exactly there — the F2P sub-domain.

  * OVER-FETCH (nagini's ``weak-over-fetch``) — APPLIES against the LENGTH
    clause. Nagini injected a spurious extra attribute into the bucket (breaking
    a closure clause); here the structural analogue is producing an extra key,
    which the LENGTH clause forbids.

  * ANTI-SCATTER / "paper over the symptom" (nagini's ``weak-scatter-injection``)
    — APPLIES against the LENGTH clause. Nagini kept the correct canonical bucket
    but ALSO scattered a raw-alias bucket; here the analogue keeps the correct
    base key but ALSO emits the raw alias identity as an extra key, so the key
    list is longer than the step list.

  * UNGROUNDED-ORACLE ECHO — VACUOUS. The postcondition is GROUNDED: every key
    is pinned to ``baseOf m = m.baseIdent``, a projection of the input carrier.
    The bundle declares no ``opaque``/``axiom`` (meta.json axioms == [],
    deep_model_references == []); there is no answer key a rival could echo. The
    honest cheapest-correct analogue is the POSITIVE CONTROL below.

WITNESSES. On a tactic-proof backend "did not verify" is the DEFAULT outcome of
reshaping an impl (the frozen script is tuned to the frozen form), so a
rejection alone attributes nothing to the spec. Every ``expect="reject"`` case
therefore carries a Lean snippet that assumes the spec predicate of the rival at
one CONCRETE input and derives ``False`` from the offending clause. The KEYING
rival is refuted at an alias step ``{ ident := 2, baseIdent := 1 }`` (its key
would be 2, but the spec demands 1); the two length rivals are refuted at a
concrete step list whose produced length disagrees with the step count. Each
witness was BUILT against its rival (elaborates) and against the frozen solution
(fails), so it is a real discriminator and not a tautology. All witness inputs
are ``decide``-able literals — no ``opaque`` term to condition on — so no
hypothesis binders are needed and none can be inconsistent.

BINDER COVERAGE. The modeled function has a SINGLE input binder, ``steps :
List RelModel``. It is varied across the reject witnesses at four distinct
input points: an alias-step singleton ``[{ident:=2, baseIdent:=1}]`` (KEYING),
base-step and alias-step singletons exercising the LENGTH clause at both a
non-alias base step ``[{ident:=1, baseIdent:=1}]`` and an alias step
``[{ident:=3, baseIdent:=1}]``, and a TWO-step traversal
``[{ident:=1, baseIdent:=1}, {ident:=2, baseIdent:=2}]`` exercising the
POSITIONAL half of the KEYING clause. So both top-level clauses are attacked,
both alias / non-alias regions of the carrier are exercised, and the binder is
varied in LENGTH as well as in element shape. The per-element sub-binders
``ident`` / ``baseIdent`` are moved relative to one another (alias where they
differ vs. base where they coincide), so no rival that mishandled only the alias
case would slip through.

Note on why the multi-step point is load-bearing (added by audit): the three
singleton-input rivals cannot attack index alignment at all, because at length 1
every permutation of the key list is the identity. A rival emitting the right
base keys as a multiset in the WRONG ORDER satisfies LENGTH exactly and is
refutable only at a traversal of two or more steps, so without that point the
spec's order-preservation guarantee was asserted in prose but never demonstrated.

AXIOM lane: EMPTY. meta.json axioms == [] and deep_model_references == []; the
keying decision is modeled deeply (``baseOf`` is a projection), so there is no
axiom-soundness / axiom-containment obligation for this gate to probe. The
nagini ``AXIOM_TESTS`` (the ``canonical_of == _meta.concrete_model`` A-reference
re-check) belongs to G-AX and is intentionally dropped here.
"""
from pathlib import Path

INSTANCE = "django__django-15814"

_BASE = (Path(__file__).parent / "Solution.lean").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# ---- region anchors (each unique inside Solution.lean; verified at load) ----
# The FULL impl-region body, and the FULL frozen tactic body, so every
# replacement lands entirely inside the region it means to edit.
_IMPL_GOLD = (
    "def implementation_relationModelKeys\n"
    "    (steps : List RelModel) : List Nat := Id.run do\n"
    "  let mut keys : List Nat := []\n"
    "  for m in steps do\n"
    "    let curModel := baseOf m\n"
    "    keys := keys ++ [curModel]\n"
    "  return keys"
)

_PROOF_BODY = (
    "  intro steps\n"
    "  -- Helper: the cleaned `forIn` loop, generalized over the accumulator, equals\n"
    "  -- the prefix accumulator appended with `steps.map baseOf` (Route B).\n"
    "  have hkey : ∀ (init : List Nat),\n"
    "      Id.run (forIn steps init\n"
    "        (fun m keys => (.yield (keys ++ [baseOf m]) : ForInStep (List Nat))))\n"
    "        = init ++ steps.map baseOf := by\n"
    "    intro init\n"
    "    induction steps generalizing init with\n"
    "    | nil => simp only [List.forIn_nil, Id.run, List.map_nil, List.append_nil]; rfl\n"
    "    | cons a as ih =>\n"
    "      rw [List.forIn_cons]\n"
    "      simp only [Id.run, bind] at ih ⊢\n"
    "      rw [ih (init ++ [baseOf a])]\n"
    "      simp [List.append_assoc]\n"
    "  -- Bridge the desugared loop body to the cleaned form and discharge the impl.\n"
    "  have himpl : implementation_relationModelKeys steps = steps.map baseOf := by\n"
    "    show Id.run (forIn steps []\n"
    "        (fun m keys => (.yield (keys ++ [baseOf m]) : ForInStep (List Nat)))) = _\n"
    "    rw [hkey []]\n"
    "    simp\n"
    "  refine ⟨?_, ?_⟩\n"
    "  · rw [himpl]; simp\n"
    "  · intro i m hi\n"
    "    rw [himpl, List.getElem?_map, hi]\n"
    "    rfl"
)

# sanity: the frozen anchors are present exactly once
assert _BASE.count(_IMPL_GOLD) == 1, "impl region drifted; update _IMPL_GOLD"
assert _BASE.count(_PROOF_BODY) == 1, "proof region drifted; update _PROOF_BODY"


def _impl(body):
    """Full Solution.lean variant with the gold impl body replaced."""
    return _swap(_BASE, _IMPL_GOLD, body)


# ---------------------------------------------------------------------------
# Positive-control impl + its re-proof (functional `map` form).
# ---------------------------------------------------------------------------
_POS_IMPL = (
    "def implementation_relationModelKeys\n"
    "    (steps : List RelModel) : List Nat :=\n"
    "  steps.map baseOf"
)
_POS_PROOF = (
    "  intro steps\n"
    "  refine ⟨?_, ?_⟩\n"
    "  · simp [implementation_relationModelKeys]\n"
    "  · intro i m hi\n"
    "    simp only [implementation_relationModelKeys, List.getElem?_map, hi]\n"
    "    rfl"
)

# Admissibility: a ground instance at an F2P-shaped alias step, proved inside the
# frozen tactic body (which is otherwise carried verbatim). No new declaration.
_ADM_GROUND = (
    "  have _ground : problem_spec_relationModelKeys\n"
    "      [{ ident := 2, baseIdent := 1 }] (implementation_relationModelKeys [{ ident := 2, baseIdent := 1 }]) := by\n"
    "    have himpl : implementation_relationModelKeys [{ ident := 2, baseIdent := 1 }] = [1] := by rfl\n"
    "    rw [himpl]\n"
    "    refine ⟨by decide, ?_⟩\n"
    "    intro i m hi\n"
    "    rcases i with _ | i\n"
    "    · simp only [List.getElem?_cons_zero, Option.some.injEq] at hi\n"
    "      subst hi\n"
    "      rfl\n"
    "    · simp at hi\n"
    + _PROOF_BODY
)

# ---------------------------------------------------------------------------
# Rival impl bodies (each a full impl region; only the impl changes, so the spec
# and the theorem STATEMENT stay byte-identical).
# ---------------------------------------------------------------------------

# PRE-PATCH / RAW KEYING: key each step under the resolved model AS-IS
# (`m.ident`) instead of its base model (`baseOf m`). Wrong on alias steps.
_RAW_KEYING = _IMPL_GOLD.replace(
    "    let curModel := baseOf m\n", "    let curModel := m.ident\n")

# OVER-FETCH: correct base key per step, but ALSO append a spurious extra key,
# so the key list is one longer than the step list.
_OVER_FETCH = _IMPL_GOLD.replace(
    "  return keys", "  keys := keys ++ [999]\n  return keys")

# ANTI-SCATTER / "paper over the symptom": emit the correct base key AND ALSO
# the raw alias identity `m.ident` as an extra key for every step, doubling the
# key list length.
_SCATTER = _IMPL_GOLD.replace(
    "    keys := keys ++ [curModel]\n",
    "    keys := keys ++ [curModel]\n    keys := keys ++ [m.ident]\n")

# ORDER / TRAVERSAL-POSITION: key every step under the correct base model and
# produce exactly one key per step (so BOTH the LENGTH clause and the per-step
# key VALUES as a multiset are satisfied), but emit them in reverse traversal
# order. This attacks the positional half of the KEYING clause, which the three
# rivals above cannot reach: each of them is refuted at a SINGLETON step list,
# where position is trivial and reversal is the identity.
_REVERSED = (
    "def implementation_relationModelKeys\n"
    "    (steps : List RelModel) : List Nat :=\n"
    "  (steps.map baseOf).reverse"
)


SPEC_TESTS = [
    # =====================================================================
    # POSITIVE CONTROL (soundness) — a structurally different but CORRECT impl
    # (a direct `steps.map baseOf`, no `Id.run do` / `let mut` / `for`) that MUST
    # verify. If a faithful correct impl cannot satisfy the frozen obligation the
    # spec is SPEC-TOO-STRONG. The theorem STATEMENT is byte-identical; the tactic
    # body is re-proved for the new shape (the frozen bridge/`forIn` induction is
    # tuned to the loop form). No helper lemma, axiom, or assumption token added.
    # =====================================================================
    {
        "id": "pos-functional-map",
        "kind": "soundness",
        "expect": "verify",
        "module": _swap(_impl(_POS_IMPL), _PROOF_BODY, _POS_PROOF),
        "rationale": (
            "a correct reshape that drops the mutable-accumulator loop and spells "
            "the per-step key computation as one functional expression "
            "(`steps.map baseOf`) must satisfy BOTH clauses — length "
            "(`(steps.map baseOf).length = steps.length`) and keying "
            "(`(steps.map baseOf)[i]? = some (baseOf m)` when `steps[i]? = some m`) "
            "— which close by `simp`/`List.getElem?_map` + `rfl`. If it cannot, the "
            "spec is over-fit to the loop FORM => SPEC-TOO-STRONG. No new "
            "declaration, axiom, or assumption token."
        ),
    },

    # =====================================================================
    # ADMISSIBILITY — confirms the obligation is SATISFIABLE (non-vacuous) at the
    # normal F2P-shaped input (an alias step whose base identity differs from its
    # resolved identity), rather than only provable in the abstract. The frozen
    # theorem carries NO precondition hypothesis (the behavior is total, `∀`
    # unguarded), so nagini's precondition-admission probe has no binder to attack;
    # the honest analogue discharges the spec predicate at the F2P ground input
    # inside the proof region, alongside the frozen obligation.
    # =====================================================================
    {
        "id": "admiss-alias-step-ground",
        "kind": "admissibility",
        "expect": "verify",
        "module": _swap(_BASE, _PROOF_BODY, _ADM_GROUND),
        "rationale": (
            "the obligation is discharged at the F2P ground input — a single alias "
            "step `{ ident := 2, baseIdent := 1 }` (resolved identity 2, base "
            "identity 1, the proxy/concrete split the F2P exercises) — where the "
            "spec requires the produced key be the BASE identity `1` (length 1, "
            "key[0] = 1), proved by reducing the impl to `[1]` and casing on the "
            "index; then the frozen obligation is closed verbatim. Verifies (else "
            "the spec is unsatisfiable at the normal alias input, the analogue of "
            "PRECOND-TOO-STRONG). Nothing is assumed: the theorem STATEMENT is "
            "byte-identical, the ground instance is a `have` inside the existing "
            "tactic body, no new declaration/axiom/`sorry`."
        ),
    },

    # =====================================================================
    # UNIQUENESS / SPEC-TOO-WEAK rivals — wrong impls sharing the frozen spec that
    # MUST be rejected. Each carries (a) the refinement argument that its faithful
    # real patch would NOT resolve the F2P, so a verifying rival would be a true
    # verify-does-not-imply-resolve break, and (b) a refutation witness pinning the
    # violation at one concrete input.
    # =====================================================================
    {
        "id": "weak-prepatch-raw-keying",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(_RAW_KEYING),
        "refinement": (
            "this is the pre-fix behavior: each step's identifier requirement is "
            "keyed under the resolved model AS-IS rather than the base model whose "
            "storage it shares. Its faithful real patch is exactly the unfixed "
            "code, which on the F2P scenario (a relation resolving to an alias "
            "model sharing a base model's identifier column) keys the requirement "
            "under the alias; the base model's identifier column is then absent "
            "from the load plan and the downstream row assembly cannot locate it. "
            "That is precisely the F2P failure, so this rival does NOT resolve."
        ),
        "rationale": (
            "REJECT from the KEYING clause `∀ i m, steps[i]? = some m → result[i]? "
            "= some (baseOf m)`: at the single alias step `{ ident := 2, baseIdent "
            ":= 1 }` the base identity is `1`, so the spec demands key `1`, but the "
            "rival records the resolved identity `2`. Refuted on an alias step "
            "(`ident ≠ baseIdent`) — the discriminating sub-domain. If it verified "
            "=> SPEC-TOO-WEAK (the base-keying fix unenforced)."
        ),
        "witness": (
            "-- Refuted on an alias step: the resolved identity (2) differs from the\n"
            "-- base identity (1) that owns the shared storage, so the produced key\n"
            "-- must be the base identity, not the alias.\n"
            "example : ¬ problem_spec_relationModelKeys\n"
            "    [{ ident := 2, baseIdent := 1 }]\n"
            "    (implementation_relationModelKeys [{ ident := 2, baseIdent := 1 }]) := by\n"
            "  intro h\n"
            "  have hkey := h.2 0 { ident := 2, baseIdent := 1 } (by rfl)\n"
            "  simp [implementation_relationModelKeys, baseOf] at hkey\n"
        ),
    },
    {
        "id": "weak-over-fetch-extra-key",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(_OVER_FETCH),
        "refinement": (
            "producing an extra key beyond the traversed steps corresponds to "
            "registering a load requirement for a model the query never reaches. "
            "A faithful patch that recorded an unrelated model's identifier "
            "requirement would over-fetch columns the fix does not select and "
            "shift the positional per-model column lists the downstream loader "
            "relies on, so the select_related().only() path does not reconstruct "
            "the object as expected. It does NOT resolve."
        ),
        "rationale": (
            "REJECT from the LENGTH clause `result.length = steps.length`: the "
            "rival appends a spurious extra key, so for a single-step (base) input "
            "the result has length 2 while the step list has length 1. Refuted at "
            "a non-alias base step `{ ident := 1, baseIdent := 1 }`, exercising the "
            "carrier where resolved and base identities coincide — a distinct "
            "sub-domain from the keying rival. If it verified => SPEC-TOO-WEAK "
            "(the one-key-per-step guarantee hollow)."
        ),
        "witness": (
            "-- Refuted on a base (non-alias) step: exactly one key must be produced\n"
            "-- per step, but an over-fetching impl emits an extra key, so the\n"
            "-- length no longer matches the step count.\n"
            "example : ¬ problem_spec_relationModelKeys\n"
            "    [{ ident := 1, baseIdent := 1 }]\n"
            "    (implementation_relationModelKeys [{ ident := 1, baseIdent := 1 }]) := by\n"
            "  intro h\n"
            "  have hlen := h.1\n"
            "  simp [implementation_relationModelKeys] at hlen\n"
        ),
    },
    {
        "id": "weak-scatter-raw-alias-key",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(_SCATTER),
        "refinement": (
            "this is the 'paper over the symptom' rival: it records the correct "
            "base key for each step (so the immediate lookup might not fail) yet "
            "ALSO emits the raw alias identity as a second key. A faithful patch "
            "that registered the requirement under BOTH the base and the raw alias "
            "identity (rather than moving it cleanly to the base) would report a "
            "requirement for a model identity the loader does not expect as a key, "
            "diverging from the single-key-per-step keying the downstream consumer "
            "relies on. It does NOT faithfully implement the fix — verify-not-resolve."
        ),
        "rationale": (
            "REJECT from the LENGTH clause `result.length = steps.length`: the "
            "rival emits two keys per step (the base key and the raw alias key), so "
            "for a single alias step the result has length 2 while the step list "
            "has length 1. Refuted at an alias step `{ ident := 3, baseIdent := 1 }` "
            "(a third distinct input point, alias identity 3), so the reject lane "
            "does not pin the carrier to one shape. If it verified => SPEC-TOO-WEAK "
            "(provenance / single-key keying unenforced)."
        ),
        "witness": (
            "-- Refuted on an alias step: keeping the correct base key while ALSO\n"
            "-- scattering the raw alias identity as a second key doubles the key\n"
            "-- list, so its length no longer matches the step count.\n"
            "example : ¬ problem_spec_relationModelKeys\n"
            "    [{ ident := 3, baseIdent := 1 }]\n"
            "    (implementation_relationModelKeys [{ ident := 3, baseIdent := 1 }]) := by\n"
            "  intro h\n"
            "  have hlen := h.1\n"
            "  simp [implementation_relationModelKeys] at hlen\n"
        ),
    },
    # =====================================================================
    # ORDER / TRAVERSAL POSITION. Added by audit: the three rivals above are each
    # refuted at a SINGLETON step list, where list position is trivial (and
    # reversal is the identity), so nothing in the battery demonstrated the
    # POSITIONAL half of the KEYING clause — `result[i]? = some (baseOf m)` at the
    # MATCHING index i — even though the frozen spec pins it and the docstring
    # claims order preservation. This rival satisfies the LENGTH clause exactly
    # and produces precisely the right multiset of base keys, so it can only be
    # rejected by the index alignment. It is also the first reject case stated at
    # a MULTI-step traversal (two steps), so the `steps` binder is varied in
    # LENGTH and not only in the alias/base shape of one element.
    # =====================================================================
    {
        "id": "weak-reversed-traversal-order",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(_REVERSED),
        "refinement": (
            "the keys are produced one per relation step, in traversal order, and "
            "the downstream consumer reads them positionally against the chain it "
            "walked. A faithful patch that accumulated the per-step requirements "
            "onto the front of the list (or walked the relation chain from the far "
            "end inward) would key each step under the right base model yet report "
            "the requirements against the wrong steps of the chain whenever a query "
            "traverses more than one relation, so the load plan attaches each "
            "model's identifier column to a different model than the one that "
            "needs it. On a single-relation query it is indistinguishable from the "
            "fix, which is why it must be pinned at a two-step traversal; it does "
            "NOT resolve the multi-relation behavior the fix is responsible for."
        ),
        "rationale": (
            "REJECT from the POSITIONAL half of the KEYING clause `∀ i m, steps[i]? "
            "= some m → result[i]? = some (baseOf m)`. This rival is deliberately "
            "correct on both weaker readings: it emits exactly one key per step "
            "(LENGTH holds: `((steps.map baseOf).reverse).length = steps.length`) "
            "and its keys are exactly the right base identities as a MULTISET — only "
            "the index alignment is wrong. At the two-step input `[{ident:=1, "
            "baseIdent:=1}, {ident:=2, baseIdent:=2}]` the spec demands "
            "`result[0]? = some 1`, but the reversed list yields `some 2`. If it "
            "verified => SPEC-TOO-WEAK (the in-traversal-order guarantee hollow, "
            "leaving the spec satisfied by any permutation of the right keys)."
        ),
        "witness": (
            "-- Refuted at a MULTI-step traversal, where position is observable: the\n"
            "-- rival produces the correct base keys in the wrong order, so the key at\n"
            "-- index 0 belongs to the last step rather than the first.\n"
            "example : ¬ problem_spec_relationModelKeys\n"
            "    [{ ident := 1, baseIdent := 1 }, { ident := 2, baseIdent := 2 }]\n"
            "    (implementation_relationModelKeys\n"
            "      [{ ident := 1, baseIdent := 1 }, { ident := 2, baseIdent := 2 }]) := by\n"
            "  intro h\n"
            "  have hkey := h.2 0 { ident := 1, baseIdent := 1 } (by rfl)\n"
            "  simp [implementation_relationModelKeys, baseOf] at hkey\n"
        ),
    },
]


# No consumed axioms and no deep-model references: the base-keying decision is
# modeled deeply (`baseOf` is a projection of the input), so there is no in-model
# axiom obligation for the PBT axiom lane to re-discharge here. (The nagini
# AXIOM_TESTS re-check of `canonical_of == _meta.concrete_model` belongs to G-AX.)
AXIOM_TESTS = []
