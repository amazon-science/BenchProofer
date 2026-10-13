"""properties.py — G-PBT falsification battery for pytest-dev__pytest-7490 (lean).

NOT a Lean file; a record of adversarial cases the G-PBT gate executes. Each
SPEC case is a full ``Solution.lean`` variant that shares the FROZEN spec
byte-for-byte (region surgery: only text inside ``-- impl-start`` /
``-- impl-end`` — and, for a case that legitimately re-proves, inside
``-- proof-start`` / ``-- proof-end`` — is changed, so ``markers.same_spec``
holds and the ``theorem correct_resolveExpectedFailure`` STATEMENT stays
byte-identical). ``expect:"verify"`` passes iff (in scope AND the file
elaborates with the obligation closed); ``expect:"reject"`` passes iff (in scope
AND it does NOT verify AND the case's refutation ``witness`` holds of the rival
while FAILING on the frozen solution).

DEFENDED SURFACE (one total pure function over two annotation observations):

  resolveExpectedFailure (before after : Option ExpectedFailure)
      : Option ExpectedFailure

  ``before`` is the annotation known before the body runs (``none`` when none is
  in effect yet); ``after`` is the annotation observed after the body runs. The
  spec pins the result completely with two independent clauses:

    (C1) ∀ x, before = some x → result = some x   -- earlier annotation is kept
    (C2) before = none       → result = after      -- else the after value stands

  (C1) is the PRESERVE clause: any established earlier annotation is
  authoritative and copied through unchanged. (C2) is the REFRESH clause: with
  no earlier annotation, the result is EXACTLY the after observation, whatever it
  is (including ``none``). Together they leave no output free.

CARRIER NARROWING vs the nagini sibling. The nagini battery contracts
``settle_saved_evaluation(slot: SavedSlot, final_marker_state: int)``, a C-style
in/out mutation over a two-field carrier ``SavedSlot(present, value)`` plus an
uninterpreted ``@Pure`` evaluator ``evaluate_marks``. This Lean bundle models the
purely-functional CORE of that operation: the store-refresh selection
``store[key] = before if before is not None else after``. The mapping collapses
nagini's two carrier fields into one ``Option``:

  * nagini ``present=False``  and ``present=True & value=None``  → ``before = none``
    (both are "no annotation established yet"; on this carrier they are the SAME
    input, so the two are not separately attackable — see the DROPPED cases);
  * nagini ``present=True & value=v (v≠None)``                    → ``before = some v``;
  * nagini's post-body ``evaluate_marks(final_marker_state)``     → the plain input
    ``after``. On this carrier ``after`` is a transparent VALUE, not an opaque
    oracle: there is no uninterpreted callee whose identity a rival could echo.

ADVERSARIAL READ of the nagini classes on this carrier:

  * ADMISSIBILITY (nagini ``admiss-empty-saved``) — APPLIES, re-derived. Nagini's
    version is a self-call establishing the permission ``Requires``; the frozen
    obligation here has no precondition, so that exact shape has no analogue. But
    the CLASS is not vacuous: on a total carrier the analogue of
    PRECOND-TOO-STRONG is the obligation being UNSATISFIABLE at exactly an
    F2P-shaped input, which a positive that discharges the spec predicate at that
    concrete input — by evaluation, as a ``have``, before closing the frozen
    obligation verbatim — tests directly. See admiss-ground-refresh. ("The frozen
    obligation has no precondition" is NOT a sufficient reason to drop this lane;
    dropping it silently removes one of the three directions this gate tests.)

  * FRAME / PERMISSION MUTATION — VACUOUS. Nagini's ``slot`` is a full-Acc in/out
    carrier and ``final_marker_state`` an ``int`` value; nagini already records
    ``has_readonly_input=False`` / ``frame_mutation_included=False`` (no
    half-permission reference to abuse). Lean is referentially transparent —
    ``before``/``after`` are immutable values — so the class is doubly vacuous
    here. No permission-violation substitute is fabricated.

  * DIVERGENCE / NON-TERMINATION — VACUOUS on lean. ``implementation_*`` is a
    total Lean ``def``; a diverging implementation cannot be written at all, so
    there is nothing to port and no known-hole to record (that disposition is a
    velvet-partial concern, not a lean one).

  * UNGROUNDED-ORACLE ECHO — VACUOUS. The nagini spec grounds the refresh clause
    in an uninterpreted ``@Pure evaluate_marks(final_marker_state)`` (its
    ``stale`` / ``fabricate`` rivals attack the ``is``-identity pin). Here
    ``after`` is a transparent input, not an axiomatized answer key: the refresh
    clause is a direct equality ``result = after``. There is no opaque callee to
    echo, so the two nagini identity-cheat rivals collapse into ONE value-level
    rival on this carrier (refresh-wrong-value below): any refresh that does not
    return ``after`` itself — whether a "stale" recomputation or a "fabricated"
    fresh value — is the same violation of (C2). meta.json axioms == [] and
    deep_model_references == []; AXIOM_TESTS is EMPTY (the axiom lane is G-AX's
    job and there is no consumed axiom here anyway).

  * NO-REFRESH / PREPATCH ECHO (nagini ``refresh-norefresh``) — APPLIES, the
    load-bearing rival. Ignoring the after observation is exactly the pre-fix
    behavior: the dynamically-attached annotation is never consulted, so a
    failing test is reported FAILED not xfailed (the issue). Refuted by (C2).

  * PARTIAL-DOMAIN (nagini ``refresh-partial-absent-only``) — APPLIES, on a
    RE-DERIVED split. Nagini's partial rival refreshes only the
    ``present=False`` sub-case and leaves ``present=True & value=None`` stale;
    that particular split does collapse here, because both of those map to the
    single input ``before = none``. But the CLASS survives: the refresh
    sub-domain (``before = none``) is still splittable on the *after* binder,
    which this carrier keeps as structured data. A rival that refreshes only
    part of it — refreshing when the after annotation is non-strict and leaving
    a strict one unrefreshed — is expressible, in scope, and refuted only at the
    sub-domain it skips (see refresh-partial-strict-only). It is a materially
    different rival from refresh-norefresh, which ignores the after observation
    everywhere: this one is CORRECT on the rest of the refresh sub-domain and on
    the whole preserve sub-domain, so it survives every input the other rivals
    fire at.

  * CLOBBER / PRESERVE VIOLATION (nagini ``refresh-clobber-prior``) — APPLIES.
    Overwriting an already-established earlier annotation with the after
    observation drops the authoritative save; refuted by (C1).

WITNESSES. On a tactic-proof backend "did not verify" is the DEFAULT outcome of
reshaping an implementation (the frozen ``cases before`` script is tuned to the
frozen form), so a rejection alone attributes nothing to the spec. Every
``expect="reject"`` case therefore carries a Lean snippet stating the spec
predicate at a concrete input over ``decide``-able literal annotations. Each
witness was checked to HOLD of its rival and to FAIL on the frozen solution (so
it discriminates rather than asserting a tautology); no witness binds a
hypothesis (all inputs are literal), so none can be inconsistent.

BINDER + CLAUSE COVERAGE. The spec predicate has two input binders, ``before``
and ``after``, and two independent clauses:
  * (C1) is attacked by refresh-clobber-prior at ``before = some ⟨"a",true,true⟩``,
    ``after = none`` — so ``before`` is exercised on its ``some`` side and the
    result is refuted where the preserve clause governs.
  * (C2) is attacked by refresh-norefresh (``before = none``,
    ``after = some ⟨"r",true,false⟩``), by refresh-wrong-value (``before =
    none``, ``after = some ⟨"fresh",false,true⟩``, a DISTINCT annotation) and by
    refresh-partial-strict-only (``before = none``, ``after = some
    ⟨"r",true,true⟩``) — so ``before`` is exercised on its ``none`` side and
    ``after`` is varied across three distinct non-none values, pinning the
    refresh clause's dependence on the actual ``after`` value (not merely on its
    being non-none) AND on the WHOLE refresh sub-domain rather than a chosen part
    of it.
``after`` also spans ``none`` (clobber) and ``some`` (the other three);
``before`` spans ``none`` and ``some``. ``pts`` = 4 distinct input points.

The ADMISSIBILITY positive (admiss-ground-refresh) adds two further points on the
refresh sub-domain, ``before = none`` with ``after = some ⟨"dynamic",true,false⟩``
and ``... true,true⟩``, discharged POSITIVELY (the spec HOLDS of the frozen impl
there) rather than refuted — so the battery exercises all three directions the
gate exists to test: SPEC-TOO-WEAK (four rivals), SPEC-TOO-STRONG (two reshapes)
and the PRECOND-TOO-STRONG analogue (obligation satisfiable at an F2P-shaped
input).

Each witness point is checked to be LOAD-BEARING and not an arbitrary spelling:
restating a witness's claim at a point where its rival AGREES with the spec makes
that witness fail against the rival. Verified by build for refresh-wrong-value
(at ``after = some ⟨"stale",true,false⟩``, the rival's own constant) and for
refresh-partial-strict-only (at a NON-strict ``after``, the half it refreshes
correctly) — both exit 1 against the rival, so neither witness would hold at the
agreement point.
"""
from pathlib import Path

INSTANCE = "pytest-dev__pytest-7490"

_BASE = (Path(__file__).parent / "Solution.lean").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# ---- region anchors (each unique inside Solution.lean; verified at load) ----
# The FULL impl-region body and the FULL frozen proof body, so every
# replacement lands entirely inside the region it means to edit and never
# touches the spec view or the theorem statement.
_IMPL_GOLD = (
    "def implementation_resolveExpectedFailure\n"
    "    (before after : Option ExpectedFailure) : Option ExpectedFailure := Id.run do\n"
    "  let mut xfailed := before\n"
    "  if xfailed.isNone then\n"
    "    xfailed := after\n"
    "  return xfailed"
)

_PROOF_GOLD = (
    "  intro before after\n"
    "  unfold problem_spec_resolveExpectedFailure implementation_resolveExpectedFailure\n"
    "  cases before with\n"
    "  | none =>\n"
    "    refine ⟨fun x h => ?_, fun _ => rfl⟩\n"
    "    exact absurd h (by simp)\n"
    "  | some x =>\n"
    "    refine ⟨fun y h => ?_, fun h => ?_⟩\n"
    "    · simpa using h\n"
    "    · exact absurd h (by simp)"
)

assert _BASE.count(_IMPL_GOLD) == 1, "impl region drifted; update _IMPL_GOLD"
assert _BASE.count(_PROOF_GOLD) == 1, "proof region drifted; update _PROOF_GOLD"

# The frozen proof's `intro` line (inside the proof region, unique in the file),
# so the admissibility positive can PREPEND a ground `have` without touching the
# theorem STATEMENT or the spec view.
_P_INTRO = "  intro before after"

assert _BASE.count(_P_INTRO) == 1, "proof intro drifted; update _P_INTRO"


def _impl(body):
    """Full Solution.lean variant with the gold impl body replaced."""
    return _swap(_BASE, _IMPL_GOLD, body)


# ---------------------------------------------------------------------------
# POSITIVE CONTROLS (soundness) — structurally different but CORRECT impls that
# MUST verify. Each keeps the theorem STATEMENT byte-identical and re-proves for
# its own shape; no helper lemma / axiom / assumption token.
# ---------------------------------------------------------------------------

# (S.match) The gold's imperative `Id.run do … let mut … if isNone` collapsed
# into a direct pattern match. Boolean-equal to gold on every input; a
# straight-line functional definition, no induction. The frozen proof's
# `cases before` script still fits (the match reduces definitionally on each
# branch), so the frozen proof body is reused verbatim.
_MATCH_IMPL = (
    "def implementation_resolveExpectedFailure\n"
    "    (before after : Option ExpectedFailure) : Option ExpectedFailure :=\n"
    "  match before with\n"
    "  | some x => some x\n"
    "  | none => after"
)

# (S.ifsome) The selection written as `if before.isSome then before else after`.
# Same value on every input; the proof re-proves with a `simp_all` close on the
# `some` branch (the frozen `simpa`/`absurd` pair is tuned to the `Id.run` shape).
_IFSOME_IMPL = (
    "def implementation_resolveExpectedFailure\n"
    "    (before after : Option ExpectedFailure) : Option ExpectedFailure :=\n"
    "  if before.isSome then before else after"
)
_IFSOME_PROOF = (
    "  intro before after\n"
    "  unfold problem_spec_resolveExpectedFailure implementation_resolveExpectedFailure\n"
    "  cases before with\n"
    "  | none => refine ⟨fun x h => ?_, fun _ => rfl⟩; exact absurd h (by simp)\n"
    "  | some x => refine ⟨fun y h => ?_, fun h => ?_⟩ <;> simp_all"
)

# (A.ground) ADMISSIBILITY. The frozen obligation carries NO precondition, so the
# nagini permission-admission self-call has no direct analogue; the analogue on a
# total carrier is the obligation being UNSATISFIABLE at exactly an F2P-shaped
# input, which this positive tests directly. It discharges the spec predicate BY
# EVALUATION (`decide`) at the two F2P-shaped points — no earlier annotation
# established, an annotation observed after the body ran, in both the non-strict
# and the strict flavor — as `have`s prepended to the frozen tactic body, then
# closes the frozen obligation VERBATIM. Nothing is assumed: no new declaration,
# no axiom/sorry token, statement byte-identical.
#
# The `have`s are load-bearing rather than decoration: the SAME two `have`s
# prepended to the no-refresh rival's proof FAIL (real build, exit 1, `decide`
# proved the proposition false at `none, some ⟨"dynamic", true, false⟩`), so they
# genuinely assert the refresh behavior at an F2P-shaped input rather than
# something every impl satisfies.
_ADMISS_GROUND = "".join(
    "  have {} : problem_spec_resolveExpectedFailure\n"
    "      none (some ⟨\"dynamic\", true, {}⟩)\n"
    "      (implementation_resolveExpectedFailure\n"
    "        none (some ⟨\"dynamic\", true, {}⟩)) := by\n"
    "    unfold problem_spec_resolveExpectedFailure "
    "implementation_resolveExpectedFailure\n"
    "    decide\n".format(name, flag, flag)
    for name, flag in (("_ground_nonstrict", "false"), ("_ground_strict", "true"))
)


# ---------------------------------------------------------------------------
# UNIQUENESS / SPEC-TOO-WEAK rivals — wrong impls sharing the frozen spec that
# MUST be rejected. Each carries (a) the refinement argument that its faithful
# real patch would NOT resolve the F2P, and (b) a refutation witness pinning the
# violation at one concrete input.
# ---------------------------------------------------------------------------

# (U.norefresh) NO REFRESH — return the before observation unconditionally,
# never consulting after. This IS the pre-fix behavior.
_NOREFRESH_IMPL = (
    "def implementation_resolveExpectedFailure\n"
    "    (before after : Option ExpectedFailure) : Option ExpectedFailure :=\n"
    "  before"
)

# (U.wrong-value) REFRESH WITH THE WRONG VALUE — when no earlier annotation was
# established, store a fabricated/stale constant instead of the after
# observation. Correct on (C1) (before is preserved), wrong on (C2). This folds
# nagini's `refresh-stale-state` and `refresh-fabricate` into one: on this
# carrier both are "the refresh branch returns something other than after".
_WRONGVAL_IMPL = (
    "def implementation_resolveExpectedFailure\n"
    "    (before after : Option ExpectedFailure) : Option ExpectedFailure := Id.run do\n"
    "  let mut xfailed := before\n"
    "  if xfailed.isNone then\n"
    "    xfailed := some ⟨\"stale\", true, false⟩\n"
    "  return xfailed"
)

# (U.partial-strict) PARTIAL-DOMAIN REFRESH — refresh the no-earlier-annotation
# case only when the after annotation is NON-strict, leaving a strict one
# unrefreshed. Correct on (C1) everywhere and on the non-strict half of (C2), so
# every input the other two rivals are refuted at is one this rival gets RIGHT;
# it is falsified only on the half of the refresh sub-domain it skips. This is
# the nagini partial-domain class re-derived on the split this carrier does keep
# (the `after` binder's fields) rather than the one it collapses.
_PARTIAL_STRICT_IMPL = (
    "def implementation_resolveExpectedFailure\n"
    "    (before after : Option ExpectedFailure) : Option ExpectedFailure := Id.run do\n"
    "  let mut xfailed := before\n"
    "  if xfailed.isNone then\n"
    "    match after with\n"
    "    | some a => if !a.strict then xfailed := some a\n"
    "    | none => pure ()\n"
    "  return xfailed"
)

# (U.clobber) PRESERVE VIOLATION — always take the after observation, dropping
# an already-established earlier annotation. Correct on (C2), wrong on (C1).
_CLOBBER_IMPL = (
    "def implementation_resolveExpectedFailure\n"
    "    (before after : Option ExpectedFailure) : Option ExpectedFailure := Id.run do\n"
    "  let mut xfailed := before\n"
    "  xfailed := after\n"
    "  return xfailed"
)


SPEC_TESTS = [
    # =====================================================================
    # POSITIVE CONTROLS (soundness) — MUST verify.
    # =====================================================================
    {
        "id": "pos-match-form",
        "kind": "soundness",
        "expect": "verify",
        "module": _impl(_MATCH_IMPL),
        "rationale": (
            "a correct reshape that replaces the imperative `Id.run do / let mut / "
            "if isNone` selection with a direct pattern match `match before with "
            "| some x => some x | none => after`. Boolean-equal to gold on every "
            "input (both keep an established earlier annotation and otherwise take "
            "the after observation), a straight-line functional definition needing "
            "no induction. The frozen `cases before` proof reduces definitionally "
            "on each branch, so it re-proves without a new lemma/axiom. If it "
            "failed to verify the spec would be over-fit to the exact `Id.run` "
            "shape => SPEC-TOO-STRONG."
        ),
    },
    {
        "id": "pos-if-isSome",
        "kind": "soundness",
        "expect": "verify",
        "module": _swap(_impl(_IFSOME_IMPL), _PROOF_GOLD, _IFSOME_PROOF),
        "rationale": (
            "a correct reshape writing the selection as `if before.isSome then "
            "before else after`. Same value on every input; the theorem STATEMENT "
            "is byte-identical and the tactic body is re-proved for the new shape "
            "(the `some` branch closes by `simp_all` rather than the `Id.run`-tuned "
            "`simpa`/`absurd` pair). No helper lemma, axiom, or assumption token. "
            "If it cannot satisfy the frozen obligation the spec is SPEC-TOO-STRONG."
        ),
    },

    # =====================================================================
    # ADMISSIBILITY — the obligation is SATISFIABLE (non-vacuous) at an
    # F2P-shaped input. MUST verify.
    # =====================================================================
    {
        "id": "admiss-ground-refresh",
        "kind": "admissibility",
        "expect": "verify",
        "module": _swap(_BASE, _P_INTRO, _ADMISS_GROUND + _P_INTRO),
        "rationale": (
            "the frozen obligation carries NO precondition, so nagini's "
            "permission-admission self-call has no direct analogue; the analogue "
            "on this total carrier is the obligation being UNSATISFIABLE at "
            "exactly an F2P-shaped input, which this case tests directly. The "
            "spec predicate is discharged BY EVALUATION (`decide`) at the two "
            "F2P-shaped points \u2014 no earlier annotation established, an "
            "annotation observed after the body ran, in the non-strict AND the "
            "strict flavor (the two observables the F2P pair exercises) \u2014 as "
            "`have`s prepended to the frozen tactic body, after which the frozen "
            "obligation is closed VERBATIM. If the spec could not be satisfied at "
            "these normal inputs the modeled behavior would be vacuous there => "
            "the PRECOND-TOO-STRONG analogue. Nothing is assumed: no new "
            "declaration, no axiom/sorry token, statement byte-identical. The "
            "`have`s are load-bearing, not decoration: the same two prepended to "
            "the no-refresh rival's proof FAIL (`decide` proves the proposition "
            "false at the non-strict point), so they assert the refresh behavior "
            "at an F2P-shaped input rather than something every impl satisfies."
        ),
    },

    # =====================================================================
    # UNIQUENESS / SPEC-TOO-WEAK rivals — MUST be rejected.
    # =====================================================================
    {
        "id": "refresh-norefresh",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(_NOREFRESH_IMPL),
        "refinement": (
            "returning the before observation unconditionally IS the pre-fix "
            "behavior: the post-body refresh block is absent, so an annotation "
            "introduced while the body runs is never consulted. Its faithful real "
            "patch is the pre-patch code, which the F2P observable defeats — a test "
            "that dynamically attaches an expected-failure marker while running and "
            "then fails is reported as a hard FAILURE instead of an expected "
            "failure, and the strict-unexpected-pass variant is not flagged. It "
            "does NOT resolve."
        ),
        "rationale": (
            "REJECT from (C2): with `before = none` the spec demands `result = "
            "after`, but this rival returns `before = none`. At `before = none`, "
            "`after = some ⟨\"r\",true,false⟩` the spec requires `some ⟨\"r\",…⟩` "
            "and the rival yields `none`. If it verified the spec would admit the "
            "regressed pre-patch => SPEC-TOO-WEAK."
        ),
        "witness": (
            "-- Refuted on the refresh sub-domain (before = none): the after\n"
            "-- observation must be the result, but the rival ignores it and\n"
            "-- returns none.\n"
            "example :\n"
            "    ¬ problem_spec_resolveExpectedFailure\n"
            "        none (some ⟨\"r\", true, false⟩)\n"
            "        (implementation_resolveExpectedFailure\n"
            "          none (some ⟨\"r\", true, false⟩)) := by\n"
            "  unfold problem_spec_resolveExpectedFailure implementation_resolveExpectedFailure\n"
            "  intro h\n"
            "  exact absurd h.2 (by decide)\n"
        ),
    },
    {
        "id": "refresh-wrong-value",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(_WRONGVAL_IMPL),
        "refinement": (
            "refreshing with a fabricated/stale constant rather than the after "
            "observation corresponds to re-deriving the annotation from a FIXED or "
            "cached marker state instead of the state as it finally stands after "
            "the body ran. The dynamically-attached annotation lives only in the "
            "after observation, so it is missed and the failing test is reported "
            "FAILED not expected-failure; and any P2P test relying on the actual "
            "reason/run/strict fields being reported would misclassify. It does "
            "NOT resolve."
        ),
        "rationale": (
            "REJECT from (C2): with `before = none` the spec demands `result = "
            "after` EXACTLY. This rival preserves before correctly (so (C1) holds) "
            "but on the refresh branch returns a constant `some ⟨\"stale\",…⟩` "
            "instead of after. At `before = none`, `after = some ⟨\"fresh\",false,"
            "true⟩` (a value DISTINCT from the constant) the result is wrong. "
            "Refuted by varying the after binder to a value the rival cannot echo — "
            "if it verified the spec would not pin the result to the actual after "
            "value => SPEC-TOO-WEAK."
        ),
        "witness": (
            "-- Refuted at before = none with after DISTINCT from the rival's\n"
            "-- fabricated constant: (C2) requires the result equal after exactly,\n"
            "-- but the rival returns its own value.\n"
            "example :\n"
            "    ¬ problem_spec_resolveExpectedFailure\n"
            "        none (some ⟨\"fresh\", false, true⟩)\n"
            "        (implementation_resolveExpectedFailure\n"
            "          none (some ⟨\"fresh\", false, true⟩)) := by\n"
            "  unfold problem_spec_resolveExpectedFailure implementation_resolveExpectedFailure\n"
            "  intro h\n"
            "  exact absurd h.2 (by decide)\n"
        ),
    },
    {
        "id": "refresh-partial-strict-only",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(_PARTIAL_STRICT_IMPL),
        "refinement": (
            "refreshing only PART of the no-earlier-annotation domain — taking "
            "the after observation when it is non-strict but leaving an "
            "annotation whose strict flag is set unrefreshed — corresponds to a "
            "faithful real patch that guards the post-body refresh on a property "
            "of the annotation it just derived instead of performing it "
            "unconditionally. The dynamically-introduced annotation still fails "
            "to reach the report step on the guarded half, so a test that "
            "introduces a STRICT expected-failure annotation while running is "
            "still misreported: the strict-unexpected-pass observable in the F2P "
            "pair is exactly that half, and it would still fail. It does NOT "
            "resolve."
        ),
        "rationale": (
            "REJECT from (C2): with `before = none` the spec demands `result = "
            "after` on the WHOLE sub-domain, not on a chosen part of it. This "
            "rival satisfies (C1) everywhere and (C2) on the non-strict half, so "
            "it is CORRECT at every input the other two rivals are refuted at — "
            "it is falsified only at `before = none`, `after = some ⟨\"r\",true,"
            "true⟩`, where it returns `none`. That the same claim restated at a "
            "non-strict `after` HOLDS of this rival is what makes the point "
            "load-bearing rather than an arbitrary spelling. If it verified the "
            "spec would pin the refresh clause on only part of its domain => "
            "SPEC-TOO-WEAK."
        ),
        "witness": (
            "-- Refuted on the part of the refresh sub-domain this rival skips:\n"
            "-- with no earlier annotation established, (C2) demands the result\n"
            "-- be the after observation EXACTLY, but an annotation whose strict\n"
            "-- flag is set is left unrefreshed and the result stays none.\n"
            "example :\n"
            "    ¬ problem_spec_resolveExpectedFailure\n"
            "        none (some ⟨\"r\", true, true⟩)\n"
            "        (implementation_resolveExpectedFailure\n"
            "          none (some ⟨\"r\", true, true⟩)) := by\n"
            "  unfold problem_spec_resolveExpectedFailure implementation_resolveExpectedFailure\n"
            "  intro h\n"
            "  exact absurd h.2 (by decide)\n"
        ),
    },
    {
        "id": "refresh-clobber-prior",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(_CLOBBER_IMPL),
        "refinement": (
            "dropping the guard and always taking the after observation "
            "corresponds to re-deriving the annotation unconditionally, discarding "
            "an annotation already established before the body ran. The design "
            "deliberately preserves the earlier annotation; a fresh re-derivation "
            "produces a different descriptor for the same logical mark, so the "
            "report step consumes a re-derived value and P2P tests relying on the "
            "setup-time annotation being the one reported would break. It does NOT "
            "resolve."
        ),
        "rationale": (
            "REJECT from (C1): when `before = some x` the spec demands `result = "
            "some x` (the earlier annotation is authoritative). This rival ignores "
            "before and returns after. At `before = some ⟨\"a\",true,true⟩`, "
            "`after = none` the spec requires `some ⟨\"a\",…⟩` but the rival yields "
            "`none`. Refuted on the preserve sub-domain (before non-none), the "
            "OTHER side of the before split from the refresh rivals — if it "
            "verified an established annotation could be silently clobbered => "
            "SPEC-TOO-WEAK."
        ),
        "witness": (
            "-- Refuted on the preserve sub-domain (before = some ...): the earlier\n"
            "-- annotation is authoritative and must be kept, but the rival\n"
            "-- overwrites it with the after observation (here none).\n"
            "example :\n"
            "    ¬ problem_spec_resolveExpectedFailure\n"
            "        (some ⟨\"a\", true, true⟩) none\n"
            "        (implementation_resolveExpectedFailure\n"
            "          (some ⟨\"a\", true, true⟩) none) := by\n"
            "  unfold problem_spec_resolveExpectedFailure implementation_resolveExpectedFailure\n"
            "  intro h\n"
            "  have := h.1 ⟨\"a\", true, true⟩ rfl\n"
            "  exact absurd this (by decide)\n"
        ),
    },
]


# No consumed axioms and no deep-model references (meta.json axioms == [],
# deep_model_references == []): the selection is modeled directly over the data,
# so there is no in-model axiom obligation for the PBT axiom lane to
# re-discharge. The nagini `ax-eval-determinism` probe targets the uninterpreted
# `evaluate_marks` callee, which this carrier does not model (its result enters
# as the transparent `after` input); that lane belongs to G-AX regardless.
AXIOM_TESTS = []
