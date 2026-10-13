"""properties.py — G-PBT falsification battery for sympy__sympy-13615 (lean).

NOT a Lean module; a manifest the G-PBT gate executes. Each SPEC_TESTS case is a
full ``Solution.lean`` variant produced by REGION SURGERY: only text inside the
``-- impl-start`` / ``-- impl-end`` region (and, for the reproving positives,
inside ``-- proof-start`` / ``-- proof-end``) differs from the frozen file. The
consumer spec view elides both regions, so ``markers.same_spec`` holds by
construction, and every variant keeps ``theorem correct_partitionByMembership``
present with a BYTE-IDENTICAL statement — only its tactic body is ever retuned.
No case adds an ``axiom``/``theorem``/``lemma`` and none reaches for
``sorry``/``admit``/``native_decide``.

``expect:"verify"`` passes iff (in scope AND the whole obligation discharges);
``expect:"reject"`` passes iff (in scope AND does NOT verify AND its refutation
``witness`` discriminates — the witness must ELABORATE against the rival and
FAIL against the frozen solution).

================================  DEFENDED SURFACE  ==========================

ONE obligation over ONE modeled function:

  implementation_partitionByMembership
      (contains : α → Option Bool) (other : List α) : ComplementResult α

It splits a finite ordered collection of candidates by a THREE-VALUED membership
outcome supplied per candidate by the ``contains`` classifier:

  * ``some false`` — a definite "no": the candidate is RETAINED as an explicit
    member of the difference (``result.kept``);
  * ``none``       — undetermined: the candidate is SET ASIDE separately
    (``result.unresolved``), and must NOT be treated as a confirmed member;
  * ``some true``  — a definite "yes": the candidate is EXCLUDED entirely and
    appears in NEITHER group.

The postcondition has TWO independent top-level conjuncts, both order-preserving
selections of the SAME input list:

  (P1) ``result.kept = other.filter (fun el => contains el = some false)``
  (P2) ``result.unresolved = other.filter (fun el => contains el = none)``

(P2) is the LOAD-BEARING clause of the change: undetermined candidates must be
carried in a SEPARATE group, never folded into ``kept`` and never dropped.

Both clauses are GROUNDED in the two input binders — ``filter`` over ``other``
composed with the caller-supplied ``contains`` — NOT an opaque answer key a
wrong impl could echo. So (as the nagini sibling's own note argues) there is no
"ungrounded-oracle echo" rival to build; honest positive controls stand in its
place.

THE DISCRIMINATING BEHAVIOUR (the public issue): forming the difference of a
finite collection that MIXES candidates with a definite-negative outcome and
candidates whose membership is undetermined. The pre-change code retained every
candidate whose outcome was not the definite-yes sentinel in ONE group and
produced no separate set-aside group, silently asserting the undetermined
candidates lie outside the subtracted set. Any rival that folds an undetermined
candidate into ``kept``, or drops it from ``unresolved``, reproduces that exact
behaviour and would NOT resolve the failing test.

================================  THE CARRIER  ===============================

Unlike the velvet sibling (whose classifier is an ``opaque`` global that never
reduces), THIS bundle takes the classifier as an INPUT PARAMETER. So the carrier
is FULLY TRANSPARENT: a witness may instantiate ``contains`` with a concrete
``fun`` literal and a concrete ``other``, and ``decide`` computes both sides of
(P1)/(P2). No conditioning on the carrier is needed, no hypothesis is bound, and
therefore no witness can be forged from an inconsistent binder set — every
witness head below binds NOTHING and states its refutation at literal inputs.

Each reject witness states ``¬ problem_spec_partitionByMembership c xs
(implementation_partitionByMembership c xs)`` at a concrete ``(c, xs)`` and
closes by ``unfold; decide``. It is checked in a file whose ``proof`` region has
been emptied, so the frozen tactic script cannot mask the verdict. This matters
here: every one of the six rivals is a loop-free closed form, and the frozen
script (an induction over the ``for`` loop's ``forIn``) fails on ALL of them
with ``Tactic 'rewrite' failed`` — the SAME error a merely-reshaped CORRECT impl
would give. Confirmed out of band with ``scripts/lean_verify.sh``: each of the
six rivals exits 1 on the frozen script, each witness ELABORATES against its
own rival (exit 0) and FAILS against the frozen solution (exit 1), so each
rejection is attributable to the postcondition rather than to tactic breakage.

The gold-side failure is a PLAIN EVALUATION in every case: ``decide`` reduces
both conjuncts at the literal inputs and reports that it proved the negated
proposition false — it refutes the CLAIM, not a missing identifier and not a
stuck unfolding. Independently re-derived by a forgery test: flipping each
witness's claim (dropping the ``¬``) INVERTS both exit codes — exit 0 on gold,
exit 1 on the rival — so gold's exit code tracks what is asserted and carries
real information about the spec at that point.

ADVERSARIAL READ of the nagini classes on this carrier (case-by-case accounting
in the footer):

  * FRAME / PERMISSION-MUTATION — VACUOUS. The sibling carries TWO MANDATORY
    rivals that illegally WRITE the read-only input list (append / index-assign)
    and are rejected by the permission system rather than by a value mismatch.
    Lean is referentially transparent: ``other : List α`` is an immutable value,
    there is no heap, no aliasing and no fractional permission, so there is no
    read-only input to overwrite and no substitute probe to fabricate.
  * DIVERGENCE / NON-TERMINATION — VACUOUS on this backend, and genuinely so
    (not a known spec hole as it would be on velvet under
    ``loom.semantics.termination "partial"``, cf. the corpus-wide termination-semantics finding):
    ``implementation_partitionByMembership`` is a total Lean ``def`` over a
    ``for`` loop on a finite list, so a diverging implementation cannot be
    written at all. The sibling carries no ``diverge-*`` case either, so nothing
    was dropped.
  * PARTIAL-DOMAIN / VALUE / ROUTING — the heart of this port: each reject rival
    is correct on part of the domain and wrong on a sub-domain, refuted at a
    concrete point that pins one routing decision.

AXIOM lane: DROPPED. The ``axioms`` region of this bundle is a skip stub (the
three-valued outcome is an input classifier, so the proof consumes no callee
contract); the axiom lane is G-AX's job and this gate ignores ``AXIOM_TESTS``
regardless.
"""
from pathlib import Path

INSTANCE = "sympy__sympy-13615"
BACKEND = "lean"

_BASE = (Path(__file__).parent / "Solution.lean").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# ---------------------------------------------------------------------------
# ANCHORS. Each lies wholly inside the region it is meant to edit and is unique
# in Solution.lean; both facts are asserted at load by _swap, so the manifest
# breaks LOUDLY if the frozen solution ever drifts.
# ---------------------------------------------------------------------------

# (A) The whole executable body of the modeled function — everything from the
# `Id.run do` onwards, inside the impl region. Reject rivals replace it with a
# loop-free closed form.
_IMPL_BODY = """ Id.run do
  let mut kept : List α := []
  let mut unresolved : List α := []
  for el in other do
    match contains el with
    | some true => pure ()            -- definite member: dropped from both groups
    | some false => kept := kept ++ [el]
    | none => unresolved := unresolved ++ [el]
  return { kept := kept, unresolved := unresolved }"""

# (B) The three-way dispatch inside the loop body (impl region only). The
# branch-reorder positive permutes these arms.
_IMPL_MATCH = """    match contains el with
    | some true => pure ()            -- definite member: dropped from both groups
    | some false => kept := kept ++ [el]
    | none => unresolved := unresolved ++ [el]"""

# (C) The matching dispatch inside the proof's loop lemma (proof region only).
# Permuting (B) forces the same permutation here for the induction to line up;
# the `theorem correct_partitionByMembership` STATEMENT is untouched.
_PROOF_MATCH = """        match contains el with
        | some true => pure (ForInStep.yield ⟨r.fst, r.snd⟩)
        | some false => pure (ForInStep.yield ⟨r.fst ++ [el], r.snd⟩)
        | none => pure (ForInStep.yield ⟨r.fst, r.snd ++ [el]⟩)"""

# (D) The whole loop (impl region) — the ladder positive reshapes the dispatch
# from a `match` into an explicit three-rung `if` chain.
_IMPL_LOOP = """  for el in other do
    match contains el with
    | some true => pure ()            -- definite member: dropped from both groups
    | some false => kept := kept ++ [el]
    | none => unresolved := unresolved ++ [el]
  return { kept := kept, unresolved := unresolved }"""

# (E) The frozen proof body (everything between the proof markers). Only the
# ladder positive rewrites it, and it re-emits the SAME theorem statement.
_PROOF_BODY = _BASE.split("-- proof-start\n")[1].split("\n-- proof-end")[0]
if _BASE.count(_PROOF_BODY) != 1:
    raise AssertionError("drift: proof region text is not unique")

# (F) The first tactic line of the frozen proof, immediately after the
# byte-identical theorem statement. The admissibility positive splices a ground
# `have` in HERE — inside the existing tactic body, after the binders are
# introduced — so the theorem statement is untouched and no declaration is added.
_PROOF_INTRO = "  intro contains other\n"


def _closed(kept: str, unresolved: str, note: str) -> str:
    """Solution.lean whose impl is a single loop-free record literal."""
    return _swap(_BASE, _IMPL_BODY,
                 f"\n  -- {note}\n"
                 f"  {{ kept := {kept},\n    unresolved := {unresolved} }}")


def _w(classifier: str, xs: str) -> str:
    """A refutation witness at a CONCRETE classifier + candidate list.

    Binds nothing (the carrier computes), so there are no hypotheses that could
    be inconsistent; `decide` evaluates both postcondition conjuncts.
    """
    return (
        f"example : ¬ problem_spec_partitionByMembership\n"
        f"    ({classifier}) {xs}\n"
        f"    (implementation_partitionByMembership\n"
        f"      ({classifier}) {xs}) := by\n"
        "  unfold problem_spec_partitionByMembership implementation_partitionByMembership\n"
        "  decide\n"
    )


SPEC_TESTS = [
    # =====================================================================
    # SOUNDNESS — positive controls. A structurally DIFFERENT but CORRECT impl
    # must still discharge the byte-identical obligation, else SPEC-TOO-STRONG.
    # Both proofs below were closed honestly (real builds, exit 0): no helper
    # lemma, no weakened statement, no sorry.
    # =====================================================================

    # POS 1 — DISPATCH REORDER. Write the three-way dispatch in the opposite
    # order (undetermined first, definite-member last). The three outcome classes
    # are mutually exclusive, so the arm order is observationally irrelevant. The
    # loop lemma inside the proof is permuted identically; the theorem statement
    # is untouched and the induction closes unchanged. Ports the sibling's
    # `pos-control-branch-reorder` argument (undetermined tested first).
    {
        "id": "pos-control-branch-reorder",
        "kind": "soundness",
        "expect": "verify",
        "module": _swap(
            _swap(_BASE, _IMPL_MATCH,
                  "    match contains el with\n"
                  "    | none => unresolved := unresolved ++ [el]\n"
                  "    | some false => kept := kept ++ [el]\n"
                  "    | some true => pure ()            "
                  "-- definite member: dropped from both groups"),
            _PROOF_MATCH,
            "        match contains el with\n"
            "        | none => pure (ForInStep.yield ⟨r.fst, r.snd ++ [el]⟩)\n"
            "        | some false => pure (ForInStep.yield ⟨r.fst ++ [el], r.snd⟩)\n"
            "        | some true => pure (ForInStep.yield ⟨r.fst, r.snd⟩)"),
        "rationale": "PASS SOURCE = (P1) ∧ (P2). Reordering the three dispatch "
                     "arms (undetermined first, definite-member last) cannot "
                     "change the output on ANY input: the three outcome classes "
                     "are mutually exclusive, so exactly one arm fires per "
                     "candidate either way, and each arm appends to the same "
                     "group in the same position. Both conjuncts therefore still "
                     "hold, and the loop lemma's identical permutation lets the "
                     "frozen induction close the byte-identical obligation "
                     "(confirmed by a real build). If a faithful reshape could "
                     "not verify, the spec would be over-fit to the arm ORDER "
                     "(SPEC-TOO-STRONG).",
    },

    # POS 2 — EXPLICIT THREE-RUNG LADDER. Replace the `match` with an equality
    # ladder that names the outcome in a local and makes the definite-member rung
    # an EXPLICIT stated no-op (vs the frozen `match`'s arm). This is a genuinely
    # different dispatch shape, so the loop lemma is restated over the ladder and
    # the induction re-run; the theorem STATEMENT is byte-identical and the proof
    # closes with no new lemma (real build, exit 0). Ports the sibling's
    # `pos-control-equality-ladder`.
    {
        "id": "pos-control-equality-ladder",
        "kind": "soundness",
        "expect": "verify",
        "module": _swap(
            _swap(_BASE, _IMPL_LOOP,
                  "  for el in other do\n"
                  "    let v := contains el\n"
                  "    -- explicit three-rung ladder: the definite-member rung is\n"
                  "    -- a stated no-op rather than an unwritten fall-through\n"
                  "    if v = some false then\n"
                  "      kept := kept ++ [el]\n"
                  "    else if v = some true then\n"
                  "      pure ()\n"
                  "    else\n"
                  "      unresolved := unresolved ++ [el]\n"
                  "  return { kept := kept, unresolved := unresolved }"),
            _PROOF_BODY,
            "theorem correct_partitionByMembership {α : Type} :\n"
            "    ∀ (contains : α → Option Bool) (other : List α),\n"
            "      problem_spec_partitionByMembership contains other\n"
            "        (implementation_partitionByMembership contains other) := by\n"
            "  intro contains other\n"
            "  simp only [problem_spec_partitionByMembership, "
            "implementation_partitionByMembership, Id.run,\n"
            "    bind_pure_comp, map_pure]\n"
            "  have key : ∀ (l : List α) (k u : List α),\n"
            "      (forIn l ((⟨k, u⟩ : MProd (List α) (List α)) : "
            "MProd (List α) (List α)) (fun el r =>\n"
            "        if contains el = some false then\n"
            "          pure (ForInStep.yield ⟨r.fst ++ [el], r.snd⟩)\n"
            "        else if contains el = some true then\n"
            "          pure (ForInStep.yield ⟨r.fst, r.snd⟩)\n"
            "        else\n"
            "          pure (ForInStep.yield ⟨r.fst, r.snd ++ [el]⟩)) : "
            "Id (MProd (List α) (List α)))\n"
            "      = (⟨k ++ l.filter (fun el => contains el = some false),\n"
            "          u ++ l.filter (fun el => contains el = none)⟩ : "
            "MProd (List α) (List α)) := by\n"
            "    intro l\n"
            "    induction l with\n"
            "    | nil =>\n"
            "      intro k u\n"
            "      simp only [List.forIn_nil, List.filter_nil, List.append_nil]\n"
            "      rfl\n"
            "    | cons hd tl ih =>\n"
            "      intro k u\n"
            "      simp only [List.forIn_cons, List.filter_cons]\n"
            "      rcases h : contains hd with _ | b\n"
            "      · simp only [ih]\n"
            "        simp\n"
            "      · cases b\n"
            "        · simp only [ih]\n"
            "          simp\n"
            "        · simp only [ih]\n"
            "          simp\n"
            "  rw [key other [] []]\n"
            "  refine ⟨?_, ?_⟩ <;> rfl\n"),
        "rationale": "PASS SOURCE = (P1) ∧ (P2). An explicit three-rung equality "
                     "ladder — outcome hoisted into a local, definite-member rung "
                     "written as a stated no-op, undetermined reached as the final "
                     "`else` — classifies every candidate exactly as the frozen "
                     "`match` does, because the outcome type has exactly three "
                     "inhabitants and the ladder's rungs are those three in a "
                     "different guise. Both conjuncts hold on every input. The "
                     "loop lemma is restated over the ladder and the induction "
                     "re-run, keeping the obligation's statement byte-identical "
                     "and adding no lemma (real build, exit 0). Confirms the spec "
                     "is not pinned to the frozen dispatch's token shape; "
                     "otherwise SPEC-TOO-STRONG.",
    },

    # =====================================================================
    # ADMISSIBILITY — the obligation is SATISFIABLE at exactly an F2P-shaped
    # concrete input, not merely in the abstract. The frozen theorem carries no
    # precondition hypothesis (the modeled behaviour is total, so the `∀` is
    # unguarded), so nagini's precondition-admission probe has no binder to
    # attack HERE; the analogue on a total carrier is the obligation being
    # unsatisfiable at the F2P-shaped point, which discharging it BY EVALUATION
    # at that concrete point tests directly. Ports the sibling's
    # `admiss-self-call-singleton` to this carrier.
    # =====================================================================
    {
        "id": "admiss-ground-mixed-collection",
        "kind": "admissibility",
        "expect": "verify",
        # A ground `have` at a collection MIXING all three outcome classes,
        # discharged by `decide` (the carrier computes), spliced INSIDE the
        # frozen tactic body after `intro`; the frozen script then closes the
        # byte-identical obligation verbatim. No new declaration, no `sorry`.
        "module": _swap(
            _BASE, _PROOF_INTRO,
            _PROOF_INTRO
            + "  have _ground : problem_spec_partitionByMembership\n"
              "      (fun n : Nat => if n = 2 then some true else if n = 3 then "
              "some false else none)\n"
              "      [2, 3, 4]\n"
              "      (implementation_partitionByMembership\n"
              "        (fun n : Nat => if n = 2 then some true else if n = 3 "
              "then some false else none)\n"
              "        [2, 3, 4]) := by\n"
              "    unfold problem_spec_partitionByMembership "
              "implementation_partitionByMembership\n"
              "    decide\n"),
        "rationale": "PASS SOURCE = (P1) ∧ (P2), discharged BY EVALUATION at a "
                     "ground F2P-shaped input before the frozen obligation is "
                     "closed verbatim. The probe point `other = [2, 3, 4]` with a "
                     "classifier reporting a definite YES for 2, a definite NO for "
                     "3 and UNDETERMINED for 4 is exactly the discriminating "
                     "shape: a finite collection MIXING all three outcome classes, "
                     "which is what the reported failing behaviour exercises. "
                     "`decide` computes both conjuncts there, so this shows the "
                     "obligation is genuinely SATISFIABLE at that concrete point "
                     "and not vacuously true — the total-carrier analogue of "
                     "PRECOND-TOO-STRONG (an obligation no F2P-shaped input can "
                     "meet). Nothing is assumed: the ground instance is a `have` "
                     "inside the existing tactic body, the theorem statement is "
                     "byte-identical, and no declaration is added. Confirmed by a "
                     "real build (exit 0).",
    },

    # =====================================================================
    # UNIQUENESS — wrong impls sharing the frozen spec, each REJECTED with a
    # machine-checked refutation witness at its own concrete input point.
    # Together they attack BOTH conjuncts and move BOTH input binders.
    # =====================================================================

    # ---- THE PRE-CHANGE BEHAVIOUR (G-DIFF family): retain every candidate whose
    # ---- outcome is not the definite-yes sentinel in ONE group, and set nothing
    # ---- aside. Attacks (P1) AND (P2) the moment an undetermined candidate
    # ---- appears; correct on inputs with none. ----
    {
        "id": "weak-prepatch-fold-undecided-into-kept",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _closed(
            "other.filter (fun el => contains el != some true)", "[]",
            "single-bucket: every non-definite-member candidate retained "
            "directly"),
        "refinement": "this IS the pre-change behaviour: undetermined candidates "
                      "and definite-negative candidates are lumped into ONE "
                      "retained group and nothing is set aside, so the result "
                      "silently asserts that an undetermined candidate lies "
                      "outside the subtracted set. On the reported failing "
                      "behaviour — a finite collection mixing undetermined "
                      "candidates with a definite-negative one — it returns the "
                      "undetermined candidates as confirmed members instead of a "
                      "separate set-aside part, so the asserted equality between "
                      "the two spellings of the difference fails. The faithful "
                      "real patch (= the pre-change code) does NOT resolve.",
        "rationale": "REJECT from (P1) `result.kept = other.filter (contains · = "
                     "some false)` — the retained group also holds the "
                     "undetermined candidates the filter excludes — AND from (P2) "
                     "`result.unresolved = other.filter (contains · = none)` — the "
                     "set-aside group is empty where the filter is not. Refuted at "
                     "`other = [2, 7]` with a classifier reporting a definite YES "
                     "for 2 and UNDETERMINED for 7: the rival keeps 7 as a "
                     "confirmed member and sets nothing aside; the spec keeps "
                     "nothing and sets 7 aside. Also exercises the "
                     "definite-yes/excluded class in the same probe. If it "
                     "verified, the whole set-aside behaviour would be unpinned "
                     "(SPEC-TOO-WEAK).",
        "witness": _w("fun n : Nat => if n = 2 then some true else none",
                      "[2, 7]"),
    },

    # ---- (P2) ONLY: retained group exactly right, set-aside group always empty
    # ---- (undetermined candidates dropped). Correct wherever no candidate is
    # ---- undetermined; wrong the moment one is. ----
    {
        "id": "weak-unresolved-always-empty",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _closed(
            "other.filter (fun el => contains el = some false)", "[]",
            "undetermined candidates never set aside"),
        "refinement": "this gets the retained group exactly right but always "
                      "produces an EMPTY set-aside group — equivalent to "
                      "discarding every candidate whose membership is "
                      "undetermined, emitting no separate unevaluated part at "
                      "all. On the reported failing behaviour the undetermined "
                      "candidates VANISH from the result rather than being "
                      "carried, so the asserted equality fails. The faithful real "
                      "patch does NOT resolve.",
        "rationale": "REJECT from (P2) alone: whenever a candidate is "
                     "undetermined, `result.unresolved` is empty while "
                     "`other.filter (contains · = none)` is not. (P1) still holds "
                     "exactly, so the rejection is attributable SOLELY to the "
                     "missing set-aside candidates — the clause the change turns "
                     "on. Refuted at `other = [5]` with a classifier reporting "
                     "UNDETERMINED for every candidate (a point where the retained "
                     "group is legitimately empty, so nothing but (P2) can be "
                     "blamed).",
        "witness": _w("fun _ : Nat => none", "[5]"),
    },

    # ---- (P1) ONLY: set-aside group right, but the undetermined candidates ALSO
    # ---- leak into the retained group — a DOUBLE-COUNT a membership- or
    # ---- length-only proxy would miss. ----
    {
        "id": "weak-undecided-leaks-into-kept",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _closed(
            "other.filter (fun el => contains el = some false) ++ "
            "other.filter (fun el => contains el = none)",
            "other.filter (fun el => contains el = none)",
            "undetermined candidates also retained directly"),
        "refinement": "this carries the undetermined candidates in the set-aside "
                      "group (correct) but ALSO lists them among the confirmed "
                      "members — so the result simultaneously asserts they are "
                      "known to lie outside the subtracted set and that their "
                      "membership is unresolved, a contradiction the fixed "
                      "behaviour never produces. On the reported failing "
                      "behaviour it returns the undetermined candidates in BOTH "
                      "parts, so the asserted equality fails. The faithful real "
                      "patch does NOT resolve.",
        "rationale": "REJECT from (P1) alone: whenever a candidate is "
                     "undetermined, `result.kept` over-counts by exactly the "
                     "candidates `other.filter (contains · = some false)` "
                     "excludes. (P2) holds exactly, so the rejection is "
                     "attributable SOLELY to the retained-group over-count — a "
                     "double-count an order- or length-only proxy would miss. "
                     "Refuted at `other = [3, 4]` with a classifier reporting a "
                     "definite NO for 3 and UNDETERMINED for 4: the rival's "
                     "retained group is `[3, 4]`, the spec's is `[3]`. Distinct "
                     "from the two rivals above both in the input point and in "
                     "the clause blamed.",
        "witness": _w("fun n : Nat => if n = 3 then some false else none",
                      "[3, 4]"),
    },

    # ---- BOTH conjuncts, wrong ROUTING: the two groups are exchanged. Correct
    # ---- only where no candidate is definite-negative and none is undetermined
    # ---- (all excluded, or empty); wrong the moment either class appears. ----
    {
        "id": "weak-groups-swapped",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _closed(
            "other.filter (fun el => contains el = none)",
            "other.filter (fun el => contains el = some false)",
            "the two retained groups exchanged"),
        "refinement": "this exchanges the two groups: the definite-negative "
                      "candidates are set aside as unresolved while the "
                      "undetermined candidates are listed as confirmed members. "
                      "It both asserts undetermined candidates lie outside the "
                      "subtracted set AND leaves genuinely-excluded-from-`self` "
                      "candidates in an unevaluated part, so the result is "
                      "structurally wrong on the reported behaviour and the "
                      "asserted equality fails. The faithful real patch does NOT "
                      "resolve.",
        "rationale": "REJECT from (P1) (the retained group receives the "
                     "undetermined candidates, not the definite-negative ones) "
                     "AND (P2) (the set-aside group receives the "
                     "definite-negative ones). Refuted at `other = [9]` with a "
                     "classifier reporting a definite NO for every candidate — a "
                     "point with NO undetermined candidate at all, so this rival "
                     "is refuted on a sub-domain where every other rival above is "
                     "CORRECT. That moves the attacked outcome class off "
                     "`none` and onto `some false`, and moves the `contains` "
                     "binder to a constant definite-negative classifier.",
        "witness": _w("fun _ : Nat => some false", "[9]"),
    },

    # ---- OFF-BY-ONE boundary: never classify the LEADING candidate. Correct
    # ---- whenever the first candidate is a definite member (excluded anyway);
    # ---- wrong when it is definite-negative (missing from the retained group)
    # ---- or undetermined (missing from the set-aside group). Needs a ≥2-element
    # ---- input, which also moves the `other` binder off length 1. ----
    {
        "id": "weak-skip-first-element",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _closed(
            "(other.drop 1).filter (fun el => contains el = some false)",
            "(other.drop 1).filter (fun el => contains el = none)",
            "the leading candidate is never classified"),
        "refinement": "this never classifies the FIRST candidate of the "
                      "collection, dropping it from BOTH parts regardless of its "
                      "outcome — a definite-negative leading candidate vanishes "
                      "from the confirmed members, an undetermined leading "
                      "candidate from the set-aside part. On any difference whose "
                      "first candidate is retained or undetermined, the result "
                      "loses an element it must keep, so both the reported "
                      "behaviour and the surrounding set-algebra equalities fail. "
                      "The faithful real patch does NOT resolve.",
        "rationale": "REJECT from (P1)/(P2) at the leading input position: "
                     "`filter` over `other` keeps index 0, `filter` over "
                     "`other.drop 1` cannot — an off-by-one a value proxy that "
                     "ignores the first element would miss, and one no other "
                     "rival here commits. Refuted at `other = [6, 8]` with a "
                     "classifier reporting a definite NO for 6 and a definite YES "
                     "for 8: the rival's retained group is empty, the spec's is "
                     "`[6]`. Probes an input of length 2 whose ONLY interesting "
                     "candidate is at index 0, and combines the definite-negative "
                     "and definite-yes classes with no undetermined candidate at "
                     "all — a classifier shape distinct from all four above.",
        "witness": _w("fun n : Nat => if n = 6 then some false else some true",
                      "[6, 8]"),
    },

    # ---- ORDER: the right ELEMENTS in the retained group, in the WRONG ORDER.
    # ---- Set-membership is perfect and both group SIZES are exact, so every
    # ---- membership-, length- or multiset-only proxy is satisfied; only the
    # ---- order-preserving `filter` equality in (P1) refutes it. Correct on any
    # ---- input with fewer than two definite-negative candidates. ----
    {
        "id": "weak-kept-order-reversed",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _closed(
            "(other.filter (fun el => contains el = some false)).reverse",
            "other.filter (fun el => contains el = none)",
            "retained group emitted in reverse candidate order"),
        "refinement": "this retains EXACTLY the right candidates and sets aside "
                      "exactly the right ones, but emits the retained group in "
                      "reverse candidate order — so the result no longer records "
                      "the two groups in the collection's own iteration order. The "
                      "spec's asserted equality is between two ORDER-PRESERVING "
                      "selections of the same input, so it fails as soon as two "
                      "candidates are definite-negative. The faithful real patch "
                      "does NOT resolve.",
        "rationale": "REJECT from (P1) alone, and from its ORDER content "
                     "specifically: `result.kept` is a permutation of "
                     "`other.filter (contains · = some false)` with the same "
                     "length and the same elements, so this rival is the one no "
                     "other here catches — a membership-only, length-only or "
                     "multiset-only reading of (P1) would ACCEPT it. (P2) holds "
                     "exactly, so the rejection is attributable solely to the "
                     "retained group's order. Refuted at `other = [1, 2]` with a "
                     "classifier reporting a definite NO for both: the rival's "
                     "retained group is `[2, 1]`, the spec's is `[1, 2]`. A sixth "
                     "distinct refutation point, and the only probe here whose two "
                     "candidates share one outcome class.",
        "witness": _w("fun n : Nat => if n = 1 then some false else "
                      "if n = 2 then some false else none",
                      "[1, 2]"),
    },
]


# ---------------------------------------------------------------------------
# NAGINI -> LEAN ACCOUNTING. The sibling battery carries 10 SPEC cases
# (2 soundness positives, 1 admissibility, 2 frame-mutation rivals, 5 uniqueness
# rivals) plus a 1-case AXIOM lane. It models the SAME purely-functional core —
# a three-way split of a finite ordered collection by a three-valued membership
# outcome into (retained, set-aside) — so the value/routing rivals port near
# 1:1, while the permission-flavoured classes are genuinely vacuous here.
#
#   sibling case (nagini)                         -> here                                  disposition
#   ------------------------------------------------------------------------------------------------------
#   pos-control-branch-reorder                    -> pos-control-branch-reorder            PORTED
#   pos-control-equality-ladder                   -> pos-control-equality-ladder           PORTED
#   admiss-self-call-singleton                    -> admiss-ground-mixed-collection       PORTED (was wrongly dropped)
#   frame-mutate-other-append                     -> (none)                                VACUOUS (no heap)
#   frame-mutate-other-index-assign               -> (none)                                VACUOUS (no heap)
#   weak-prepatch-fold-undecided-into-survivors   -> weak-prepatch-fold-undecided-into-kept   PORTED
#   weak-pending-always-empty                     -> weak-unresolved-always-empty          PORTED
#   weak-undecided-leaks-into-survivors           -> weak-undecided-leaks-into-kept        PORTED
#   weak-buckets-swapped                          -> weak-groups-swapped                   PORTED
#   weak-skip-first-element                       -> weak-skip-first-element               PORTED
#   AXIOM_TESTS (x1)                              -> (none)                                DROPPED (G-AX's lane)
#
# PORTED (both positives). The sibling's branch-reorder argument ("the outcome
#   classes are disjoint, so the routing order is irrelevant") re-expresses
#   directly as a permutation of the three-way dispatch arms; its equality-ladder
#   argument ("the spec is not pinned to the frozen if/elif token shape")
#   re-expresses as an explicit three-rung `if` ladder with the definite-member
#   rung written as a stated no-op. Unlike velvet — where `loom_solve` reproves
#   automatically — each positive here needed its proof re-closed against the
#   reshaped impl. Both were closed HONESTLY (permuted / restated loop lemma,
#   same induction, byte-identical theorem statement, no helper lemma, no
#   `sorry`) and both build clean. NEITHER positive was dropped for proof cost.
# ADDED (weak-kept-order-reversed). Not in the sibling: an AUDIT addition. All
#   five ported rivals get the retained group's CONTENTS wrong, so none of them
#   pins the ORDER half of (P1) — a reading of (P1) up to permutation would have
#   accepted every impl this battery rejected. The new rival selects exactly the
#   right candidates for both groups and only reverses the retained one, so it is
#   refuted solely by order (rival build exit 0, gold exit 1).
# PORTED (all 5 uniqueness rivals). The pre-change fold, the always-empty
#   set-aside group, the double-count leak, the exchanged groups and the
#   off-by-one port DIRECTLY onto the two postcondition conjuncts; their
#   refinement arguments carry over intact. Each is expressed as a loop-free
#   closed form over the two input binders, and each is refuted by a witness at
#   its OWN concrete `(contains, other)` point — checked out of band with two
#   real builds (elaborates against the rival, fails against gold). No witness
#   binds a hypothesis (the carrier computes), so none can be a forgery from an
#   inconsistent binder set and the gate's consistency probe has nothing to run.
# PORTED (admissibility). The sibling self-calls the modeled function on `[7]` to
#   show the read-only-input precondition admits a normal input. It is TRUE that
#   this bundle states no precondition — `correct_partitionByMembership` binds
#   `∀ (contains) (other)` with no hypothesis — but that is NOT a reason to drop
#   the lane, and an earlier revision of this manifest dropped it on exactly that
#   reasoning. The analogue on a TOTAL carrier is the obligation being
#   unsatisfiable at an F2P-shaped input, which a positive that discharges the
#   obligation AT THAT CONCRETE INPUT — by evaluation, as a `have`, before
#   closing the frozen obligation verbatim — tests directly. That is
#   `admiss-ground-mixed-collection`, discharged by `decide` at `other =
#   [2, 3, 4]` over a classifier mixing all three outcome classes: the
#   discriminating shape rather than an arbitrary point. It builds clean (exit
#   0), so the lane is EXPRESSIBLE here and this battery now tests
#   PRECOND-TOO-STRONG alongside SPEC-TOO-WEAK and SPEC-TOO-STRONG.
# VACUOUS (2 frame-mutation rivals). The sibling carries these as MANDATORY (its
#   self-declared #1 weakness class) because its input list is a heap object held
#   at HALF permission that an impl can illegally append to or index-assign into,
#   and the rejection then comes from the permission system rather than from a
#   value mismatch. Lean is referentially transparent: `other : List α` is an
#   immutable value, there is no heap, no aliasing, no fractional permission and
#   no `mut` binder on any input — so there is no read-only input to overwrite.
#   Per the porting map, no substitute is fabricated.
# VACUOUS (divergence). Not shipped, and here genuinely VACUOUS rather than a
#   known spec hole: `implementation_partitionByMembership` is a total Lean `def`
#   whose only loop is a `for` over a finite list, so a non-terminating rival
#   cannot be written at all — the situation the corpus-wide termination-semantics finding records
#   for velvet under `loom.semantics.termination "partial"` (a rival that
#   satisfies every clause vacuously and verifies) has no analogue on this
#   backend. The sibling carries no `diverge-*`/`nonterm-*` case either, so
#   nothing was dropped in the port.
# DROPPED (AXIOM_TESTS x1). The sibling's axiom lane probes the range of its
#   three-valued verdict callee and the fidelity of its two reference folds. Here
#   the three-valued outcome is an INPUT PARAMETER, so the bundle's `axioms`
#   region is a skip stub, the proof consumes no callee contract, and the real
#   callee is exercised by G-CONF. In any case this gate ignores AXIOM_TESTS.
#
# COVERAGE. The single obligation `correct_partitionByMembership` is DEFENDED (2
# soundness positives, both proofs closed, plus 1 admissibility positive showing
# the obligation is satisfiable at the F2P-shaped mixed-class point) and ATTACKED
# (6 `expect="reject"` rivals). BOTH independent top-level conjuncts are attacked:
# (P1) `result.kept = other.filter (contains · = some false)` by
# weak-undecided-leaks-into-kept (over-count), weak-groups-swapped (wrong
# selection), weak-prepatch-fold (fold-in), weak-skip-first-element (boundary)
# and weak-kept-order-reversed (ORDER — right elements, wrong sequence, the one
# defect a permutation-blind reading of (P1) would admit); (P2)
# `result.unresolved = other.filter (contains · = none)` by
# weak-unresolved-always-empty (empty), weak-groups-swapped, weak-prepatch-fold
# and weak-skip-first-element.
#
# BOTH input binders are genuinely varied by the reject witnesses — the failure
# mode the porting map warns about (a binder every witness holds at one value)
# is explicitly avoided:
#   * `other`: `[2, 7]`, `[5]`, `[3, 4]`, `[9]`, `[6, 8]`, `[1, 2]` — SIX distinct
#     points, lengths 1 and 2, with the discriminating candidate at index 0 in
#     one case and index 1 in others (plus `[2, 3, 4]` at length 3 for the
#     admissibility positive);
#   * `contains`: six DISTINCT classifiers, jointly covering every outcome class
#     and several combinations — {yes, undetermined}, {undetermined only},
#     {no, undetermined}, {no only}, {no, yes}, {no, no}. In particular three
#     rivals are
#     refuted at points with NO undetermined candidate at all, so a rival that
#     mishandled only the definite-negative or only the definite-yes class cannot
#     hide behind the undetermined-heavy probes.
# No two rivals share a refutation point, so each near-miss (leak vs
# always-empty vs pre-change fold — all three agree with the frozen behaviour
# wherever nothing is undetermined) demonstrates the exact sub-domain its
# rationale claims. No frame/permission rival is fabricated; for the divergence
# class see the corpus-wide termination-semantics finding (nothing to ship here — that finding is
# recorded against velvet's `partial` bundles, and this backend has no analogue).
#
# AXIOM_TESTS: empty. The axiom lane is G-AX's job; this gate ignores it.
AXIOM_TESTS = []
