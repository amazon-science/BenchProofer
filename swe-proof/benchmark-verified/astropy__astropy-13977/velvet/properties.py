"""properties.py — G-PBT falsification battery for astropy__astropy-13977 (velvet).

NOT a Velvet module; a record of adversarial cases the G-PBT gate executes.
Each SPEC case is a full ``Solution.lean`` variant that shares the FROZEN spec
byte-for-byte (region surgery: only text inside the ``-- impl-start`` /
``-- impl-end`` region, or inside the ``prove_correct`` tactic body, is changed —
both of which the consumer spec view elides — so ``markers.same_spec`` holds and
the ``prove_correct dispatchUfunc`` obligation survives with a byte-identical
statement) and swaps in a candidate implementation; it is checked by the real
verifier. ``expect:"verify"`` passes iff (in scope AND verifies);
``expect:"reject"`` passes iff (in scope AND does NOT verify AND its refutation
``witness`` discriminates: the witness must elaborate against the rival and FAIL
against the frozen solution).

DEFENDED SURFACE (one contracted method over an opaque operation descriptor):

  dispatchUfunc (call)   ensures out = ufuncSpec call

``call`` is the single INPUT binder. It is an opaque handle: the spec observes it
ONLY through two opaque helpers — a wrapped computation ``coreUfunc call``
(``Except.ok v`` = it yielded a value; ``Except.error recoverable`` = it failed in
a way another participant might resolve; ``Except.error fatal`` = any other
failure) and a boolean ``canDefer call`` (whether some participant advertises its
own handler). ``ufuncSpec`` pins the whole outcome as a total function of those
two observations, with FOUR independent top-level legs:

  (L1) coreUfunc = ok v                       -> out = ok (result v)   [value verbatim]
  (L2) coreUfunc = error recoverable, canDefer -> out = ok deferred     [DEFER]
  (L3) coreUfunc = error recoverable, ¬canDefer -> out = error recoverable [re-propagate same]
  (L4) coreUfunc = error fatal                 -> out = error fatal      [propagate unchanged]

L2 is the discriminating behaviour the public issue reports (a recoverable
incompatibility, with an alternate handler present, must become a deferral rather
than escape). A wrong rival must violate one of L1-L4.

ADVERSARIAL READ of the nagini classes on THIS carrier:
  * FRAME-MUTATION — VACUOUS here. The nagini class exists because an input may
    carry a fractional heap permission an impl can overwrite. This backend is
    referentially transparent and this bundle declares NO ``mut`` binder: ``call``
    is an immutable value, there is no heap and no aliasing, so there is no
    read-only input to mutate and no substitute probe to build. Not fabricated.
  * PARTIAL-DOMAIN / VALUE — APPLIES. ``call`` is only ever observed through
    ``coreUfunc`` (three outcomes) and ``canDefer`` (two values); a rival right on
    part of that observation space but diverging on a sub-region is the natural
    falsifier. The rivals below partition the space exactly along L1-L4.
  * UNGROUNDED-ORACLE ECHO — N/A in the harmful sense. ``ufuncSpec`` is a total
    ``def`` in the ``pure`` region written directly over ``coreUfunc``/``canDefer``,
    the two observations the impl itself branches on; it is not an opaque
    answer-key the impl could echo without doing the work (the impl must itself
    reproduce the leg dispatch). The ``axioms`` region declares no ``axiom`` —
    both callees are ``opaque`` with no ``ensures`` — so there is no consumed
    contract to attack. Honest positive controls stand in for the ungrounded-echo
    probe.

THE WITNESS ON AN OPAQUE CARRIER. ``call`` feeds only opaque functions, so a
``decide`` on a concrete literal (``dispatchUfuncTester 0``) gets STUCK: nothing
reduces ``coreUfunc 0`` or ``canDefer 0``. A witness therefore cannot pin ``call``
to a value; instead it HYPOTHESISES the two observations at a symbolic ``call``
(``coreUfunc call = …``, ``canDefer call = …`` — exactly the sub-region the
rival's leg is wrong on) and shows the extracted program's output differs from
``ufuncSpec call`` there. Reaching the program uses Velvet's own extractor
(``extract_program_for`` gives ``dispatchUfuncExec = NonDetT.run ∘ dispatchUfunc``,
and ``NonDetT.run (pure x) = DivM.res x``). The snippet is checked in a file whose
``prove_correct`` block has been stripped, so no tactic script can mask the
verdict, and it must (1) elaborate against the rival and (2) FAIL against the
frozen solution — verified for each rival below (the gold reduces the very same
goal to ``¬(x = x)``, an unsolved ``False``). No ``sorry``/``admit``/
``native_decide``/``axiom``: the hypotheses are ordinary equalities of the opaque
observations, not assumptions of the conclusion.

WITNESS PLACEMENT / BINDER COVERAGE. Because ``call`` is observed through two
projections, "varying the binder" means varying those observations. The seven
rivals below probe ``coreUfunc`` at all three outcomes {ok, recoverable, fatal}
and ``canDefer`` at both {true, false}, so no observation of the sole input is
held fixed across the battery. Rivals attack in two TIERS, and the tiers
deliberately share hypothesis regions while failing there for DIFFERENT reasons:

  * tier 1 (four rivals) flips a whole leg — establishes each of L1-L4 is
    load-bearing;
  * tier 2 (three near misses) keeps the leg's recover-vs-escape SHAPE and gets
    only the pinned value wrong — the deferral sentinel (L2), the propagated
    failure's identity (L4), the re-raised failure's identity (L3).

So on {recoverable, canDefer=true} the never-defers rival lets the failure escape
whereas the near miss returns normally with the wrong value: same region, distinct
refutations, neither implying the other. A spec pinning only leg shape would pass
tier 1 and fail tier 2.

AXIOM lane: EMPTY (``axioms`` region declares no ``axiom``; both unchanged
sub-computations are ``opaque`` with no asserted ``ensures``, owed no contract).
There is no axiom-soundness / axiom-containment obligation to probe here, and the
gate ignores ``AXIOM_TESTS`` regardless.
"""
from pathlib import Path

INSTANCE = "astropy__astropy-13977"
BACKEND = "velvet"

_BASE = (Path(__file__).parent / "Solution.lean").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# ---- impl-region anchor: the whole leg-dispatch `let`, wholly inside the one
# ---- `-- impl-start` / `-- impl-end` region and unique in the file (both facts
# ---- asserted at load by _swap). Every variant reshapes exactly this block. ----
_IMPL = (
    "    let result : Except UfuncErr Outcome :=\n"
    "      match coreUfunc call with\n"
    "      | Except.ok v => Except.ok (Outcome.result v)\n"
    "      | Except.error UfuncErr.recoverable =>\n"
    "          if canDefer call then Except.ok Outcome.deferred\n"
    "          else Except.error UfuncErr.recoverable\n"
    "      | Except.error UfuncErr.fatal => Except.error UfuncErr.fatal\n"
)

# ---- the frozen `prove_correct` tactic body. A positive control that reshapes
# ---- the impl into a form the frozen script no longer closes may RETUNE this
# ---- body (it is elided from the consumer spec view) WITHOUT touching the spec
# ---- or dropping the obligation — the `prove_correct dispatchUfunc by` header
# ---- statement stays byte-identical. Unique in the file. ----
_PROOF = (
    "prove_correct dispatchUfunc by\n"
    "  loom_solve\n"
    "  simp_all [ufuncSpec]\n"
)


def _swap2(a_old, a_new, p_old, p_new):
    """Reshape the impl region AND retune the prove_correct tactic body."""
    return _swap(_swap(_BASE, a_old, a_new), p_old, p_new)


# ---- witness preamble. The spec is a `method` CONTRACT, not a bare predicate,
# ---- and its input is observed only through opaque helpers, so a witness
# ---- reaches the impl through Velvet's extractor and HYPOTHESISES the two
# ---- observations at the sub-region the rival mishandles.  `dispatchUfuncExec`
# ---- is `NonDetT.run (dispatchUfunc call)`, which reduces to `DivM.res result`;
# ---- `≠ DivM.res (ufuncSpec call)` says the impl's output contradicts the
# ---- postcondition there. Checked in a file whose `prove_correct` block is
# ---- stripped, so no tactic script can interfere.
def _wit(hyps, rws):
    hyp_lines = "".join(f"\n    ({h})" for h in hyps)
    rw = ", ".join(rws)
    return (
        "extract_program_for dispatchUfunc\n\n"
        f"example (call : Int){hyp_lines} :\n"
        "    dispatchUfuncExec call ≠ DivM.res (ufuncSpec call) := by\n"
        "  unfold dispatchUfuncExec dispatchUfunc ufuncSpec\n"
        f"  rw [{rw}]\n"
        "  simp [NonDetT.run, pure]\n"
    )


SPEC_TESTS = [
    # =====================================================================
    # POSITIVE CONTROLS (soundness) — structurally different but CORRECT
    # impls that MUST verify. If a faithful correct reshape cannot verify, the
    # spec is SPEC-TOO-STRONG. Each keeps the `ensures out = ufuncSpec call`
    # obligation and only reshapes the executable leg-dispatch.
    # =====================================================================
    {
        "id": "pos-arms-reordered",
        "kind": "soundness",
        "expect": "verify",
        # Reshape: the same three-way outcome dispatch written with the fatal
        # arm before the recoverable arm. A `match` is order-insensitive on
        # disjoint constructors, so the computed outcome is identical on every
        # leg. The frozen script closes by `rfl` on the frozen arm order; the
        # reordered form needs an explicit split on the outcome, so the tactic
        # body is retuned (elided from the spec view) while the obligation
        # statement is byte-identical.
        "module": _swap2(
            _IMPL,
            "    let result : Except UfuncErr Outcome :=\n"
            "      match coreUfunc call with\n"
            "      | Except.ok v => Except.ok (Outcome.result v)\n"
            "      | Except.error UfuncErr.fatal => Except.error UfuncErr.fatal\n"
            "      | Except.error UfuncErr.recoverable =>\n"
            "          if canDefer call then Except.ok Outcome.deferred\n"
            "          else Except.error UfuncErr.recoverable\n",
            _PROOF,
            "prove_correct dispatchUfunc by\n"
            "  loom_solve\n"
            "  unfold ufuncSpec\n"
            "  cases coreUfunc call with\n"
            "  | ok v => rfl\n"
            "  | error e => cases e <;> rfl\n",
        ),
        "rationale": "reordering the disjoint outcome arms computes the same "
                     "`Except UfuncErr Outcome` on every leg, so "
                     "`out = ufuncSpec call` still holds; a correct reshape must "
                     "verify (else SPEC-TOO-STRONG on arm order).",
    },
    {
        "id": "pos-recover-local",
        "kind": "soundness",
        "expect": "verify",
        # Reshape: hoist the recover decision (defer-iff-canDefer, else
        # re-propagate the same recoverable failure) into a typed local, then
        # use it in the recoverable arm. Identical value flow, so all of L1-L4
        # are unchanged; the frozen tactic body still closes (no retune needed).
        "module": _swap(
            _BASE, _IMPL,
            "    let recover : Except UfuncErr Outcome :=\n"
            "      if canDefer call then Except.ok Outcome.deferred\n"
            "      else Except.error UfuncErr.recoverable\n"
            "    let result : Except UfuncErr Outcome :=\n"
            "      match coreUfunc call with\n"
            "      | Except.ok v => Except.ok (Outcome.result v)\n"
            "      | Except.error UfuncErr.recoverable => recover\n"
            "      | Except.error UfuncErr.fatal => Except.error UfuncErr.fatal\n"),
        "rationale": "binding the recover decision to a typed local before the "
                     "outcome dispatch leaves every leg of `ufuncSpec` intact, "
                     "so `out = ufuncSpec call` holds; a correct reshape must "
                     "verify.",
    },

    # =====================================================================
    # ADMISSIBILITY (PRECOND-TOO-STRONG) — the obligation must be SATISFIABLE at
    # the interesting concrete points, not merely dischargeable somewhere. On a
    # total carrier with no `require` clause the analogue of a contradictory
    # precondition is a post-image that pins an UNREACHABLE value at an
    # F2P-shaped input: the obligation would then be vacuously unprovable there
    # and no faithful impl could exist. This case discharges the post-image at
    # each of the four legs BY EVALUATION as `have`s — including the
    # discriminating (recoverable ∧ canDefer) point, where the demanded outcome
    # is the deferral sentinel — and only then closes the frozen obligation
    # verbatim. The `have`s are `clear`ed before `loom_solve` so they cannot
    # help the main goal: the case fails if any leg's post-image is
    # unsatisfiable, and proves nothing extra if all are.
    # =====================================================================
    {
        "id": "admiss-legs-satisfiable",
        "kind": "admissibility",
        "expect": "verify",
        # Impl region UNCHANGED (frozen impl verbatim); only the tactic body is
        # extended, which the consumer spec view elides. The obligation
        # statement `prove_correct dispatchUfunc` is byte-identical.
        "module": _swap(
            _BASE, _PROOF,
            "prove_correct dispatchUfunc by\n"
            "  have hF2P : ∀ c : Int,\n"
            "      coreUfunc c = Except.error UfuncErr.recoverable → canDefer c = true →\n"
            "      ufuncSpec c = Except.ok Outcome.deferred := by\n"
            "    intro c h1 h2\n"
            "    simp [ufuncSpec, h1, h2]\n"
            "  have hL3 : ∀ c : Int,\n"
            "      coreUfunc c = Except.error UfuncErr.recoverable → canDefer c = false →\n"
            "      ufuncSpec c = Except.error UfuncErr.recoverable := by\n"
            "    intro c h1 h2\n"
            "    simp [ufuncSpec, h1, h2]\n"
            "  have hL1 : ∀ (c v : Int), coreUfunc c = Except.ok v →\n"
            "      ufuncSpec c = Except.ok (Outcome.result v) := by\n"
            "    intro c v h1\n"
            "    simp [ufuncSpec, h1]\n"
            "  have hL4 : ∀ c : Int, coreUfunc c = Except.error UfuncErr.fatal →\n"
            "      ufuncSpec c = Except.error UfuncErr.fatal := by\n"
            "    intro c h1\n"
            "    simp [ufuncSpec, h1]\n"
            "  clear hF2P hL3 hL1 hL4\n"
            "  loom_solve\n"
            "  simp_all [ufuncSpec]\n"),
        "rationale": "the post-image `out = ufuncSpec call` must be SATISFIABLE "
                     "at each of L1-L4, in particular at the discriminating "
                     "(recoverable ∧ canDefer) point where it demands the "
                     "deferral sentinel. Each leg is discharged by evaluation as "
                     "a `have`, then `clear`ed so it cannot assist the main goal, "
                     "before the frozen obligation is closed verbatim. If any "
                     "leg pinned an unreachable outcome this would fail => "
                     "PRECOND-TOO-STRONG (the total-carrier analogue: an "
                     "obligation unsatisfiable at an F2P-shaped input).",
    },

    # =====================================================================
    # UNIQUENESS / SPEC-TOO-WEAK rivals — wrong impls sharing the frozen spec
    # that MUST be rejected, each with a machine-checked refutation witness at
    # a concrete sub-region of the input's observation space, and the
    # refinement argument for why its faithful real counterpart would NOT
    # resolve the failing tests.
    # =====================================================================

    # ---- L1: the value-verbatim success leg ----
    {
        "id": "weak-success-alters-value",
        "kind": "uniqueness",
        "expect": "reject",
        # On a successful wrapped computation, perturbs the carried value
        # (`v + 1`) instead of returning it verbatim. Correct on every failure
        # leg; wrong exactly when the computation succeeds.
        "module": _swap(
            _BASE, _IMPL,
            "    let result : Except UfuncErr Outcome :=\n"
            "      match coreUfunc call with\n"
            "      | Except.ok v => Except.ok (Outcome.result (v + 1))\n"
            "      | Except.error UfuncErr.recoverable =>\n"
            "          if canDefer call then Except.ok Outcome.deferred\n"
            "          else Except.error UfuncErr.recoverable\n"
            "      | Except.error UfuncErr.fatal => Except.error UfuncErr.fatal\n"),
        "refinement": "a counterpart that altered a successful result before "
                      "returning it would corrupt the value of every ordinary "
                      "(non-failing) call — the entire pass-through path the "
                      "unchanged tests exercise — so those tests, which compare "
                      "the returned value against the wrapped computation's own, "
                      "still fail. It would NOT resolve.",
        "rationale": "REJECT from L1 (`coreUfunc = ok v -> out = ok (result v)`): "
                     "at a successful outcome the impl returns a perturbed value "
                     "where the post-image demands the value verbatim. Probes "
                     "`coreUfunc call = ok`.",
        "witness": _wit(["h1 : coreUfunc call = Except.ok 0"], ["h1"]),
    },

    # ---- L2: the deferral leg (the discriminating F2P behaviour) ----
    {
        "id": "weak-recoverable-never-defers",
        "kind": "uniqueness",
        "expect": "reject",
        # On a recoverable failure re-propagates the same failure regardless of
        # whether an alternate handler is available — i.e. never defers. This is
        # the pre-fix behaviour localized to the deferral leg: correct on L1,
        # L3, L4, wrong exactly at (recoverable AND canDefer).
        "module": _swap(
            _BASE, _IMPL,
            "    let result : Except UfuncErr Outcome :=\n"
            "      match coreUfunc call with\n"
            "      | Except.ok v => Except.ok (Outcome.result v)\n"
            "      | Except.error UfuncErr.recoverable =>\n"
            "          Except.error UfuncErr.recoverable\n"
            "      | Except.error UfuncErr.fatal => Except.error UfuncErr.fatal\n"),
        "refinement": "a counterpart that let a recoverable incompatibility "
                      "escape even when a participating operand advertises its "
                      "own handler is exactly the pre-fix behaviour the issue "
                      "reports: the alternate handler never gets its turn, so the "
                      "failing tests that require a deferral in that scenario "
                      "still observe the surfaced failure and fail. It would NOT "
                      "resolve.",
        "rationale": "REJECT from L2 (`coreUfunc = error recoverable ∧ canDefer "
                     "-> out = ok deferred`): with a recoverable failure and an "
                     "available handler the impl re-propagates the failure where "
                     "the post-image demands the deferral. Probes `coreUfunc = "
                     "error recoverable`, `canDefer = true`.",
        "witness": _wit(
            ["h1 : coreUfunc call = Except.error UfuncErr.recoverable",
             "h2 : canDefer call = true"], ["h1", "h2"]),
    },

    # ---- L3: the re-propagate leg (mirror of L2 at canDefer = false) ----
    {
        "id": "weak-recoverable-always-defers",
        "kind": "uniqueness",
        "expect": "reject",
        # On a recoverable failure defers unconditionally — even when NO
        # alternate handler is available. Correct on L1, L2, L4; wrong exactly
        # at (recoverable AND ¬canDefer), the mirror sub-region of the rival
        # above. Refuted with `canDefer = false`, the half of that observation
        # the never-defers rival cannot be refuted on (there its output
        # coincides with the frozen one), so the two rivals move `canDefer`
        # rather than pinning it.
        "module": _swap(
            _BASE, _IMPL,
            "    let result : Except UfuncErr Outcome :=\n"
            "      match coreUfunc call with\n"
            "      | Except.ok v => Except.ok (Outcome.result v)\n"
            "      | Except.error UfuncErr.recoverable => Except.ok Outcome.deferred\n"
            "      | Except.error UfuncErr.fatal => Except.error UfuncErr.fatal\n"),
        "refinement": "a counterpart that deferred on every recoverable failure "
                      "— even with no operand advertising a handler — would "
                      "swallow a genuine incompatibility that ought to surface, "
                      "turning it into a deferral no participant can act on, so "
                      "the unchanged tests that require the failure to be "
                      "re-raised when no alternate handler exists still fail. It "
                      "would NOT resolve.",
        "rationale": "REJECT from L3 (`coreUfunc = error recoverable ∧ ¬canDefer "
                     "-> out = error recoverable`): with a recoverable failure "
                     "and no available handler the impl defers where the "
                     "post-image demands the same failure re-propagated. Probes "
                     "`coreUfunc = error recoverable`, `canDefer = false` — the "
                     "mirror of the never-defers rival.",
        "witness": _wit(
            ["h1 : coreUfunc call = Except.error UfuncErr.recoverable",
             "h2 : canDefer call = false"], ["h1", "h2"]),
    },

    # ---- L4: the fatal propagation leg ----
    {
        "id": "weak-fatal-intercepted",
        "kind": "uniqueness",
        "expect": "reject",
        # Intercepts a FATAL failure and turns it into a deferral. Correct on
        # L1-L3; wrong exactly on the fatal leg. Probes `coreUfunc = error
        # fatal`, the third outcome no other rival exercises, so `coreUfunc` is
        # varied across all three of its outcomes by the battery.
        "module": _swap(
            _BASE, _IMPL,
            "    let result : Except UfuncErr Outcome :=\n"
            "      match coreUfunc call with\n"
            "      | Except.ok v => Except.ok (Outcome.result v)\n"
            "      | Except.error UfuncErr.recoverable =>\n"
            "          if canDefer call then Except.ok Outcome.deferred\n"
            "          else Except.error UfuncErr.recoverable\n"
            "      | Except.error UfuncErr.fatal => Except.ok Outcome.deferred\n"),
        "refinement": "a counterpart that intercepted a non-recoverable failure "
                      "and deferred would suppress an error that must always "
                      "propagate unchanged, so the unchanged tests that expect "
                      "such a failure to escape still fail (they now see a "
                      "deferral). It would NOT resolve.",
        "rationale": "REJECT from L4 (`coreUfunc = error fatal -> out = error "
                     "fatal`): on a fatal failure the impl defers where the "
                     "post-image demands the failure propagated unchanged. "
                     "Probes `coreUfunc = error fatal`, the outcome no other "
                     "rival exercises.",
        "witness": _wit(["h1 : coreUfunc call = Except.error UfuncErr.fatal"],
                        ["h1"]),
    },

    # =====================================================================
    # NEAR-MISS rivals. The four above each flip a WHOLE leg — they establish
    # that every leg is load-bearing, but not WHICH value each leg pins. A rival
    # that keeps the leg's *shape* (still recovers on L2, still fails on L3/L4)
    # and only gets the carried value/sentinel/error-tag wrong is the sharper
    # attack, and none of the four detects it. Added for clause coverage.
    # =====================================================================

    # ---- L2, near miss: recovers, but NOT with the deferral sentinel ----
    {
        "id": "weak-defer-as-plain-value",
        "kind": "uniqueness",
        "expect": "reject",
        # On (recoverable ∧ canDefer) the impl DOES intercept the failure and
        # return normally — but returns an ordinary value rather than the
        # distinguished deferral sentinel. Correct on L1, L3, L4, and even
        # correct about L2's "do not let the failure escape"; wrong only about
        # WHICH normal return L2 demands. This is what pins `Outcome.deferred`
        # specifically, which weak-recoverable-never-defers does not.
        "module": _swap(
            _BASE, _IMPL,
            "    let result : Except UfuncErr Outcome :=\n"
            "      match coreUfunc call with\n"
            "      | Except.ok v => Except.ok (Outcome.result v)\n"
            "      | Except.error UfuncErr.recoverable =>\n"
            "          if canDefer call then Except.ok (Outcome.result 0)\n"
            "          else Except.error UfuncErr.recoverable\n"
            "      | Except.error UfuncErr.fatal => Except.error UfuncErr.fatal\n"),
        "refinement": "a counterpart that swallowed a recoverable incompatibility "
                      "and returned some ordinary value instead of the distinct "
                      "'not implemented' sentinel would never hand the operation "
                      "to the participant that advertises a handler — the retry "
                      "against the other operand is precisely what the sentinel "
                      "triggers — so the failing tests would see a fabricated "
                      "value where they require the alternate handler's result. "
                      "It would NOT resolve, and it additionally corrupts a call "
                      "that ought to succeed elsewhere.",
        "rationale": "REJECT from L2 (`coreUfunc = error recoverable ∧ canDefer "
                     "-> out = ok deferred`): the impl recovers but returns "
                     "`result 0` where the post-image demands `deferred`. Pins "
                     "the SENTINEL, not merely the recover/escape decision. "
                     "Probes `coreUfunc = error recoverable`, `canDefer = true`.",
        "witness": _wit(
            ["h1 : coreUfunc call = Except.error UfuncErr.recoverable",
             "h2 : canDefer call = true"], ["h1", "h2"]),
    },

    # ---- L4, near miss: fatal still FAILS, but reclassified ----
    {
        "id": "weak-fatal-reclassified",
        "kind": "uniqueness",
        "expect": "reject",
        # On a fatal outcome the impl still propagates a FAILURE (it does not
        # intercept it, unlike weak-fatal-intercepted) — but relabels it as the
        # recoverable shape. Correct on L1-L3; wrong only about the IDENTITY of
        # the propagated failure, which is what "propagates unchanged" means.
        "module": _swap(
            _BASE, _IMPL,
            "    let result : Except UfuncErr Outcome :=\n"
            "      match coreUfunc call with\n"
            "      | Except.ok v => Except.ok (Outcome.result v)\n"
            "      | Except.error UfuncErr.recoverable =>\n"
            "          if canDefer call then Except.ok Outcome.deferred\n"
            "          else Except.error UfuncErr.recoverable\n"
            "      | Except.error UfuncErr.fatal =>\n"
            "          Except.error UfuncErr.recoverable\n"),
        "refinement": "a counterpart that let a non-recoverable failure out under "
                      "the recoverable failure's identity would change what "
                      "callers observe and what any enclosing handler catches: a "
                      "failure that must escape as itself would be reported as "
                      "the other kind. The unchanged tests that assert the exact "
                      "failure a non-recoverable outcome surfaces would still see "
                      "the wrong one, so it would NOT resolve.",
        "rationale": "REJECT from L4 (`coreUfunc = error fatal -> out = error "
                     "fatal`): the impl propagates a failure but the WRONG one. "
                     "Pins the propagated failure's IDENTITY (`unchanged`), which "
                     "weak-fatal-intercepted — flipping the whole leg to a normal "
                     "return — does not. Probes `coreUfunc = error fatal`.",
        "witness": _wit(["h1 : coreUfunc call = Except.error UfuncErr.fatal"],
                        ["h1"]),
    },

    # ---- L3, near miss: re-propagates, but not the SAME failure ----
    {
        "id": "weak-repropagate-wrong-failure",
        "kind": "uniqueness",
        "expect": "reject",
        # On (recoverable ∧ ¬canDefer) the impl correctly declines to recover and
        # lets a failure escape — but escalates it to the other failure shape
        # instead of re-propagating the very same one. Correct on L1, L2, L4;
        # wrong only about the identity of the re-raised failure, the mirror of
        # weak-fatal-reclassified and the sharpening of
        # weak-recoverable-always-defers.
        "module": _swap(
            _BASE, _IMPL,
            "    let result : Except UfuncErr Outcome :=\n"
            "      match coreUfunc call with\n"
            "      | Except.ok v => Except.ok (Outcome.result v)\n"
            "      | Except.error UfuncErr.recoverable =>\n"
            "          if canDefer call then Except.ok Outcome.deferred\n"
            "          else Except.error UfuncErr.fatal\n"
            "      | Except.error UfuncErr.fatal => Except.error UfuncErr.fatal\n"),
        "refinement": "a counterpart that re-raised a DIFFERENT failure than the "
                      "one it caught, when no alternate handler is available, "
                      "would replace the informative incompatibility report with "
                      "an unrelated one — and, because the substituted shape is "
                      "the never-intercepted kind, it would also defeat any "
                      "caller that legitimately handles the original. The "
                      "unchanged tests asserting the specific failure surfaced in "
                      "that scenario still fail. It would NOT resolve.",
        "rationale": "REJECT from L3 (`coreUfunc = error recoverable ∧ ¬canDefer "
                     "-> out = error recoverable`): the impl fails, but with the "
                     "other failure shape where the post-image demands the SAME "
                     "recoverable failure re-propagated unchanged. Pins the "
                     "re-raised failure's identity. Probes `coreUfunc = error "
                     "recoverable`, `canDefer = false`.",
        "witness": _wit(
            ["h1 : coreUfunc call = Except.error UfuncErr.recoverable",
             "h2 : canDefer call = false"], ["h1", "h2"]),
    },
]


# ---------------------------------------------------------------------------
# Nagini -> velvet accounting. The sibling battery has 6 SPEC cases (1
# soundness positive, 1 admissibility, 4 uniqueness rivals); every one is
# accounted for below. The two carriers are NOT the same partition: the sibling
# models a back-to-front scan over a list of operand kinds with a tri-state
# 0/1/2 return, whereas this bundle models the outcome dispatch of the whole
# operation over ONE opaque descriptor, observed only through a success/raise
# outcome and a boolean deferral classification. The nagini rivals are expressed
# over the list carrier; here they re-site onto the four disjoint legs of
# `ufuncSpec`, so the mapping is stated case by case.
#
#   sibling case                       -> here                            status
#   ---------------------------------------------------------------------------
#   pos-control-branch-reorder         -> pos-arms-reordered              PORTED
#   admiss-wellformed-flag             -> admiss-legs-satisfiable         RE-SITED
#   frame-mutation-write-io_kinds      -> (none, VACUOUS)                 OMITTED
#   partial-domain-skip-first-operand  -> weak-recoverable-never-defers   RE-SITED
#   partial-domain-always-abstain      -> weak-recoverable-always-defers  RE-SITED
#   uniqueness-success-returns-abstain -> weak-success-alters-value       RE-SITED
#
# 1 ported, 4 re-sited, 1 omitted = 6 sibling cases accounted for; this battery
# carries 9 cases (the 6 above plus weak-fatal-intercepted and two of the three
# near-miss rivals have no sibling counterpart — see ADDED).
#
# RE-SITED (the argument is unchanged; only the carrier is):
#  * partial-domain-skip-first-operand attacks the sibling's
#    "has_custom_handler => surface abstain code 1" clause by missing a custom
#    operand at index 0. Here the "abstain because an alternate handler exists"
#    behaviour IS the deferral leg L2 (recoverable + canDefer -> deferred), and a
#    rival that never defers is the faithful re-siting of "a custom operand goes
#    unnoticed so the dispatch surfaces the error instead of deferring". This is
#    also the discriminating F2P behaviour the public issue reports.
#  * partial-domain-always-abstain attacks the sibling's
#    "all_recognised => surface the error code 2" clause by abstaining even when
#    every operand is recognised. Here "surface the error when no alternate
#    handler exists" IS leg L3 (recoverable + ¬canDefer -> re-propagate), and a
#    rival that always defers is the faithful re-siting.
#  * uniqueness-success-returns-abstain attacks the sibling's
#    "not recoverable_failure => code 0" success clause. Here the success clause
#    is leg L1 (coreUfunc = ok v -> value verbatim); a rival that perturbs the
#    successful value is the analogous "the ordinary/success path is pinned"
#    attack on this carrier (the sibling flipped the whole success outcome to the
#    abstain code; here Outcome.result carries the value, so the sharpest success
#    falsifier corrupts that value).
#
# RE-SITED, admissibility (the sibling's admiss-wellformed-flag). The sibling
#  carries a `Requires` Forall forward as a loop invariant to show the
#  precondition is USABLE at a reachable index. This bundle has no `require` and
#  no loop, so that exact machinery is absent — but the LANE is not vacuous, and
#  an earlier revision of this file wrongly said it was. The total-carrier
#  analogue of PRECOND-TOO-STRONG is the post-image being UNSATISFIABLE at an
#  F2P-shaped input, and `admiss-legs-satisfiable` tests it directly: it
#  discharges `ufuncSpec` at each of L1-L4 by evaluation as a `have` — including
#  the discriminating (recoverable ∧ canDefer) point, where the demanded outcome
#  is the deferral sentinel — `clear`s them so they cannot assist, and only then
#  closes the frozen obligation verbatim. It is NOT true that "ufuncSpec is
#  total, therefore satisfiable by construction, therefore nothing to test": the
#  claim being probed is that each leg's demanded outcome is REACHABLE by the
#  contracted return type at that point, and that is a build, not an argument.
#  Impl region byte-identical to frozen; only the (spec-view-elided) tactic body
#  is extended, so the obligation statement is untouched.
#
# ADDED (3, no sibling counterpart). weak-fatal-intercepted, plus the three
#  near-miss rivals weak-defer-as-plain-value / weak-fatal-reclassified /
#  weak-repropagate-wrong-failure. The four leg-flipping rivals establish that
#  every leg is load-bearing but not WHICH value each leg pins: each near miss
#  keeps its leg's recover-vs-escape SHAPE and gets only the sentinel, the
#  propagated failure's identity, or the re-raised failure's identity wrong. A
#  spec that pinned only the shape (e.g. "L2 returns normally", "L4 fails")
#  would admit all three, and none of the leg-flipping rivals would notice.
#  Each carries a machine-checked witness on the same hypothesis region as its
#  coarse sibling, and the two are not redundant: they fail there for different
#  reasons (wrong shape vs wrong value within the right shape).
#
# ADDED, on weak-fatal-intercepted specifically. The sibling models a
#  tri-state 0/1/2 with no non-recoverable-failure channel, so it has no case for
#  a fatal failure. This carrier distinguishes recoverable from fatal failures
#  (coreUfunc's third outcome), and leg L4 pins that a fatal failure must
#  propagate unchanged; the rival attacks it. It is added for BINDER COVERAGE:
#  without it `coreUfunc` would only ever be probed at {ok, recoverable} and a
#  rival mishandling the fatal outcome would go uncaught. Not a fabricated
#  wrongness — it is a real divergence from L4 with a machine-checked witness and
#  a refinement argument (a fatal error that must always escape would be
#  suppressed).
#
# OMITTED (1):
#  * frame-mutation-write-io_kinds. Nagini-specific (fractional heap
#    permissions). This backend is referentially transparent and the method
#    declares no `mut` binder: `call` is an immutable value with no heap and no
#    aliasing, so there is no read-only input to overwrite and no substitute
#    probe. VACUOUS; no substitute fabricated.
#
# BINDER / CLAUSE COVERAGE. The sole input `call` is observed only through
# `coreUfunc call` and `canDefer call`. The seven rivals probe `coreUfunc` at all
# three of its outcomes {ok, recoverable, fatal} and `canDefer` at both {true,
# false}, so neither observation of the input is pinned across the battery. Every
# top-level leg of `ufuncSpec` (L1-L4) is attacked, and L2/L3/L4 are attacked
# TWICE — once by flipping the leg's shape and once by keeping the shape and
# corrupting the value it pins (see the two tiers in the module docstring). Both
# positive controls defend the whole obligation, and `admiss-legs-satisfiable`
# defends its satisfiability at each leg's concrete point.
#
# WHAT IS DELIBERATELY NOT CLAIMED. L1's carried value is pinned only by
# `weak-success-alters-value` (a `v + 1` perturbation). Because `v` is an opaque
# handle the impl cannot inspect, `Outcome.result v` admits no near miss finer
# than "some other value", so the perturbation IS the sharpest available L1
# attack rather than a coarse one. No sub-domain of `coreUfunc`'s success values
# is claimed to be separately probed — there is nothing to separate.
#
# WITNESS DISCRIMINATION (verified during authoring, and re-checked by the gate's
# two builds per reject case): each witness elaborates against its rival (the
# rival's output provably differs from `ufuncSpec call` on the hypothesised
# region) and FAILS against the frozen solution (the frozen impl reduces the same
# goal to `¬(x = x)`, an unsolved `False`). The opaque carrier forbids a
# `decide`-on-a-literal witness — `coreUfunc`/`canDefer` never reduce at a
# concrete `call` — so every witness hypothesises the two observations at a
# symbolic `call`; the hypotheses are ordinary equalities, not assumptions of the
# conclusion, and no `sorry`/`admit`/`native_decide`/`axiom` appears.
#
# AXIOM_TESTS: dropped. The axiom lane is G-AX's job and this bundle declares no
# axiom (both callees are `opaque` with no asserted `ensures`), so there is
# nothing there to probe.
AXIOM_TESTS = []
