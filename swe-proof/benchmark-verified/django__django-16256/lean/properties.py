"""properties.py — G-PBT falsification battery for django__django-16256 (lean).

NOT a Lean file; a record of adversarial cases the G-PBT gate executes. Each
SPEC case is a full ``Solution.lean`` variant that shares the FROZEN spec
byte-for-byte (region surgery: only text inside the ``-- impl-start`` /
``-- impl-end`` region — and, for a case that legitimately re-proves, inside the
``-- proof-start`` / ``-- proof-end`` region — is changed, so ``markers.same_spec``
holds and the single ``theorem correct_scopedOp`` STATEMENT stays byte-identical).
``expect="verify"`` passes iff (in scope AND the file elaborates with the
obligation closed); ``expect="reject"`` passes iff (in scope AND it does NOT
verify AND the case's refutation ``witness`` holds of the rival while FAILING on
the frozen solution).

PORT NOTE. This is a PORT of the nagini falsification battery (see
``../nagini/properties.py``) onto this backend's carrier. The nagini bundle
contracts SIX functions in three operation families (``create`` /
``get_or_create`` / ``update_or_create`` and their deferred ``a*`` forms), with
the observable effect modeled as a fractional-permission list APPEND on a related
set and the async forms delegating to their same-named immediate form. This Lean
bundle models only the purely-functional core the three ops share: the
scope-binding MERGE that the fix routes each async method through. It is one
total function ``scopedOp`` over the observable inputs (the scope bindings, the
caller kwargs) returning the effective argument map, with a two-clause
postcondition. Most nagini cases therefore carry over as attacks on ONE of the
two clauses of the single modeled obligation; the mapping of each nagini case to
its Lean counterpart (or its principled omission) is in the module ``assessment``
submitted to the gate.

DEFENDED SURFACE (one modeled behavior). ``implementation_scopedOp bindings
kwargs`` folds each scope binding into the caller kwargs (replace-first-else-
append), then hands the effective map to the underlying data op. The
postcondition ``problem_spec_scopedOp`` pins that map with two independent
top-level clauses, selected by which input key is probed:

  * CLAUSE 1 — bound keys forced: ``∀ b ∈ bindings, result.lookup b.1 = some
    b.2``. Every scope key resolves to ITS scope value. This is the CHANGED
    clause: the pre-fix async method bypassed the scoped collection and ran the
    bare data op on the caller kwargs, so the scope bindings were never merged in
    (``result = kwargs``), leaving every scope key at whatever the caller
    supplied (typically unset).
  * CLAUSE 2 — frame: ``∀ k, (∀ b ∈ bindings, b.1 ≠ k) → result.lookup k =
    kwargs.lookup k``. Every key NOT in the scope is left exactly as the caller
    supplied it — no caller argument dropped, no spurious key introduced.

The BEHAVIOURAL DISCRIMINATOR (the fix): merge the scope bindings into the
caller's argument map before the data op runs. The pre-fix code never merged
them; the no-merge rival below IS that pre-fix behavior, caught by clause 1.

ADVERSARIAL READ of the nagini case classes on this carrier:

  * FRAME / PERMISSION MUTATION — VACUOUS. Lean is referentially transparent: an
    input carries no heap permission, there is no read-only half-permission to
    overwrite and no aliasing to exploit. The nagini full-permission note and its
    spurious-mutation concern re-express here NOT as a permission attack but as
    clause 2 (the frame): a rival that drops a caller key or introduces an extra
    key violates it. Two reject cases below exercise exactly that, so the
    "spurious mutation" concern is defended by an ordinary functional clause; no
    permission-specific substitute is fabricated.

  * DIVERGENCE / NON-TERMINATION — VACUOUS on lean. The nagini vacuity rival
    (case 8, ``weak-acreate-diverge``: an ``Invariant(True)`` loop that verifies
    under partial correctness while the awaiting F2P hangs) has no expressible
    instance here: ``implementation_scopedOp`` is a TOTAL Lean ``def``, so a
    diverging implementation cannot be written at all. (On velvet under
    ``partial`` termination semantics this would be a KNOWN SPEC HOLE, not a
    vacuous class — see ``the corpus-wide termination-semantics finding`` — but that disposition is
    velvet-specific; on lean the class is genuinely vacuous.) Not ported; no
    witness exists for a rival that cannot be written.

  * UNGROUNDED-ORACLE ECHO — VACUOUS. The postcondition is GROUNDED: ``result``
    is pinned by structural predicates over the actual input carrier
    (``.lookup`` on the bindings and kwargs), not equated to an opaque answer
    key. There is no oracle an impl could echo; no ``opaque`` callee appears
    (the merge is modeled deeply as ``kwUpsert``). In its place the battery
    carries honest cheapest-implementation POSITIVE CONTROLS that must verify.

PER-CASE MAP OF THE DROPPED NAGINI CASES (attack F, one verdict each). The
nagini battery has 8 cases; this carrier models ONE total function, so the
mapping is many-to-one rather than case-to-case:

  1. ``pos-control-reorder-goc`` — PORTED, twice. The branch reorder has no
     analogue (there is no branch), so the "structurally different but correct"
     role is carried by ``pos-control-foldl-form`` and, load-bearingly, by
     ``pos-control-append-form`` (observably distinct output list).
  2. ``admiss-acreate-fresh-accessor`` — PORTED as
     ``admiss-ground-merge-instance``. The nagini version re-seats a fresh
     accessor to establish a heap precondition; here the only precondition is
     ``Nodup``, discharged by ``decide`` at the ground F2P-shaped input.
  3. ``weak-acreate-no-attach`` and 4. ``weak-aget-or-create-no-attach`` —
     COLLAPSE onto ``weak-no-merge``. Both nagini cases are the same defect (the
     deferred form runs a non-scoping op) at two different operation families;
     this bundle models the shared merge core once, so the two are ONE rival
     here. Not a dropped attack: the distinction between the ``create`` and
     ``get_or_create`` families is a property of the unmodeled data op, which is
     behavior-identical across the fix.
  5. ``weak-goc-always-attach-located`` — INEXPRESSIBLE, and demonstrated so.
     It attacks the ``exists`` branch guard of the locate-or-produce family
     (attach on the located branch, where the set must stay unchanged). The
     modeled function has no ``exists`` input and no branch: the merge is
     unconditional on every operation family, so there is no located sub-domain
     to be wrong on. The clause it violates
     (``Implies(exists, members == Old(members))``) has no counterpart in
     ``problem_spec_scopedOp``. Expressing it would require adding a branch input
     to the frozen spec — outside this lane.
  6. ``weak-goc-flip-created-flag`` — INEXPRESSIBLE for the same structural
     reason: the ``created`` flag is a return component of the locate-or-produce
     op, and this bundle's result is the effective argument MAP, which has no
     flag component. The value-pin ATTACK CLASS it represents is nonetheless
     ported, at the only value this carrier exposes: ``weak-wrong-value``
     perturbs the bound value, so "delivers the right shape, wrong value" is
     defended.
  7. ``weak-acreate-double-attach`` — PORTED as ``weak-spurious-key`` (see the
     FRAME note above): the referentially-transparent analogue of an
     over-extended related set is an extra key in the effective map.
  8. ``weak-acreate-diverge`` — VACUOUS on lean, see the DIVERGENCE note below.

  Two rivals in this battery have NO nagini ancestor and were added because the
  carrier exposes a distinction nagini's did not: ``weak-partial-merge``
  (traversal completeness over a multi-binding scope, which the generic
  operation genuinely has) and ``weak-caller-wins-override`` (the binding must
  OVERRIDE a caller-supplied value for the same key — the sub-domain where the
  frame clause does not apply).

  * VALUE-PIN / PARTIAL-DOMAIN — APPLIES. Rivals that deliver the map but bind a
    scope key to the wrong value, merge only part of the bindings, drop a caller
    key, or introduce a spurious key: each correct on part of the domain but
    wrong where a clause bites.

WITNESSES. On a tactic-proof backend "did not verify" is the DEFAULT outcome of
reshaping an implementation — the frozen proof is tuned to the frozen ``for``/
``kwUpsert`` form — so a rejection alone attributes nothing to the spec. Every
``expect="reject"`` case therefore carries a Lean snippet that instantiates the
frozen spec predicate at one CONCRETE input, extracts the relevant clause
(``h.1``/``h.2``), and derives ``False`` by evaluation. Each was built and run
BOTH ways with ``scripts/lean_verify.sh``: it ELABORATES against the rival
(exit 0) and FAILS on the frozen solution (exit 1), so it discriminates rather
than asserting a tautology. All witness inputs are concrete literal
``List (String × Int)`` values — fully decidable — so no hypothesis about an
opaque term is needed and the ``witness-inconsistent`` / carrier-conditioning
machinery does not apply here.

Because every input is a literal, each witness closes by ``revert``+``decide``,
and the gold-side build is required to fail with ``decide`` REPORTING a verdict
(``Tactic `decide` proved that the proposition ... is false``) rather than with a
bare ``unsolved goals``. The difference is evidentiary, not stylistic: a
``decide`` that reports means the kernel EVALUATED the claim and found the frozen
solution satisfies it, whereas an unsolved goal is consistent with a tactic that
merely failed to make progress — the same exit code carrying much less
information. Two witnesses here originally closed by ``simp [List.lookup]``,
whose gold-side goal stalled at an unreduced ``pure (kwUpsert ...)``; they were
re-cast into the ``decide`` form so that all six gold-side failures are reported
refutations.

BINDER / POINT SPREAD. The frozen obligation has two input binders, ``bindings``
and ``kwargs``. The reject witnesses move both rather than fixing them at one
convenient point: ``bindings`` ranges over length-1 (``[("f",1)]``,
``[("ct",7)]``) and length-2 (``[("f",1),("g",2)]``); ``kwargs`` ranges over
empty ``[]``, a disjoint caller key ``[("g",5)]`` / ``[("q",4)]``, and a caller
key that COLLIDES with a scope key (``[("ct",9)]`` against binding ``ct↦7``).
Clause 1 is attacked at a scope key present at the head of ``bindings``, at a
scope key in the TAIL that a first-only merge misses, at the VALUE component,
and at the OVERRIDE point where the caller already supplied the scope key.
Clause 2 is attacked both by a rival that drops the caller key and by one that
adds a spurious key. No two rivals share a refutation point; the six reject
witnesses probe six distinct inputs.

The override point is called out separately because it is the one sub-domain
where the two clauses do not merely partition the key space: on a collision the
frame clause does NOT apply (the key IS a scope key), so clause 1 alone has to
do the work of forcing the binding to WIN over the caller's value. A battery
whose every witness kept the two key sets disjoint would never demonstrate that,
and the ``kwUpsert``-vs-append distinction (replace-first versus merely
appending, which differ only when the key is already present) would go
unattacked. ``weak-caller-wins-override`` is that witness.

WITNESS FORM. Each reject witness closes by ``revert``+``decide`` rather than by
``simp``. All inputs are concrete literals, so ``decide`` evaluates the claim and
its gold-side failure is a REPORTED verdict (``decide`` proved that the
proposition ... is false) rather than a bare unsolved goal — i.e. the frozen
solution demonstrably SATISFIES the refuted claim, instead of the tactic merely
failing to derive ``False`` from it. That distinction is the whole evidentiary
content of the gold-side build, so it is spelled the decisive way on purpose.

AXIOM lane: EMPTY here. The bundle consumes no ``axiom`` and declares no
``opaque`` (the merge is modeled deeply as ``kwUpsert``, an R leg validated by
G-CONF). The axiom lane belongs to G-AX; this gate ignores it, and the nagini
``AXIOM_TESTS`` (also empty there) are dropped.
"""
from pathlib import Path

INSTANCE = "django__django-16256"

_BASE = (Path(__file__).parent / "Solution.lean").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# ---- region anchors (each unique inside Solution.lean; verified at load) ----
# Every anchor lies ENTIRELY inside the impl region (or, for the positive that
# re-proves its helper, inside the proof region) so same_spec stays
# byte-identical and the `theorem correct_scopedOp` STATEMENT is untouched.

# The full impl definition (header + body). Swapped whole for the foldl-form
# positive control, whose `impl_eq_foldl` then closes by `rfl`.
_IMPL_FULL = (
    "def implementation_scopedOp\n"
    "    (bindings kwargs : List (String × Int)) : List (String × Int) := Id.run do\n"
    "  let mut out := kwargs\n"
    "  for b in bindings do\n"
    "    out := kwUpsert out b.1 b.2\n"
    "  return out\n"
)

# The impl body alone (the mutable-fold loop). Swapped by the reject rivals so
# only the loop shape changes — the `def` header and signature are preserved.
_IMPL_BODY = (
    "  let mut out := kwargs\n"
    "  for b in bindings do\n"
    "    out := kwUpsert out b.1 b.2\n"
    "  return out\n"
)

# The frozen `impl_eq_foldl` bridging lemma (proof region). For the foldl-form
# positive the impl IS the fold, so this lemma collapses to `rfl`.
_IEF_FROZEN = (
    "theorem impl_eq_foldl (bindings kwargs) :\n"
    "    implementation_scopedOp bindings kwargs\n"
    "      = bindings.foldl (fun acc b => kwUpsert acc b.1 b.2) kwargs := by\n"
    "  induction bindings generalizing kwargs with\n"
    "  | nil => rfl\n"
    "  | cons a as ih =>\n"
    "    unfold implementation_scopedOp\n"
    "    simp only [List.forIn_cons, List.foldl_cons, Id.run, bind, pure]\n"
    "    have := ih (kwUpsert kwargs a.1 a.2)\n"
    "    unfold implementation_scopedOp at this\n"
    "    simp only [Id.run, bind, pure] at this\n"
    "    exact this\n"
)

# Head of the frozen `correct_scopedOp` proof body (proof region). The
# admissibility case prepends a ground `have` before it, leaving the frozen
# closing tactics intact.
_PROOF_HEAD = (
    "  intro bindings kwargs hnd\n"
    "  rw [impl_eq_foldl]\n"
)

# The ENTIRE frozen proof region (bridging lemma + obligation). Swapped whole by
# the append-form positive, whose impl is not definitionally the fold, so
# `impl_eq_foldl` is not merely re-proved but no longer needed: that positive
# reproves the obligation directly from its own inline inductions. Kept as one
# anchor so the swap cannot silently leave a stale bridging lemma behind.
_PROOF_FROZEN_ALL = _IEF_FROZEN + "\n" + (
    "theorem correct_scopedOp : ∀ (bindings kwargs : List (String × Int)),\n"
    "    (bindings.map Prod.fst).Nodup →\n"
    "    problem_spec_scopedOp bindings kwargs (implementation_scopedOp bindings kwargs) := by\n"
    "  intro bindings kwargs hnd\n"
    "  rw [impl_eq_foldl]\n"
    "  refine ⟨?_, ?_⟩\n"
    "  · intro b hb\n"
    "    exact foldl_lookup_bound bindings hnd kwargs b hb\n"
    "  · intro k hk\n"
    "    exact foldl_lookup_other bindings kwargs k hk\n"
)


SPEC_TESTS = [
    # =====================================================================
    # POSITIVE CONTROL (soundness), OBSERVABLY DISTINCT SHAPE — a correct impl
    # that is NOT definitionally equal to the frozen one. This is the load-
    # bearing soundness probe of the battery, and the reason it exists next to
    # the `foldl` positive below: the `foldl` reshape has the frozen impl's
    # `impl_eq_foldl` closing by `rfl`, i.e. the two impls are the SAME TERM up
    # to unfolding, so a spec could reject every genuinely different correct
    # impl and that case would still pass. This one cannot pass that way — it
    # returns a DIFFERENT LIST from the frozen impl on the same input
    # (`[("f",1),("g",5)]` where the frozen impl returns `[("g",5),("f",1)]`),
    # and the two are only equal as MAPS, which is precisely the equivalence the
    # postcondition is supposed to be stated up to. `problem_spec_scopedOp`
    # observes `result` only through `.lookup`, so a spec that pinned the list
    # ORDER (or the concrete carrier) rather than the map would reject this and
    # be SPEC-TOO-STRONG relative to the modeled behavior.
    #
    # The impl prepends the bindings to the caller kwargs and relies on
    # `List.lookup`'s first-occurrence semantics to give the binding priority —
    # the same override the frozen `kwUpsert` gets by replacing in place. The
    # proof is reworked accordingly (two inline `have`-scoped inductions on the
    # bindings, no new top-level declaration, no axiom, no `sorry`); the
    # `theorem correct_scopedOp` STATEMENT stays byte-identical.
    # =====================================================================
    {
        "id": "pos-control-append-form",
        "kind": "soundness",
        "expect": "verify",
        "module": _swap(
            _swap(
                _BASE, _IMPL_FULL,
                "def implementation_scopedOp\n"
                "    (bindings kwargs : List (String × Int)) : List (String × Int) :=\n"
                "  bindings ++ kwargs\n",
            ),
            _PROOF_FROZEN_ALL,
            "theorem correct_scopedOp : ∀ (bindings kwargs : List (String × Int)),\n"
            "    (bindings.map Prod.fst).Nodup →\n"
            "    problem_spec_scopedOp bindings kwargs (implementation_scopedOp bindings kwargs) := by\n"
            "  have hbound : ∀ (bs kws : List (String × Int)), (bs.map Prod.fst).Nodup →\n"
            "      ∀ b ∈ bs, (bs ++ kws).lookup b.1 = some b.2 := by\n"
            "    intro bs\n"
            "    induction bs with\n"
            "    | nil => intro _ _ b hb; simp at hb\n"
            "    | cons a as ih =>\n"
            "      intro kws hn b hb\n"
            "      obtain ⟨k0, v0⟩ := a\n"
            "      simp only [List.map_cons, List.nodup_cons] at hn\n"
            "      obtain ⟨hnotin, hn'⟩ := hn\n"
            "      rcases List.mem_cons.mp hb with rfl | hmem\n"
            "      · simp [List.cons_append, List.lookup_cons]\n"
            "      · have hne : k0 ≠ b.1 := fun e => hnotin (e ▸ List.mem_map_of_mem hmem)\n"
            "        have hbq : ((b.1 : String) == k0) = false :=\n"
            "          beq_eq_false_iff_ne.mpr (fun e => hne e.symm)\n"
            "        simp only [List.cons_append, List.lookup_cons, hbq, Bool.false_eq_true, if_false]\n"
            "        exact ih kws hn' b hmem\n"
            "  have hframe : ∀ (bs kws : List (String × Int)) (k : String),\n"
            "      (∀ b ∈ bs, b.1 ≠ k) → (bs ++ kws).lookup k = kws.lookup k := by\n"
            "    intro bs\n"
            "    induction bs with\n"
            "    | nil => intro _ _ _; rfl\n"
            "    | cons a as ih =>\n"
            "      intro kws k h\n"
            "      obtain ⟨k0, v0⟩ := a\n"
            "      have hne : k0 ≠ k := h (k0, v0) List.mem_cons_self\n"
            "      have hbq : ((k : String) == k0) = false :=\n"
            "        beq_eq_false_iff_ne.mpr (fun e => hne e.symm)\n"
            "      simp only [List.cons_append, List.lookup_cons, hbq, Bool.false_eq_true, if_false]\n"
            "      exact ih kws k (fun b hb => h b (List.mem_cons_of_mem _ hb))\n"
            "  intro bindings kwargs hnd\n"
            "  have himpl : implementation_scopedOp bindings kwargs = bindings ++ kwargs := rfl\n"
            "  rw [himpl]\n"
            "  exact ⟨fun b hb => hbound bindings kwargs hnd b hb,\n"
            "         fun k hk => hframe bindings kwargs k hk⟩\n",
        ),
        "rationale": (
            "the merge is re-expressed as `bindings ++ kwargs`, giving the scope "
            "bindings priority through `List.lookup`'s first-occurrence semantics "
            "instead of by replacing in place. This is the battery's strongest "
            "soundness probe because it is NOT definitionally equal to the frozen "
            "impl: on bindings [f↦1] and kwargs [g↦5] it returns "
            "[(f,1),(g,5)] where the frozen impl returns [(g,5),(f,1)]. The two "
            "agree as MAPS but not as lists, so this case verifies only if the "
            "postcondition really observes `result` up to `.lookup` — a spec that "
            "pinned list order or the concrete carrier would reject a faithful "
            "correct impl (SPEC-TOO-STRONG). It also confirms the `Nodup` "
            "precondition is doing the work it claims: without it the "
            "prepend-merge would not force the binding for a duplicated key. "
            "Proof: two inline `have`-scoped inductions over the bindings, no new "
            "top-level declaration, no axiom, no `sorry`; the theorem statement is "
            "byte-identical."
        ),
    },

    # =====================================================================
    # POSITIVE CONTROL (soundness) — a structurally DIFFERENT but CORRECT
    # implementation that MUST verify. If a faithful correct impl cannot satisfy
    # the frozen obligation the spec is SPEC-TOO-STRONG. The theorem statement
    # stays byte-identical; the reshape is a pure functional `foldl` in place of
    # the `Id.run do`/`let mut`/`for` loop — the SAME value on every input. Its
    # `impl_eq_foldl` bridging lemma then closes by `rfl` (the impl *is* the
    # fold), and the frozen `correct_scopedOp` body is retained verbatim. No new
    # lemma, no axiom, no `sorry`.
    #
    # Ports nagini case 1 (pos-control-reorder-goc): the nagini positive was a
    # structurally-different-but-correct reshape of the modeled core (branch
    # reorder). Here the analogous reshape expresses the same merge as a pure
    # left fold rather than a mutable loop.
    # =====================================================================
    {
        "id": "pos-control-foldl-form",
        "kind": "soundness",
        "expect": "verify",
        "module": _swap(
            _swap(
                _BASE, _IMPL_FULL,
                "def implementation_scopedOp\n"
                "    (bindings kwargs : List (String × Int)) : List (String × Int) :=\n"
                "  bindings.foldl (fun acc b => kwUpsert acc b.1 b.2) kwargs\n",
            ),
            _IEF_FROZEN,
            "theorem impl_eq_foldl (bindings kwargs) :\n"
            "    implementation_scopedOp bindings kwargs\n"
            "      = bindings.foldl (fun acc b => kwUpsert acc b.1 b.2) kwargs := by\n"
            "  rfl\n",
        ),
        "rationale": (
            "the merge is re-expressed as a pure `List.foldl` (replace-first-else-"
            "append per binding) instead of the mutable `Id.run do`/`for` loop; "
            "the produced map is identical on every input, so both clauses of "
            "`problem_spec_scopedOp` still hold. Proof: the bridging lemma "
            "`impl_eq_foldl` now closes by `rfl` and the frozen `correct_scopedOp` "
            "body is retained verbatim; no new lemma/axiom/sorry. "
            "SCOPE OF THE EVIDENCE, stated honestly: that `rfl` is exactly why "
            "this case is the WEAKER of the two positives. The `Id.run do`/`for` "
            "loop already ELABORATES to the fold, so the two impls are the same "
            "term up to unfolding and this case cannot by itself witness "
            "SPEC-TOO-STRONG — a spec that rejected every observably different "
            "correct impl would still pass it. Its real content is narrower and "
            "still worth having: it shows the obligation is not tied to the "
            "SURFACE SYNTAX of the mutable loop (`Id.run`/`forIn` unfolding is not "
            "load-bearing), so a correct impl written in direct functional style "
            "is accepted. The observably-distinct positive above "
            "(`pos-control-append-form`, which returns a different list) is what "
            "actually discharges SPEC-TOO-STRONG. Ports nagini's "
            "structurally-different-correct positive to the single modeled core."
        ),
    },

    # =====================================================================
    # ADMISSIBILITY — a positive control confirming the obligation is
    # SATISFIABLE (non-vacuous) at the normal, F2P-shaped merge input rather than
    # only in the abstract `∀`. The frozen `correct_scopedOp` carries ONE
    # precondition hypothesis (`(bindings.map Prod.fst).Nodup`); the honest
    # analogue of nagini's precondition-admission probe is to discharge the spec
    # predicate at a ground input whose bindings ARE nodup (the generic-relation
    # F2P scenario: two distinct scope keys `ct`/`oid`, a disjoint caller key
    # `field`), alongside the frozen obligation. Ports nagini case 2
    # (admiss-acreate-fresh-accessor).
    # =====================================================================
    {
        "id": "admiss-ground-merge-instance",
        "kind": "admissibility",
        "expect": "verify",
        # Prepend a ground `have` discharging the obligation at the two-binding
        # F2P-shaped input, reusing the frozen helper lemmas; then close the
        # frozen obligation verbatim. Nothing is assumed: no new declaration, the
        # theorem statement is byte-identical, the ground instance is a `have`
        # inside the existing tactic body, and its `Nodup` side-goal is `decide`d.
        "module": _swap(
            _BASE, _PROOF_HEAD,
            '  have _ground : problem_spec_scopedOp [("ct", 7), ("oid", 3)] [("field", 2)]\n'
            '      (implementation_scopedOp [("ct", 7), ("oid", 3)] [("field", 2)]) := by\n'
            "    rw [impl_eq_foldl]\n"
            "    refine ⟨?_, ?_⟩\n"
            "    · intro b hb; exact foldl_lookup_bound _ (by decide) _ b hb\n"
            "    · intro k hk; exact foldl_lookup_other _ _ k hk\n"
            + _PROOF_HEAD,
        ),
        "rationale": (
            "the obligation is discharged at a ground F2P-shaped merge input (two "
            "distinct scope bindings ct↦7, oid↦3 over a disjoint caller key "
            "field↦2 — the generic-relation scenario), then the frozen obligation "
            "is closed verbatim. Verifies (else the modeled behavior is "
            "unsatisfiable at exactly the input the F2P exercises — the analogue "
            "of PRECOND-TOO-STRONG). Nothing is assumed: no new declaration, the "
            "theorem statement is byte-identical, the ground instance is a `have` "
            "reusing the frozen helper lemmas, and its `Nodup` side-condition is "
            "`decide`d. Ports nagini's fresh-accessor admissibility probe."
        ),
    },

    # =====================================================================
    # UNIQUENESS / SPEC-TOO-WEAK rivals — wrong implementations sharing the
    # frozen spec that MUST be rejected. Each carries (a) the refinement
    # argument that its faithful real patch would NOT resolve the F2P, so a
    # verifying rival would be a true verify-does-not-imply-resolve break rather
    # than an artifact, and (b) a refutation witness pinning the violation at one
    # concrete input, checked both ways.
    # =====================================================================

    # ---- the pre-fix bug: never merge the bindings (nagini cases 3 & 4) ----
    {
        "id": "weak-no-merge",
        "kind": "uniqueness",
        "expect": "reject",
        # Pre-fix behavior: hand the caller kwargs straight to the data op, never
        # merging any scope binding. This is the pre-patch skeleton verbatim.
        "module": _swap(_BASE, _IMPL_BODY, "  return kwargs\n"),
        "refinement": (
            "this IS the pre-fix defect (Solution_prepatch: `return kwargs`): the "
            "async method delegated to the bare data op on the caller kwargs, so "
            "the scope binding was never forced in. Its faithful real patch is the "
            "unpatched code where the async form runs the collection-unscoped op — "
            "which is exactly what FAILS test_acreate / test_acreate_reverse / "
            "test_generic_async_acreate (after the operation the newly-created "
            "object must belong to the scoped collection: `aget()`/`acount()` "
            "observe the scope binding). It does NOT resolve, so a verifying rival "
            "here is a true verify-not-resolve break."
        ),
        "rationale": (
            "REJECT from clause 1 (bound keys forced): with a single binding "
            "f↦1 and empty caller kwargs, `result.lookup \"f\"` must be `some 1`, "
            "but `return kwargs` yields `[]` whose lookup is `none`. Binder "
            "spread: bindings length 1, kwargs empty."
        ),
        "witness": (
            'example : ¬ problem_spec_scopedOp [("f", 1)] [] (implementation_scopedOp [("f", 1)] []) := by\n'
            '  intro h\n'
            '  have hb := h.1 ("f", 1) (by simp)\n'
            '  revert hb\n'
            '  decide\n'
        ),
    },

    # ---- merge only the first binding (traversal completeness) ----
    {
        "id": "weak-partial-merge",
        "kind": "uniqueness",
        "expect": "reject",
        # Force in only the FIRST scope binding, dropping the rest. Correct when
        # there is a single binding (FK/reverse), wrong for the generic op which
        # carries two (content-type + object-id).
        "module": _swap(
            _BASE, _IMPL_BODY,
            "  let mut out := kwargs\n"
            "  for b in bindings.take 1 do\n"
            "    out := kwUpsert out b.1 b.2\n"
            "  return out\n",
        ),
        "refinement": (
            "a faithful real patch that merged only the first scope binding would "
            "set the content-type key but leave the object-id key unset for the "
            "generic manager (which binds TWO distinct scope keys). The created "
            "object would then not belong to the scoped collection under the "
            "object-id, so test_generic_async_acreate / "
            "test_generic_async_aget_or_create (which assert `acount()` on the "
            "scoped collection after the op) FAIL. It does NOT resolve; the "
            "single-binding FK scenarios still pass, so it is a partial-domain "
            "miss on exactly the multi-binding path."
        ),
        "rationale": (
            "REJECT from clause 1 at a TAIL binding: with bindings [f↦1, g↦2] and "
            "empty kwargs, `result.lookup \"g\"` must be `some 2`, but a "
            "first-only merge leaves g unset (`none`). Distinct from weak-no-merge "
            "— it moves the bindings binder to length 2 and probes the tail key, "
            "the sub-domain a length-1 witness cannot reach."
        ),
        "witness": (
            'example : ¬ problem_spec_scopedOp [("f", 1), ("g", 2)] [] (implementation_scopedOp [("f", 1), ("g", 2)] []) := by\n'
            '  intro h\n'
            '  have hb := h.1 ("g", 2) (by simp)\n'
            '  revert hb\n'
            '  decide\n'
        ),
    },

    # ---- bind the scope key to the WRONG value (value pin) ----
    {
        "id": "weak-wrong-value",
        "kind": "uniqueness",
        "expect": "reject",
        # Force the scope key in, but to a perturbed value rather than the scope
        # value itself.
        "module": _swap(
            _BASE, _IMPL_BODY,
            "  let mut out := kwargs\n"
            "  for b in bindings do\n"
            "    out := kwUpsert out b.1 (b.2 + 1)\n"
            "  return out\n",
        ),
        "refinement": (
            "a faithful real patch that merged the scope KEY but under the wrong "
            "value (e.g. attaching the created object to the wrong owning "
            "instance / content object) would place the object outside the "
            "collection the test queries. test_acreate_reverse asserts the "
            "created object's owner IS `self.s1`, and the generic tests count the "
            "scoped collection; a wrong owner value fails both. It does NOT "
            "resolve — every input is wrong, so the F2P observes it immediately."
        ),
        "rationale": (
            "REJECT from clause 1 (bound value pinned): with binding ct↦7 the spec "
            "requires `result.lookup \"ct\" = some 7`, but the rival stores "
            "`some 8`. Binder spread: bindings [ct↦7], kwargs empty; probes the "
            "VALUE component of clause 1, which the no-merge/partial-merge rivals "
            "(both about a MISSING key) do not."
        ),
        "witness": (
            'example : ¬ problem_spec_scopedOp [("ct", 7)] [] (implementation_scopedOp [("ct", 7)] []) := by\n'
            '  intro h\n'
            '  have hb := h.1 ("ct", 7) (by simp)\n'
            '  revert hb\n'
            '  decide\n'
        ),
    },

    # ---- drop the caller's own kwargs (frame: clause 2, missing key) ----
    {
        "id": "weak-drop-caller-kwargs",
        "kind": "uniqueness",
        "expect": "reject",
        # Return only the bindings, discarding the caller's argument map. The
        # scope keys are present (clause 1 holds) but every non-scope caller key
        # is lost — the frame is violated.
        "module": _swap(_BASE, _IMPL_BODY, "  return bindings\n"),
        "refinement": (
            "a faithful real patch that forwarded only the scope bindings and "
            "dropped the caller's own kwargs would lose the user-supplied fields "
            "(e.g. `field=2` in test_acreate, `tag=\"orange\"` in "
            "test_generic_async_acreate). The created object would miss its "
            "caller-set attributes, so the F2P assertions on those values "
            "(`new_simple.field == 2`, `tag.tag == ...`) FAIL. It does NOT "
            "resolve."
        ),
        "rationale": (
            "REJECT from clause 2 (frame): key g is not a scope key (bindings = "
            "[f↦1]) so the spec requires `result.lookup \"g\" = kwargs.lookup "
            "\"g\" = some 5`, but `return bindings` yields `none` for g. Binder "
            "spread: kwargs carries a disjoint caller key [g↦5]; the first rival "
            "to attack clause 2 rather than clause 1."
        ),
        "witness": (
            'example : ¬ problem_spec_scopedOp [("f", 1)] [("g", 5)] (implementation_scopedOp [("f", 1)] [("g", 5)]) := by\n'
            '  intro h\n'
            '  have hg := h.2 "g" (by decide)\n'
            '  revert hg\n'
            '  decide\n'
        ),
    },

    # ---- caller value WINS over the scope binding (the override sub-domain) ----
    {
        "id": "weak-caller-wins-override",
        "kind": "uniqueness",
        "expect": "reject",
        # Merge a binding only when the caller did NOT already supply that key
        # (a `setdefault`-style merge). Correct on the whole disjoint-key
        # sub-domain every other rival lives in; wrong exactly where the caller
        # supplies a scope key, which is the case the binding must override.
        "module": _swap(
            _BASE, _IMPL_BODY,
            "  let mut out := kwargs\n"
            "  for b in bindings do\n"
            "    out := if (out.lookup b.1).isSome then out else kwUpsert out b.1 b.2\n"
            "  return out\n",
        ),
        "refinement": (
            "a faithful real patch that merged each scope binding only when the "
            "key was absent (a `setdefault`-style merge rather than an assign) "
            "would let a caller-supplied value for a scope key survive, so the "
            "created object would be attached to a collection the caller named "
            "rather than the one the operation was invoked through. It is correct "
            "whenever the caller supplies no scope key — which is the shape of "
            "most of the F2P calls — so it is a genuine partial-domain miss "
            "rather than a wholesale break, and exactly the sub-domain the other "
            "rivals leave unattacked. It does NOT resolve: a caller who passes "
            "the scope key explicitly gets an object outside the collection "
            "`aget()`/`acount()` then queries."
        ),
        "rationale": (
            "REJECT from clause 1 at the OVERRIDE point: with binding ct↦7 and "
            "caller kwargs [ct↦9] the spec requires `result.lookup \"ct\" = some "
            "7` (the binding overrides the caller), but a merge-if-absent rival "
            "leaves `some 9`. Binder spread: the only witness where a caller key "
            "COLLIDES with a scope key, so the frame clause does not apply and "
            "clause 1 alone must force the binding to win. This is also what "
            "distinguishes `kwUpsert` (replace-first) from a plain append."
        ),
        "witness": (
            'example : ¬ problem_spec_scopedOp [("ct", 7)] [("ct", 9)] (implementation_scopedOp [("ct", 7)] [("ct", 9)]) := by\n'
            '  intro h\n'
            '  have hb := h.1 ("ct", 7) (by simp)\n'
            '  revert hb\n'
            '  decide\n'
        ),
    },

    # ---- introduce a spurious extra key (frame: clause 2, extra key) ----
    {
        "id": "weak-spurious-key",
        "kind": "uniqueness",
        "expect": "reject",
        # Merge the bindings correctly but ALSO append an unrelated key that was
        # neither a scope binding nor a caller argument — the referentially-
        # transparent analogue of nagini's double-attach (spurious mutation).
        "module": _swap(
            _BASE, _IMPL_BODY,
            "  let mut out := kwargs\n"
            "  for b in bindings do\n"
            "    out := kwUpsert out b.1 b.2\n"
            '  out := kwUpsert out "z" 7\n'
            "  return out\n",
        ),
        "refinement": (
            "a faithful real patch that injected an extra field into the effective "
            "argument map (an over-merge) would pass an unexpected kwarg to the "
            "underlying data op — a field the model neither declares nor the "
            "caller supplied — which raises / creates a malformed row. This is the "
            "referentially-transparent analogue of nagini's double-attach "
            "(over-extended related set): the F2P assertions that the created "
            "object matches exactly the supplied+scope fields FAIL. It does NOT "
            "resolve. (nagini case 7, weak-acreate-double-attach.)"
        ),
        "rationale": (
            "REJECT from clause 2 (frame): key z is neither a scope key "
            "(bindings=[f↦1]) nor present in kwargs=[q↦4], so the spec requires "
            "`result.lookup \"z\" = kwargs.lookup \"z\" = none`, but the rival "
            "introduces `some 7`. Binder spread: kwargs = [q↦4] (a distinct "
            "caller key from the drop-caller rival), probing the EXTRA-key "
            "direction of the frame."
        ),
        "witness": (
            'example : ¬ problem_spec_scopedOp [("f", 1)] [("q", 4)] (implementation_scopedOp [("f", 1)] [("q", 4)]) := by\n'
            '  intro h\n'
            '  have hz := h.2 "z" (by decide)\n'
            '  revert hz\n'
            '  decide\n'
        ),
    },
]

# No AXIOM lane here: the bundle consumes no `axiom` and declares no `opaque`
# (the merge is modeled deeply as `kwUpsert`, an R leg validated by G-CONF).
# The nagini AXIOM_TESTS were also empty; dropped.
AXIOM_TESTS = []
