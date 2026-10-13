"""properties.py — G-PBT falsification battery for psf__requests-1921 (lean).

NOT a Lean file; a manifest the G-PBT gate executes. Each SPEC case is a full
``Solution.lean`` variant that shares the FROZEN spec byte-for-byte (region
surgery: only text inside the ``-- impl-start`` / ``-- impl-end`` region — and,
for a case that legitimately re-proves, inside the ``-- proof-start`` /
``-- proof-end`` region — is changed, so ``markers.same_spec`` holds and the
single ``theorem correct_effectiveSetting`` STATEMENT stays byte-identical).
``expect="verify"`` passes iff (in scope AND the file elaborates with the
obligation closed, no ``sorry``/``admit``/``native_decide`` and no new
``axiom``/``theorem``); ``expect="reject"`` passes iff (in scope AND it does NOT
verify AND the case's refutation ``witness`` holds of the rival while FAILING on
the frozen solution).

PORT NOTE. This is a PORT of the nagini falsification battery
(``../nagini/properties.py``) onto this backend's carrier. The nagini bundle
models an imperative ``effective_collection`` over a ``PSeq[int]`` carrier where
each position holds an integer sentinel (``none_val()`` / ``absent()``) and pins
every position against a GROUNDED deep model (nagini's ``combined``). This Lean
bundle models the SAME single purely-functional core — merging a per-request
key/value mapping over a session-level mapping of defaults into the single
effective mapping, honoring the null sentinel so that no null-valued entry
survives — over a ``List (String × Option String)`` carrier. The grounding is
the SAME: the postcondition equates ``result`` to a fully-unfolded pure model
``effective req ses`` (no opaque answer key to echo). The nagini
frame/permission-mutation class is VACUOUS here (referential transparency — see
``assessment``).

DEFENDED SURFACE (one modeled behavior; ONE top-level clause).
``problem_spec_effectiveSetting req ses result`` pins EXACTLY:

  * (C0)  ``result = effective req ses`` — the result IS the session defaults
    overlaid by the per-request entries (request wins on shared keys, in place),
    with every key the request maps to the null sentinel removed, and then with
    every remaining null-valued entry removed. The headline guarantee — no
    null-valued entry survives, regardless of whether the null came from the
    per-request mapping or from the session defaults — is the last conjunct of
    ``effective`` (the final ``filter (·.2.isSome)``).

The BEHAVIOURAL DISCRIMINATOR (the fix): after applying the per-request entries
and honoring request-nulled keys, a FINAL pass must drop every remaining
null-valued entry — the entries the SESSION defaults mapped to null, which the
request never mentions and so the request-keyed null-drop never touches. The
pre-fix behavior omitted that final pass; the ``prepatch-no-final-nulldrop``
rival below IS that pre-fix behavior, and on a session-only null it leaves a
null-valued entry in the result.

BINDER STRUCTURE. The spec predicate has TWO input binders: ``req`` (the
per-request mapping) and ``ses`` (the session defaults). Both are load-bearing
and both are varied across the reject witnesses (see the point-spread block at
the bottom): some witnesses hold ``req = []`` (attacking session-side handling),
others give ``req`` a real override or a request-side null, and ``ses`` ranges
over real / null values on shared and unshared keys. The five reject witnesses
probe five DISTINCT input tuples (``pts=5``), one of which repeats a key inside
``req`` — the only shape on which a key-keyed drop and a value-keyed drop can
disagree.

ADVERSARIAL READ of the case classes on this carrier:

  * FRAME / PERMISSION MUTATION — VACUOUS. The nagini sibling holds its two
    inputs at ``Acc(.,1/2)`` and makes an illegal-write rival MANDATORY there —
    the persistent session mapping is shared across requests and must not be
    mutated. On this referentially transparent carrier ``req`` and ``ses`` are
    immutable values: there is no ``mut`` input binder, no aliasing, no
    read-only cell to overwrite, so the class is vacuous. No substitute probe is
    fabricated (porting map: vacuous here). The underlying real-code concern
    (a faithful merge must not mutate its session argument) is still a live
    F2P/PASS_TO_PASS constraint, but it is unobservable on this pure carrier.

  * UNGROUNDED-ORACLE ECHO — VACUOUS. ``effective`` is a GROUNDED pure model (a
    fully-unfolded function of ``req``/``ses``, not an opaque answer key), so
    there is no wrong echo to build. In its place the battery carries an honest
    cheapest-implementation POSITIVE CONTROL that must verify (else the spec
    would reject its own grounded model — SPEC-TOO-STRONG). Ports the nagini
    ``oracle-direct-positive``. That positive is definitionally ``effective``, so
    it closes by one ``rfl`` and probes the spec's UNFOLDING only; the two
    reshape positives added by the audit carry the list-algebra content (a filter
    commutation and a fold/filter fusion), so the soundness lane does not rest on
    a single definitional case.

  * PARTIAL-DOMAIN / VALUE — APPLIES. Rivals correct on part of the domain but
    diverging where the fix bites: omitting the final null-drop entirely (the
    pre-fix bug, a session-only null survives); skipping the null-drop for the
    FIRST entry only (the universal equality catches the carve-out a
    "most positions" fuzzer misses); over-dropping a key the session nulled even
    when the request overrides it with a real value; and swapping the override
    precedence (session wins instead of request).

WITNESSES. On a tactic-proof backend "did not verify" is the DEFAULT outcome of
reshaping an implementation — the frozen proof is tuned to the frozen form — so
a rejection alone attributes nothing to the spec. Every ``expect="reject"`` case
therefore carries a Lean snippet that states the spec predicate directly at one
CONCRETE input and closes by ``decide`` (the ``Id.run do`` / ``for`` loop and
the pure model both reduce to normal forms on ground ``List`` literals). Each
witness binds NOTHING in its head (all inputs are ground list literals), so there
are no hypotheses whose joint satisfiability could be in question — the carrier
is fully transparent at these inputs, so no conditioning is needed. Each was
checked with two real ``lake env lean`` builds to HOLD of its rival and to FAIL
on the frozen solution, so it discriminates rather than asserting a tautology.

REFINEMENT (why a verifying rival would be a true verify-but-not-resolve break).
Each reject case's ``refinement`` argues that its faithful real counterpart is a
merge that mishandles the null sentinel or the override precedence, so on the
issue's exact scenario (a session default mapped to null) the emitted mapping
carries a null-valued entry that then gets sent, or drops/keeps the wrong entry,
and the F2P observable (the null-mapped default is NOT sent) fails — so the
faithful patch would NOT resolve.

AXIOM lane: EMPTY here. The bundle declares no ``opaque`` callee and consumes no
``axiom`` (the merge is modeled deeply as list operations); the axiom lane
belongs to G-AX, and the nagini ``AXIOM_TESTS`` (also empty there) are dropped.
"""
from pathlib import Path

INSTANCE = "psf__requests-1921"
BACKEND = "lean"

_BASE = (Path(__file__).parent / "Solution.lean").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# ---- region anchors (each unique inside Solution.lean; verified at load) ----
# The final null-drop pass in the impl loop body (the discriminating step of the
# fix): after the overlay and the request-keyed null-drop, keep only entries that
# carry a real value. Every impl reshape below lands entirely inside
# `-- impl-start`/`-- impl-end`.
_FINAL = "  merged := merged.filter (fun q => q.2.isSome)\n"

# The initial accumulator + the overlay loop (impl region). Reordering these two
# flips the override precedence.
_INIT = "  let mut merged : List Entry := ses\n"
_OVLOOP = "  for p in req do\n    merged := dictSet merged p.1 p.2\n"

# The whole impl body (for the oracle-direct positive control), so it can be
# replaced by the pure model as one unit while the theorem STATEMENT is untouched.
_IMPL_BODY = """def implementation_effectiveSetting
    (req ses : List Entry) : List Entry := Id.run do
  -- Start from the session defaults, then let the per-request entries override.
  let mut merged : List Entry := ses
  for p in req do
    merged := dictSet merged p.1 p.2
  -- Honor keys the request maps to the null sentinel.
  for p in req do
    if p.2.isNone then
      merged := merged.filter (fun q => q.1 != p.1)
  -- Keep only entries that carry a real value.
  merged := merged.filter (fun q => q.2.isSome)
  return merged"""

_IMPL_DIRECT = """def implementation_effectiveSetting
    (req ses : List Entry) : List Entry :=
  (dropNulledKeys req (overlay ses req)).filter (fun q => q.2.isSome)"""

# The request-keyed null-drop loop (impl region), as ONE unit. Deleting it is the
# "the final isSome-filter subsumes this pass" reshape. See
# `drop-request-keyed-null-pass`: on THIS carrier that reshape is not correct, so
# it is a rival, not a positive.
_NULLLOOP = ("  -- Honor keys the request maps to the null sentinel.\n"
             "  for p in req do\n"
             "    if p.2.isNone then\n"
             "      merged := merged.filter (fun q => q.1 != p.1)\n")

# ---- two CORRECT reshapes that must verify (SPEC-TOO-STRONG probes) ----
# Both keep the theorem STATEMENT byte-identical and reprove inside the proof
# region with no new axiom/lemma/sorry. The shared `forIn -> foldl` bridges are
# the frozen proof's own; each adds one list-algebra step about ITS reshape.
_LOOP1 = """  have loop1 : ∀ (xs : List Entry) (init : List Entry),
      (Id.run (forIn xs init (fun (p : Entry) (r : List Entry) =>
          (do
            pure PUnit.unit
            pure (ForInStep.yield (dictSet r p.1 p.2)) : Id (ForInStep (List Entry))))))
      = xs.foldl (fun acc p => dictSet acc p.1 p.2) init := by
    intro xs
    induction xs with
    | nil => intro init; rfl
    | cons a as ih =>
      intro init
      rw [List.forIn_cons, List.foldl_cons]
      simp only [Id.run, bind] at ih ⊢
      rw [ih]
"""
_LOOP2 = """  have loop2 : ∀ (xs : List Entry) (init : List Entry),
      (Id.run (forIn xs init (fun (p : Entry) (r : List Entry) =>
          (if p.2.isNone = true then
            (do
              pure PUnit.unit
              pure (ForInStep.yield (List.filter (fun q => q.1 != p.1) r)))
          else
            (do
              pure PUnit.unit
              pure (ForInStep.yield r)) : Id (ForInStep (List Entry))))))
      = xs.foldl (fun acc p => if p.2.isNone then acc.filter (fun q => q.1 != p.1) else acc) init := by
    intro xs
    induction xs with
    | nil => intro init; rfl
    | cons a as ih =>
      intro init
      rw [List.forIn_cons, List.foldl_cons]
      simp only [Id.run, bind] at ih ⊢
      by_cases h : a.2.isNone = true
      · simp only [h, if_true, ih]
      · simp only [h, ih, Bool.false_eq_true, if_false]
"""

# (E-a) Drop the null-valued entries FIRST, then honor the request-nulled keys.
# Correct because the two filters commute; the reordering is not definitional, so
# `rfl` alone does NOT close it — the `comm` step is the real content.
_IMPL_FILTER_FIRST = """def implementation_effectiveSetting
    (req ses : List Entry) : List Entry := Id.run do
  -- Start from the session defaults, then let the per-request entries override.
  let mut merged : List Entry := ses
  for p in req do
    merged := dictSet merged p.1 p.2
  -- Keep only entries that carry a real value FIRST ...
  merged := merged.filter (fun q => q.2.isSome)
  -- ... then honor keys the request maps to the null sentinel.
  for p in req do
    if p.2.isNone then
      merged := merged.filter (fun q => q.1 != p.1)
  return merged"""

_PROOF_FILTER_FIRST = ("""  intro req ses
  unfold problem_spec_effectiveSetting implementation_effectiveSetting effective
    dropNulledKeys overlay
""" + _LOOP1 + _LOOP2 + """  have comm : ∀ (xs : List Entry) (l : List Entry),
      xs.foldl (fun acc p =>
          if p.2.isNone then acc.filter (fun q => q.1 != p.1) else acc)
        (List.filter (fun q => q.2.isSome) l)
      = List.filter (fun q => q.2.isSome)
          (xs.foldl (fun acc p =>
            if p.2.isNone then acc.filter (fun q => q.1 != p.1) else acc) l) := by
    intro xs
    induction xs with
    | nil => intro l; rfl
    | cons a as ih =>
      intro l
      rw [List.foldl_cons, List.foldl_cons]
      by_cases h : a.2.isNone = true
      · rw [if_pos h, if_pos h, ← ih]
        congr 1
        rw [List.filter_filter, List.filter_filter]
        apply List.filter_congr
        intro q _
        exact Bool.and_comm _ _
      · rw [if_neg (by simpa using h), if_neg (by simpa using h), ih]
  simp only [Id.run, bind] at loop1 loop2 ⊢
  rw [loop1, loop2, comm]
  rfl
""")

# (E-b) Collapse BOTH final passes into ONE fused filter: keep an entry iff it
# carries a real value AND the request does not map its key to the null sentinel.
# Replaces a loop by a membership test, so nothing here is definitional.
_IMPL_FUSED = """def implementation_effectiveSetting
    (req ses : List Entry) : List Entry := Id.run do
  -- Start from the session defaults, then let the per-request entries override.
  let mut merged : List Entry := ses
  for p in req do
    merged := dictSet merged p.1 p.2
  -- One fused pass: keep an entry iff it carries a real value AND the request
  -- does not map its key to the null sentinel.
  merged := merged.filter
    (fun q => q.2.isSome && !(req.any (fun p => p.1 == q.1 && p.2.isNone)))
  return merged"""

_PROOF_FUSED = ("""  intro req ses
  unfold problem_spec_effectiveSetting implementation_effectiveSetting effective
    dropNulledKeys overlay
""" + _LOOP1 + """  have key : ∀ (xs : List Entry) (l : List Entry),
      List.filter (fun q => q.2.isSome)
        (xs.foldl (fun acc p =>
          if p.2.isNone then acc.filter (fun q => q.1 != p.1) else acc) l)
      = List.filter
          (fun q => q.2.isSome && !(xs.any (fun p => p.1 == q.1 && p.2.isNone))) l := by
    intro xs
    induction xs with
    | nil => intro l; simp
    | cons a as ih =>
      intro l
      rw [List.foldl_cons]
      simp only [List.any_cons]
      by_cases h : a.2.isNone = true
      · rw [if_pos h, ih, List.filter_filter]
        apply List.filter_congr
        intro q _
        simp only [h, Bool.and_true, Bool.not_or, bne]
        by_cases hq : q.1 = a.1
        · simp only [hq, beq_self_eq_true, Bool.not_true, Bool.and_false,
                     Bool.false_and]
        · have h1 : (q.1 == a.1) = false := beq_eq_false_iff_ne.mpr hq
          have h2 : (a.1 == q.1) = false := beq_eq_false_iff_ne.mpr (Ne.symm hq)
          simp only [h1, h2, Bool.not_false, Bool.and_true, Bool.true_and]
      · have ha : a.2.isNone = false := Bool.eq_false_iff.mpr h
        rw [if_neg (by simpa using h), ih]
        apply List.filter_congr
        intro q _
        simp only [ha, Bool.and_false, Bool.false_or]
  simp only [Id.run, bind] at loop1 ⊢
  rw [loop1, key]
  rfl
""")

# The frozen proof body (from the intro line to just before `-- proof-end`). The
# oracle-direct positive replaces the whole body with the trivial `rfl` proof its
# reshaped (definitionally-equal-to-`effective`) impl admits. Statement stays
# byte-identical (only the tactic body changes); no new axiom/lemma.
_PROOF_BODY = _BASE[_BASE.index("  intro req ses\n"):_BASE.index("-- proof-end")]
_PROOF_DIRECT = (
    "  intro req ses\n"
    "  unfold problem_spec_effectiveSetting implementation_effectiveSetting "
    "effective\n"
    "  rfl\n")

# The frozen proof's intro line — unique in the file — so the admissibility
# positive can prepend a ground `have` without touching the theorem STATEMENT or
# the spec view; the frozen tactic body then closes the ∀ obligation as before.
_P_INTRO = "  intro req ses\n"


def _witness(req, ses):
    """State the spec predicate directly at one concrete (req, ses) and refute
    it by `decide`. Binds nothing in the head, so no consistency question."""
    return (
        f"example : ¬ problem_spec_effectiveSetting {req} {ses}\n"
        f"    (implementation_effectiveSetting {req} {ses}) := by\n"
        "  unfold problem_spec_effectiveSetting\n"
        "  decide")


SPEC_TESTS = [
    # =====================================================================
    # SOUNDNESS POSITIVE — a structurally different CORRECT impl that MUST
    # verify, else SPEC-TOO-STRONG. Keeps the `correct_effectiveSetting`
    # statement byte-identical.
    # =====================================================================
    {
        "id": "oracle-direct-positive",
        "kind": "soundness",
        "expect": "verify",
        # The honest cheapest impl: build the result by the pure model directly
        # (overlay, then honor request-nulled keys, then drop remaining nulls)
        # instead of the imperative `Id.run do` loop. Definitionally equal to the
        # grounded model, so the proof is `intro; unfold; rfl` — no new
        # axiom/lemma, statement byte-identical. (Verified: real build.)
        "module": _swap(
            _swap(_BASE, _IMPL_BODY, _IMPL_DIRECT),
            _PROOF_BODY, _PROOF_DIRECT),
        "rationale": "`effective` is a GROUNDED pure model (a fully-unfolded "
                     "function of req/ses, not an opaque answer key), so there is "
                     "no wrong echo to build. The honest cheapest impl computes "
                     "the model directly; it MUST verify, else the spec would "
                     "reject its own grounded model (SPEC-TOO-STRONG). The impl is "
                     "definitionally `effective req ses`, so the reshaped proof "
                     "closes by `intro; unfold; rfl`; statement byte-identical, no "
                     "new axiom/lemma. Ports nagini's oracle-direct-positive.",
    },

    # =====================================================================
    # SOUNDNESS POSITIVE (added by audit) — reorder the two final passes: drop
    # the null-valued entries BEFORE honoring the request-nulled keys. Correct
    # (the two filters commute) and NOT definitionally equal to the frozen impl,
    # so `rfl` alone does not close it — the reproof carries a real `comm` step.
    # This is the "structurally different correct impl whose proof stays near the
    # frozen one" the frozen battery's only positive did NOT provide: the
    # oracle-direct positive is definitionally `effective`, so it costs one `rfl`
    # and exercises no list algebra. (Verified: real build, exit 0.)
    # =====================================================================
    {
        "id": "reshape-filter-before-nulldrop-positive",
        "kind": "soundness",
        "expect": "verify",
        "module": _swap(
            _swap(_BASE, _IMPL_BODY, _IMPL_FILTER_FIRST),
            _PROOF_BODY, _PROOF_FILTER_FIRST),
        "rationale": "a faithful CORRECT reshape that must verify, else "
                     "SPEC-TOO-STRONG. It applies the two final passes in the "
                     "opposite order (drop null-valued entries first, then honor "
                     "the request-nulled keys); the result is the same because the "
                     "two filters commute, which is exactly what the reproof's "
                     "`comm` step establishes. Unlike the oracle-direct positive "
                     "this is NOT definitionally `effective` — `rfl` alone fails on "
                     "it — so it is the positive that actually exercises the spec's "
                     "list algebra rather than its unfolding. Statement "
                     "byte-identical; no new axiom/lemma/sorry.",
    },

    # =====================================================================
    # SOUNDNESS POSITIVE (added by audit) — collapse BOTH final passes into ONE
    # fused filter keyed off a membership test on `req`. A larger reshape than
    # the reorder above (a loop becomes an `any`), still correct, still provable
    # with no new declaration. Replaces the nagini `pos-control-branch-reorder-
    # fused` the port dropped: the sibling's fused positive DOES have a
    # counterpart here, and it lands. (Verified: real build, exit 0.)
    # =====================================================================
    {
        "id": "reshape-fused-filter-positive",
        "kind": "soundness",
        "expect": "verify",
        "module": _swap(
            _swap(_BASE, _IMPL_BODY, _IMPL_FUSED),
            _PROOF_BODY, _PROOF_FUSED),
        "rationale": "a second faithful CORRECT reshape that must verify, else "
                     "SPEC-TOO-STRONG. It fuses the request-nulled-key pass and the "
                     "null-valued-entry pass into a single filter whose predicate "
                     "tests the request mapping by membership (`req.any`) instead of "
                     "iterating it, so a loop is replaced by a decision procedure. "
                     "The reproof's `key` step is the substantive content: a "
                     "keyed-drop fold followed by an isSome-filter equals the single "
                     "fused filter. This is the direct counterpart of nagini's "
                     "pos-control-branch-reorder-fused, which the port recorded as "
                     "undroppable-but-dropped; it is expressible and it verifies. "
                     "Statement byte-identical; no new axiom/lemma/sorry.",
    },

    # =====================================================================
    # ADMISSIBILITY — confirm the obligation is SATISFIABLE (non-vacuous) at a
    # normal, F2P-shaped input. The frozen theorem carries no precondition, so the
    # nagini precondition-admission self-call re-expresses as: discharge the spec
    # predicate by evaluation at the issue's exact scenario (a session default
    # mapped to the null sentinel plus a real default, request empty) as a `have`,
    # then close the frozen obligation verbatim. Nothing is assumed: no new
    # declaration, statement byte-identical, ground instance is a `have` prepended
    # to the existing tactic body. (Verified: real build.)
    # =====================================================================
    {
        "id": "admiss-f2p-shaped",
        "kind": "admissibility",
        "expect": "verify",
        "module": _swap(
            _BASE, _P_INTRO,
            '  have _ground : problem_spec_effectiveSetting [] '
            '[("a", none), ("k", some "v")]\n'
            '      (implementation_effectiveSetting [] '
            '[("a", none), ("k", some "v")]) := by\n'
            "    unfold problem_spec_effectiveSetting\n"
            "    decide\n"
            + _P_INTRO),
        "rationale": "the obligation is discharged at the issue's exact F2P shape "
                     "(request empty; session defaults map key `a` to the null "
                     "sentinel and key `k` to a real value) by evaluation as a "
                     "`have`, then the frozen obligation is closed verbatim. "
                     "Verifies (else the modeled behavior would be unsatisfiable at "
                     "exactly a normal F2P input — the analogue of "
                     "PRECOND-TOO-STRONG). Nothing is assumed: no new declaration, "
                     "statement byte-identical, ground instance is a `have` in the "
                     "existing tactic body. Ports nagini's "
                     "admissibility-f2p-shaped-self-call.",
    },

    # =====================================================================
    # UNIQUENESS / SPEC-TOO-WEAK rivals — wrong impls sharing the frozen spec
    # that MUST be rejected. Each carries (a) the refinement argument that its
    # faithful real patch would NOT resolve the F2P, and (b) a witness pinning the
    # violation at one concrete input.
    # =====================================================================

    # ---- the fix itself: omit the final null-drop pass (pre-fix behavior) ----
    {
        "id": "prepatch-no-final-nulldrop",
        "kind": "uniqueness",
        "expect": "reject",
        # Pre-fix behavior: drop the FINAL pass that removes remaining null-valued
        # entries. A key the SESSION defaults map to null (which the request never
        # mentions) then survives with its null value.
        "module": _swap(_BASE, _FINAL, ""),
        "refinement": "this IS the pre-fix behavior: without the final null-drop a "
                      "key the session defaults map to the null sentinel — which "
                      "the request never mentions, so the request-keyed null-drop "
                      "never touches it — survives with its null value. A faithful "
                      "patch omitting that pass sends the null-mapped default; the "
                      "F2P observable (a session default set to null is NOT sent) "
                      "then fails, so the faithful patch would NOT resolve.",
        "rationale": "REJECT from C0: the spec pins `result = effective req ses`, "
                     "whose last conjunct drops every remaining null-valued entry, "
                     "but the rival leaves the session-only null in place. Refuted "
                     "at req=[], ses=[(\"a\", none)] where the rival keeps "
                     "[(\"a\", none)] but effective yields [].",
        "witness": _witness("[]", '[("a", none)]'),
    },

    # ---- skip the final null-drop for the FIRST entry only ----
    {
        "id": "first-entry-carveout",
        "kind": "uniqueness",
        "expect": "reject",
        # Correct on every entry EXCEPT the first: the final null-drop is applied
        # only to the tail, so a null-valued FIRST entry survives. A "most
        # positions" fuzzer would miss this; the universal equality catches it.
        "module": _swap(
            _BASE, _FINAL,
            "  merged := (merged.take 1) ++ "
            "(merged.drop 1).filter (fun q => q.2.isSome)\n"),
        "refinement": "skips the final null-drop for the FIRST resulting entry "
                      "while applying it to the rest. A faithful patch that filtered "
                      "all but the first entry would still send a null-mapped "
                      "default when it lands first; the F2P observable can fall on "
                      "that entry, so the faithful patch would NOT resolve.",
        "rationale": "REJECT from C0 at the first entry: the spec pins "
                     "`result = effective req ses` (all null entries dropped), but "
                     "the rival preserves a null-valued head. Refuted at req=[], "
                     "ses=[(\"a\", none), (\"k\", some \"v\")] where the rival keeps "
                     "the null head [(\"a\", none), (\"k\", some \"v\")] but "
                     "effective yields [(\"k\", some \"v\")]. Distinct from the "
                     "prepatch rival in the OTHER direction (measured, both ways, "
                     "with real builds): this rival AGREES with `effective` at "
                     "req=[], ses=[(\"k\", some \"v\"), (\"a\", none)] — the null "
                     "entry is not first there, so the carve-out never fires — "
                     "whereas the prepatch rival is refuted at that same input. It "
                     "is NOT the case that this rival needs a two-entry input: the "
                     "null entry is also first in the prepatch witness's "
                     "single-entry ses=[(\"a\", none)], so it is refuted there too. "
                     "The carve-out is what the two-entry witness above isolates: "
                     "the tail IS filtered, only the head survives.",
        "witness": _witness("[]", '[("a", none), ("k", some "v")]'),
    },

    # ---- over-drop: remove a key the session nulled even when request overrides ----
    {
        "id": "over-drop-session-null",
        "kind": "uniqueness",
        "expect": "reject",
        # Too-aggressive: also drop any key the SESSION mapped to null, even when
        # the request explicitly overrides it with a real value (request should
        # win). Strips a legitimately-set per-request entry.
        "module": _swap(
            _BASE, _FINAL,
            "  merged := (merged.filter (fun q => q.2.isSome)).filter "
            "(fun q => !(ses.any (fun p => p.1 == q.1 && p.2.isNone)))\n"),
        "refinement": "drops a key whenever the SESSION default was null — even "
                      "when the request explicitly overrides it with a real value, "
                      "where the request must win. A faithful patch stripping such "
                      "an overridden entry would lose a header the caller "
                      "legitimately set for this request; the PASS_TO_PASS "
                      "request-construction suite would lose a header it must send, "
                      "so the faithful patch would NOT resolve.",
        "rationale": "REJECT from C0: at a key the session maps to null but the "
                     "request overrides with a real value, the overlay makes the "
                     "effective value the real request value (request wins), so "
                     "`effective` keeps it, but the rival drops it. Refuted at "
                     "req=[(\"k\", some \"v\")], ses=[(\"k\", none)] where the rival "
                     "yields [] but effective yields [(\"k\", some \"v\")]. This "
                     "witness varies `req` off empty (a real override) — the binder "
                     "the null-side rivals hold at [].",
        "witness": _witness('[("k", some "v")]', '[("k", none)]'),
    },

    # ---- drop the request-keyed null pass, keeping only the final filter ----
    {
        "id": "drop-request-keyed-null-pass",
        "kind": "uniqueness",
        "expect": "reject",
        # The "the final isSome-filter subsumes the request-keyed pass" reshape.
        # It does NOT: the overlay applies request entries IN ORDER with in-place
        # update, so when the request maps a key to the null sentinel and then to
        # a real value, the overlay's surviving value for that key is the REAL
        # one — the final filter keeps it, while the request-keyed pass would
        # still remove the key outright. Wrong, not merely reshaped.
        "module": _swap(_BASE, _NULLLOOP, ""),
        "refinement": "keeps only the value-keyed drop and omits the key-keyed "
                      "one. A faithful patch that dropped the key-keyed pass would "
                      "still send a key the caller explicitly mapped to the null "
                      "sentinel whenever the caller's own mapping also supplies a "
                      "real value for that key later in order; the F2P observable "
                      "(a key mapped to null is NOT sent) then fails on that key, "
                      "so the faithful patch would NOT resolve.",
        "rationale": "REJECT from C0: `effective` removes every key the request "
                     "maps to null via `dropNulledKeys req`, which is keyed off the "
                     "KEY and so fires regardless of what value survived the "
                     "overlay; the rival only filters on the surviving VALUE. "
                     "Refuted at req=[(\"k\", none), (\"k\", some \"v\")], ses=[] "
                     "where the overlay leaves [(\"k\", some \"v\")] — which the "
                     "rival keeps — but effective yields [] because `k` is a "
                     "request-nulled key. MEASURED sub-domain (exhaustive shadow "
                     "enumeration, keys {a,b}, values {none,x,y}, |req|,|ses| ≤ 2, "
                     "session mappings unique-key): the rival agrees with "
                     "`effective` on all 625 inputs whose `req` has unique keys and "
                     "diverges on 100 of the 450 whose `req` repeats a key — so it "
                     "is a genuine partial-domain rival whose divergence needs a "
                     "repeated key in `req`, which is why this witness is the only "
                     "one in the battery with a two-entry `req`.",
        "witness": _witness('[("k", none), ("k", some "v")]', "[]"),
    },

    # ---- override precedence flipped: session wins instead of request ----
    {
        "id": "precedence-flipped",
        "kind": "uniqueness",
        "expect": "reject",
        # Overlay the SESSION defaults on top of the request (session wins on
        # shared keys) instead of the request on top of the session.
        "module": _swap(
            _swap(_BASE, _INIT, "  let mut merged : List Entry := req\n"),
            _OVLOOP,
            "  for p in ses do\n    merged := dictSet merged p.1 p.2\n"),
        "refinement": "flips the override precedence: the session default wins on a "
                      "shared key instead of the per-request value. A faithful patch "
                      "with reversed precedence would ignore a caller's per-request "
                      "override and send the session default instead; the F2P/"
                      "PASS_TO_PASS suites pin request-wins semantics, so the "
                      "faithful patch would NOT resolve.",
        "rationale": "REJECT from C0: on a key present in both mappings the spec "
                     "pins the request value (request wins in `overlay ... req`), "
                     "but the rival keeps the session value. Refuted at "
                     "req=[(\"k\", some \"b\")], ses=[(\"k\", some \"a\")] where the "
                     "rival yields [(\"k\", some \"a\")] but effective yields "
                     "[(\"k\", some \"b\")]. Both binders are non-empty here, "
                     "exercising a shared-key collision.",
        "witness": _witness('[("k", some "b")]', '[("k", some "a")]'),
    },
]

# ---------------------------------------------------------------------------
# Nagini -> lean accounting. The sibling battery has 7 SPEC cases (1 frame
# mutation, 1 soundness oracle-positive, 1 soundness pos-control reorder, 1
# admissibility, 3 uniqueness/partial-domain rivals) plus an EMPTY AXIOM lane.
# This bundle models the SAME single purely-functional core (the effective-
# mapping merge) and re-expresses the sibling's non-vacuous cases. The spec here
# has a SINGLE top-level clause (result = effective req ses), so per-clause
# coverage is one clause attacked by five rivals varying both binders, and
# defended by three verifying positives (one definitional, two that reprove).
#
#   sibling case                              -> here
#   -----------------------------------------------------------------------
#   frame-mutation-write-session              -> (none)   VACUOUS (pure carrier)
#   oracle-direct-positive                    -> oracle-direct-positive   PORTED
#   pos-control-branch-reorder-fused          -> reshape-fused-filter-positive
#                                                AND reshape-filter-before-
#                                                nulldrop-positive          PORTED
#   admissibility-f2p-shaped-self-call        -> admiss-f2p-shaped        RE-EXPR
#   partial-domain-prepatch-rv-keyed-drop     -> prepatch-no-final-nulldrop PORTED
#   partial-domain-first-element-no-drop      -> first-entry-carveout      PORTED
#   over-drop-real-request-override           -> over-drop-session-null    PORTED
#   (none)                                    -> precedence-flipped        ADDED
#   (none)                                    -> drop-request-keyed-null-pass ADDED
#   AXIOM_TESTS (0)                           -> (none)   DROPPED (G-AX)
#
# VACUOUS (frame-mutation-write-session): the sibling makes an illegal-write-to-
#   read-only-session rival MANDATORY because its inputs are held at Acc(.,1/2).
#   On this referentially transparent carrier req/ses are immutable values — no
#   `mut` input, no aliasing, no read-only cell to overwrite — so the class is
#   vacuous. The underlying concern (a faithful merge must not mutate its shared
#   session argument, else PASS_TO_PASS's repeated-request suite breaks) is real
#   but unobservable on a pure carrier; no substitute probe is fabricated.
# PORTED (pos-control-branch-reorder-fused) — CORRECTED BY AUDIT. An earlier
#   revision of this manifest recorded this sibling case as DROPPED, on two
#   claims. BOTH were measured false with real builds:
#     (i) it claimed the reshape "dropping the now-redundant request-keyed null
#         loop, since the final isSome-filter subsumes it" is OBSERVATIONALLY
#         CORRECT. It is not, on this carrier. The overlay applies request
#         entries in order with in-place update, so a request that maps a key to
#         the null sentinel and LATER to a real value leaves a real value for
#         that key; the final value-keyed filter keeps it, while `dropNulledKeys`
#         removes the key outright. That reshape is a WRONG impl, and it now
#         ships as the reject case `drop-request-keyed-null-pass` with a witness
#         that discriminates it from gold. A positive control asserting it
#         correct would have been a false soundness claim.
#     (ii) it claimed a correct reshape's proof "requires a genuinely new lemma"
#         and so had to be dropped per SPEC_GUIDE. Two such reshapes are now
#         shipped as verifying positives — `reshape-filter-before-nulldrop-
#         positive` (the two final passes reordered; needs only that the two
#         filters commute) and `reshape-fused-filter-positive` (both passes fused
#         into one membership-keyed filter). Each reproves INSIDE the proof
#         region with `have` steps and no new top-level declaration, so no new
#         lemma is introduced and no obligation is weakened; the theorem
#         statement stays byte-identical. The real obstacle was a tactic gap, not
#         an expressibility limit, and a tactic gap is not a reason to drop a
#         case.
#   Net effect: the battery no longer rests its soundness lane on a single
#   positive that is definitionally `effective` (and so closes by one `rfl`,
#   exercising the spec's unfolding but none of its list algebra).
# ADDED (precedence-flipped): attacks the override-precedence facet of the single
#   clause (request-wins on shared keys), varying BOTH binders to a shared-key
#   collision — a facet none of the ported null-handling rivals exercise. Not a
#   fabricated behavior: it is a real, load-bearing aspect of `effective`.
#
# POINT SPREAD. The five reject witnesses probe five DISTINCT input tuples
# (pts=5):
#   (req, ses) =
#     ([], [("a", none)])                     prepatch-no-final-nulldrop
#     ([], [("a", none), ("k", some "v")])    first-entry-carveout
#     ([("k", some "v")], [("k", none)])      over-drop-session-null
#     ([("k", some "b")], [("k", some "a")])  precedence-flipped
#     ([("k", none), ("k", some "v")], [])    drop-request-keyed-null-pass
#   Across them `req` ranges over [], two distinct single-entry overrides, and a
#   two-entry mapping that REPEATS a key (the only point where the request-keyed
#   drop and the value-keyed drop can disagree); `ses` ranges over [], single and
#   double entries with null and real values on shared and unshared keys. So
#   neither input binder is pinned, and the variation is meaningful rather than
#   two spellings of one point: each witness's input is one where its own rival
#   diverges from `effective` and — checked both ways with real builds for the
#   prepatch/first-entry pair — at least one other rival AGREES with `effective`.
#
# AXIOM_TESTS: dropped. The axiom lane is G-AX's job; this bundle declares no
# axiom (the merge is modeled deeply as list operations), so there is nothing to
# probe and the gate ignores AXIOM_TESTS regardless.
AXIOM_TESTS = []
